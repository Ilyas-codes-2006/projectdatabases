from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_mail import Mail
from config import config_data as config
from datetime import date
from db import *
from auth import register_user, login_user, token_required, mail, request_password_reset, reset_password_with_token, \
    admin_required


def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app)

    app.config.from_mapping(
        DEBUG=config["debug"],
        DB_CONNSTR=config["db_connstr"],
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = config["db_connstr"]

    # E-mail configuratie
    app.config['MAIL_SERVER']         = config['mail_server']
    app.config['MAIL_PORT']           = config['mail_port']
    app.config['MAIL_USE_TLS']        = True
    app.config['MAIL_USERNAME']       = config['mail_username']
    app.config['MAIL_PASSWORD']       = config['mail_password']
    app.config['MAIL_DEFAULT_SENDER'] = config['mail_sender']

    # Koppel de mail instantie aan de app
    mail.init_app(app)

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.get("/")
    def root():
        return {"status": "MatchUp backend ok"}

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # ---------------------------------------------------------------------------
    # Auth routes
    # ---------------------------------------------------------------------------

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email and password are required"}), 400

        result = login_user(data['email'], data['password'])

        if result['success']:
            return jsonify({
                "token": result['token'],
                "name": result['name'],
                "user_id": result['user_id'],
                "is_admin": result['is_admin']
            }), 200
        else:
            return jsonify({"error": result['error']}), 401

    @app.route("/api/auth/register", methods=["POST"])
    def register():
        try:
            data = request.json
            required_fields = ['first_name', 'last_name', 'email', 'date_of_birth', 'password']
            if not data:
                return jsonify({"error": "Invalid JSON"}), 400
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing field: {field}"}), 400
        except Exception:
            return jsonify({"error": "Invalid request format"}), 400

        try:
            parsed_dob = date.fromisoformat(data['date_of_birth'])
        except ValueError:
            return jsonify({"error": "Ongeldige geboortedatum. Gebruik YYYY-MM-DD."}), 400

        result = register_user(
            last_name=data['last_name'],
            first_name=data['first_name'],
            password=data['password'],
            bio=data.get('bio', ''),
            is_admin=data.get('is_admin', False),
            date_of_birth=parsed_dob,
            email=data['email']
        )

        if result['success']:
            return jsonify({"message": "User registered successfully"}), 201
        else:
            return jsonify({"error": result['error']}), 400


    @app.route("/api/admin/users", methods=["GET"])
    @token_required
    @admin_required
    def list_users():
        """
        Alleen toegankelijk voor admin gebruikers. Toont een lijst van alle geregistreerde gebruikers.
        """
        print("Admin user is accessing the user list")
        users = db.session.query(
            User.id,
            User.first_name,
            User.last_name,
            User.email,
            User.date_of_birth,
            User.created_at
        ).all()

        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "date_of_birth": user.date_of_birth.isoformat(),
                "created_at": user.created_at.isoformat()
            })
        return jsonify(user_list), 200



    @app.route("/api/auth/forgot-password", methods=["POST"])
    def forgot_password():
        """
        Stap 1: gebruiker geeft zijn e-mail op.
        We sturen altijd dezelfde response, ook als het e-mail niet bestaat
        (voorkomt user enumeration).
        """
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({"error": "E-mailadres is verplicht"}), 400

        request_password_reset(data['email'])

        # Altijd dezelfde neutrale boodschap teruggeven
        return jsonify({
            "message": "Als dit e-mailadres bij ons bekend is, ontvang je binnen enkele minuten een resetlink."
        }), 200

    @app.route("/api/auth/reset-password", methods=["POST"])
    def reset_password():
        """
        Stap 2: gebruiker heeft de link in de mail geopend en vult
        zijn nieuwe wachtwoord in.
        """
        data = request.get_json()
        if not data or 'token' not in data or 'new_password' not in data:
            return jsonify({"error": "Token en nieuw wachtwoord zijn verplicht"}), 400

        if len(data['new_password']) < 8:
            return jsonify({"error": "Wachtwoord moet minimaal 8 tekens bevatten"}), 400

        result = reset_password_with_token(data['token'], data['new_password'])

        if result['success']:
            return jsonify({"message": "Wachtwoord succesvol gewijzigd! Je kunt nu inloggen."}), 200
        else:
            return jsonify({"error": result['error']}), 400

    # ---------------------------------------------------------------------------
    # Match routes
    # ---------------------------------------------------------------------------

    @app.route("/api/matches/<int:match_id>/result", methods=["POST"])
    @token_required
    def update_match_result(match_id):
        data = request.get_json()

        match = db.session.get(Match, match_id)

        if match is None:
            return jsonify({"error": "Match not found"}), 404

        home_score = data.get("score_home")
        away_score = data.get("score_away")

        winner_team_id = data.get("winner_team_id")
        if winner_team_id and winner_team_id not in (match.home_team_id, match.away_team_id):
            return jsonify({"error": "winner_team_id must be the home or away team"}), 400

        try:
            new_score = Score(
                set=1,
                home_score=home_score,
                away_score=away_score
            )
            db.session.add(new_score)
            db.session.flush()
            match.result = new_score.id

            if "user_id" in data:
                match.reported_by = data["user_id"]

            db.session.commit()

            apply_match_result(match_id)

            return jsonify({"message": "Match result recorded, score added"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    return app
