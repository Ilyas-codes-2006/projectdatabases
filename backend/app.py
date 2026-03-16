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
from clubs import show_clubs, join_club

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

    @app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
    @token_required
    @admin_required
    def delete_user(user_id):
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # No selfDelete
        current_admin_id = int(g.current_user['sub'])
        if user.id == current_admin_id:
            return jsonify({"error": "You cannot delete yourself"}), 400

        user_name = f"{user.first_name} {user.last_name}"
        
        try:
            # Link is: User -> Member
            member_ids = [m.id for m in Member.query.filter_by(user_id=user_id).all()]
            
            if member_ids:
                # TeamMember links to Member, NOT directly to User
                team_members = TeamMember.query.filter(TeamMember.member_id.in_(member_ids)).all()
                team_member_ids = [tm.id for tm in team_members]
                
                if team_member_ids:
                    Availability.query.filter(Availability.team_member_id.in_(team_member_ids)).delete(synchronize_session=False)
                
                TeamMember.query.filter(TeamMember.member_id.in_(member_ids)).delete(synchronize_session=False)

            Member.query.filter_by(user_id=user_id).delete(synchronize_session=False)
            
            PasswordResetToken.query.filter_by(user_id=user_id).delete(synchronize_session=False)
            Request.query.filter_by(user_id=user_id).delete(synchronize_session=False)

            # Nullify matches reported_by to keep history
            Match.query.filter_by(reported_by=user_id).update({Match.reported_by: None}, synchronize_session=False)

            # Force FLUSH to ensure dependent rows are gone
            db.session.flush()

            db.session.delete(user)
            db.session.commit()
            
            return jsonify({"message": f"User {user_name} deleted successfully"}), 200
    @app.route("/api/admin/users/<int:user_id>/details", methods=["GET"])
    @token_required
    @admin_required
    def get_user_details(user_id):
        """Haal huidige club en team op van een specifieke gebruiker."""
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "Gebruiker niet gevonden"}), 404

        member = db.session.query(Member).filter_by(user_id=user_id).first()

        club_id = None
        team_id = None

        if member:
            club_id = member.club_id
            team_member = db.session.query(TeamMember).filter_by(member_id=member.id).first()
            if team_member:
                team_id = team_member.team_id

        return jsonify({"club_id": club_id, "team_id": team_id}), 200

    @app.route("/api/admin/clubs", methods=["GET"])
    @token_required
    @admin_required
    def list_all_clubs():
        """Haal alle clubs op voor de admin dropdown."""
        clubs = db.session.query(Club).all()
        return jsonify([
            {"id": c.id, "name": c.name, "city": c.city}
            for c in clubs
        ]), 200

    @app.route("/api/admin/teams", methods=["GET"])
    @token_required
    @admin_required
    def list_all_teams():
        """Haal alle teams op met hun ledenaantal voor de admin dropdown."""
        teams = db.session.query(
            Team.id,
            Team.name,
            db.func.count(TeamMember.id).label("member_count")
        ).outerjoin(TeamMember, TeamMember.team_id == Team.id).group_by(Team.id).all()

        return jsonify([
            {"id": t.id, "name": t.name, "member_count": t.member_count}
            for t in teams
        ]), 200

    @app.route("/api/admin/users/<int:user_id>/club", methods=["PUT"])
    @token_required
    @admin_required
    def update_user_club(user_id):
        """
        Pas de club van een gebruiker aan.
        Stuur club_id: null om de gebruiker uit zijn club te verwijderen.
        """
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Geen data meegegeven"}), 400

        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "Gebruiker niet gevonden"}), 404

        new_club_id = data.get("club_id")  # kan None zijn

        if new_club_id is not None:
            club = db.session.get(Club, new_club_id)
            if not club:
                return jsonify({"error": "Club niet gevonden"}), 404

        member = db.session.query(Member).filter_by(user_id=user_id).first()
        if member:
            member.club_id = new_club_id
        else:
            from datetime import date
            member = Member(user_id=user_id, club_id=new_club_id, joined_at=date.today())
            db.session.add(member)

        try:
            db.session.commit()
            return jsonify({"message": "Club succesvol bijgewerkt"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/admin/users/<int:user_id>/team", methods=["PUT"])
    @token_required
    @admin_required
    def update_user_team(user_id):
        """
        Pas het team van een gebruiker aan.
        Stuur team_id: null om de gebruiker uit zijn team te verwijderen.
        """
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Geen data meegegeven"}), 400

        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "Gebruiker niet gevonden"}), 404

        new_team_id = data.get("team_id")  # kan None zijn

        if new_team_id is not None:
            team = db.session.get(Team, new_team_id)
            if not team:
                return jsonify({"error": "Team niet gevonden"}), 404

            count = db.session.query(TeamMember).filter_by(team_id=new_team_id).count()
            if count >= 2:
                return jsonify({"error": "Dit team zit al vol (max 2 leden)"}), 400

        # Zorg dat member record bestaat
        from datetime import date
        member = db.session.query(Member).filter_by(user_id=user_id).first()
        if not member:
            member = Member(user_id=user_id, club_id=None, joined_at=date.today())
            db.session.add(member)
            db.session.flush()

        # Verwijder huidig team membership
        db.session.query(TeamMember).filter_by(member_id=member.id).delete()

        # Voeg toe aan nieuw team indien opgegeven
        if new_team_id is not None:
            db.session.add(TeamMember(team_id=new_team_id, member_id=member.id))

        try:
            db.session.commit()
            return jsonify({"message": "Team succesvol bijgewerkt"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

        except Exception as e:
            db.session.rollback()
            print(f"Delete error: {e}")
            return jsonify({"error": "Could not delete user. Database error.", "details": str(e)}), 500

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

    @app.get("/api/clubs")
    @token_required
    def get_clubs():
        clubs_data = show_clubs()
        return jsonify(clubs_data)

    @app.post("/api/clubs/<int:club_id>/join")
    @token_required
    def join_club_(club_id):
        result = join_club(club_id)
        return jsonify(result)

    return app

