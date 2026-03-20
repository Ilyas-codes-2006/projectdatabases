from flask import Flask, jsonify, request, g
import jwt
from flask_cors import CORS
from flask_mail import Mail
from config import config_data as config
from datetime import date
from db import *
from auth import register_user, login_user, token_required, mail, request_password_reset, reset_password_with_token, \
    admin_required
from teams import show_teams, create_team, join_team
from clubs import show_clubs, request_new_club, request_join_club, review_join_request

from flask import Flask
from flask_cors import CORS
from db import db
from flask_mail import Mail

mail = Mail()

def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app)

    # Default config
    app.config.from_mapping(
        DEBUG=config["debug"],
        SQLALCHEMY_DATABASE_URI=config["db_connstr"],
        SQLALCHEMY_TRACK_MODIFICATIONS=False,

        MAIL_SERVER=config["mail_server"],
        MAIL_PORT=config["mail_port"],
        MAIL_USE_TLS=True,
        MAIL_USERNAME=config["mail_username"],
        MAIL_PASSWORD=config["mail_password"],
        MAIL_DEFAULT_SENDER=config["mail_sender"],
    )

    # Test config overschrijft alles
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    mail.init_app(app)

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



    # ---------------------------------------------------------------------------
    # Profile routes
    # ---------------------------------------------------------------------------

    @app.route("/api/profile", methods=["GET"])
    @token_required
    def get_profile():
        user_id = g.current_user['sub']
        user = db.session.get(User, int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "bio": user.bio or "",
            "photo_url": user.photo_url or "",
            "date_of_birth": user.date_of_birth.isoformat(),
        }), 200

    @app.route("/api/profile", methods=["PUT"])
    @token_required
    def update_profile():
        user_id = g.current_user['sub']
        user = db.session.get(User, int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 404
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        if 'bio' in data:
            user.bio = data['bio']
        if 'photo_url' in data:
            user.photo_url = data['photo_url']
        try:
            db.session.commit()
            return jsonify({"message": "Profile updated successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

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

    @app.get("/api/teams")
    @token_required
    def get_teams():
        teams_data = show_teams()
        return jsonify(teams_data) #return als JSOn

    @app.post("/api/teams")
    def new_team():
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({"error": "Missing token"}), 401
        try:
            payload = jwt.decode(token, config['jwt_secret'], algorithms=[config['jwt_algorithm']])
            user_id = payload['sub']
        except Exception:
            return jsonify({"error": "Invalid token"}), 401
        data = request.get_json()
        if not data or 'team_name' not in data:
            return jsonify({"error": "team_name is required"}), 400
        team_data = create_team(data['team_name'], user_id)
        return jsonify(team_data)

    @app.post("/api/teams/<int:team_id>/join")
    @token_required
    def join_team_(team_id):
        result = join_team(team_id)
        return jsonify(result)

    @app.get("/api/profile/club-status")
    @token_required
    def club_status():
        user_id = int(g.current_user['sub'])
        member = db.session.query(Member).filter_by(user_id=user_id).first()
        if member and member.is_admin and member.club_id:
            club = db.session.get(Club, member.club_id)
            return jsonify({
                "is_club_admin": True,
                "club_id": member.club_id,
                "club_name": club.name if club else None,
            }), 200
        return jsonify({"is_club_admin": False, "club_id": None, "club_name": None}), 200

    @app.get("/api/admin/club-requests/<int:request_id>")
    @token_required
    @admin_required
    def get_club_request_detail(request_id):
        import json as _json
        r = db.session.get(ClubRequest, request_id)
        if not r:
            return jsonify({"error": "not_found"}), 404
        user = db.session.get(User, r.user_id)
        try:
            attachments = _json.loads(r.attachments) if r.attachments else []
        except Exception:
            attachments = []
        return jsonify({
            "success": True,
            "id": r.id,
            "club_name": r.club_name,
            "city": r.city,
            "motivation": r.motivation,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "requester_name": f"{user.first_name} {user.last_name}" if user else "?",
            "requester_email": user.email if user else "?",
            "attachments": attachments,
        }), 200

    @app.get("/api/clubs/<int:club_id>/members")
    @token_required
    def get_club_members(club_id):
        user_id = int(g.current_user['sub'])
        # Only club admin of this club can view members
        requester = db.session.query(Member).filter_by(user_id=user_id, club_id=club_id, is_admin=True).first()
        if not requester and not g.current_user.get('is_admin'):
            return jsonify({"error": "forbidden"}), 403
        members_q = db.session.query(Member).filter_by(club_id=club_id).all()
        result = []
        for m in members_q:
            u = db.session.get(User, m.user_id)
            if u:
                result.append({
                    "id": u.id,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                    "email": u.email,
                    "elo": m.elo,
                    "is_admin": m.is_admin,
                })
        return jsonify({"success": True, "members": result}), 200

    @app.get("/api/clubs")
    @token_required
    def get_clubs():
        clubs_data = show_clubs()
        return jsonify(clubs_data)

    @app.post("/api/clubs/<int:club_id>/join-request")
    @token_required
    def request_join_club_(club_id):
        data = request.get_json() or {}
        motivation = data.get("motivation", "").strip()
        result = request_join_club(club_id, motivation, mail)
        if result["success"]:
            return jsonify(result), 201
        return jsonify({"error": result.get("error")}), 400

    @app.get("/api/clubs/<int:club_id>/join-requests")
    @token_required
    def get_join_requests(club_id):
        user_id = int(g.current_user['sub'])
        # Must be club admin
        admin_member = db.session.query(Member).filter_by(
            user_id=user_id, club_id=club_id, is_admin=True
        ).first()
        if not admin_member:
            return jsonify({"error": "forbidden"}), 403

        reqs = db.session.query(JoinRequest).filter_by(club_id=club_id).order_by(
            JoinRequest.created_at.desc()
        ).all()
        result = []
        for r in reqs:
            u = db.session.get(User, r.user_id)
            result.append({
                "id": r.id,
                "user_id": r.user_id,
                "requester_name": f"{u.first_name} {u.last_name}" if u else "?",
                "requester_email": u.email if u else "?",
                "motivation": r.motivation,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            })
        return jsonify({"success": True, "requests": result}), 200

    @app.post("/api/clubs/join-requests/<int:join_request_id>/review")
    @token_required
    def review_join_request_(join_request_id):
        data = request.get_json() or {}
        action = data.get("action")
        if action not in ("approve", "reject"):
            return jsonify({"error": "action must be 'approve' or 'reject'"}), 400
        result = review_join_request(join_request_id, action, mail)
        if result["success"]:
            return jsonify(result), 200
        return jsonify({"error": result.get("error")}), 400

    @app.post("/api/clubs/request")
    @token_required
    def request_club():
        import json, base64
        # Accepteer zowel JSON als multipart/form-data
        if request.content_type and "multipart/form-data" in request.content_type:
            club_name = (request.form.get("club_name") or "").strip()
            city      = (request.form.get("city") or "").strip()
            motivation = (request.form.get("motivation") or "").strip()
            files = request.files.getlist("attachments")
            attachments = []
            for f in files:
                if f and f.filename:
                    data_b64 = base64.b64encode(f.read()).decode("utf-8")
                    attachments.append({
                        "filename": f.filename,
                        "mimetype": f.mimetype or "application/octet-stream",
                        "data_b64": data_b64,
                    })
        else:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid request"}), 400
            club_name  = data.get("club_name", "").strip()
            city       = data.get("city", "").strip()
            motivation = data.get("motivation", "").strip()
            attachments = []

        if not club_name or not city:
            return jsonify({"error": "club_name and city are required"}), 400

        result = request_new_club(club_name, city, motivation, attachments, mail)
        if result["success"]:
            return jsonify(result), 201
        return jsonify({"error": result.get("error")}), 400

    @app.get("/api/admin/club-requests")
    @token_required
    @admin_required
    def get_club_requests():
        import json as _json
        from db import ClubRequest, User
        requests_q = db.session.query(ClubRequest).order_by(ClubRequest.created_at.desc()).all()
        result = []
        for r in requests_q:
            user = db.session.get(User, r.user_id)
            try:
                att_count = len(_json.loads(r.attachments)) if r.attachments else 0
            except Exception:
                att_count = 0
            result.append({
                "id": r.id,
                "club_name": r.club_name,
                "city": r.city,
                "motivation": r.motivation,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "requester_name": f"{user.first_name} {user.last_name}" if user else "?",
                "requester_email": user.email if user else "?",
                "attachments_count": att_count,
            })
        return jsonify({"success": True, "requests": result}), 200

    @app.post("/api/admin/club-requests/<int:request_id>/review")
    @token_required
    @admin_required
    def review_club_request(request_id):
        from clubs import review_club_request as do_review
        data = request.get_json()
        action = data.get("action")  # "approve" or "reject"
        if action not in ("approve", "reject"):
            return jsonify({"error": "action must be 'approve' or 'reject'"}), 400
        result = do_review(request_id, action, mail)
        if result["success"]:
            return jsonify(result), 200
        return jsonify({"error": result.get("error")}), 400

    return app