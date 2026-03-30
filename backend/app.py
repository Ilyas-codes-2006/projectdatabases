from flask import Flask, jsonify, request, g
import jwt
from flask_cors import CORS
from flask_mail import Mail
from config import config_data as config
from datetime import date
from db import *
from auth import register_user, login_user, token_required, mail, request_password_reset, reset_password_with_token, \
    admin_required, change_user_email, change_user_name, change_user_birthday
from teams import show_teams, create_team, join_team
from email_validator import validate_email, EmailNotValidError
from clubs import show_clubs, request_new_club, request_join_club, request_join, review_join_request, leave_club, \
    delete_club, _delete_club_cascade, _auto_delete_if_no_admin

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

        email = data['email'].lower()
        try:
            res = validate_email(email)
            email = res.normalized
        except EmailNotValidError:
            return jsonify({"error": "Invalid e-mail."}), 400

        result = login_user(email, data['password'])

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
            return jsonify({"error": "Invalid date of birth!"}), 400

        email = data['email'].lower()
        try:
            res = validate_email(email)
            email = res.normalized
        except EmailNotValidError:
            return jsonify({"error": "Invalid e-mail."}), 400

        today = date.today()
        latest_accepting_date = date(today.year - 6, today.month, today.day)

        if parsed_dob > latest_accepting_date:
            return jsonify(
                {"error": "Invalid date of birth. You have to be at least 6 years old to have an account!"}), 400

        result = register_user(
            last_name=data['last_name'],
            first_name=data['first_name'],
            password=data['password'],
            bio=data.get('bio', ''),
            is_admin=data.get('is_admin', False),
            date_of_birth=parsed_dob,
            email=email
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
            members = Member.query.filter_by(user_id=user_id).all()
            member_ids = [m.id for m in members]
            # Track which clubs this user was admin of, so we can check afterward
            administered_club_ids = [m.club_id for m in members if m.is_admin and m.club_id]

            if member_ids:
                # TeamMember links to Member, NOT directly to User
                team_members = TeamMember.query.filter(TeamMember.member_id.in_(member_ids)).all()
                team_member_ids = [tm.id for tm in team_members]

                if team_member_ids:
                    Availability.query.filter(Availability.team_member_id.in_(team_member_ids)).delete(
                        synchronize_session=False)

                TeamMember.query.filter(TeamMember.member_id.in_(member_ids)).delete(synchronize_session=False)

            Member.query.filter_by(user_id=user_id).delete(synchronize_session=False)

            PasswordResetToken.query.filter_by(user_id=user_id).delete(synchronize_session=False)
            Request.query.filter_by(user_id=user_id).delete(synchronize_session=False)
            JoinRequest.query.filter_by(user_id=user_id).delete(synchronize_session=False)

            # Nullify matches reported_by to keep history
            Match.query.filter_by(reported_by=user_id).update({Match.reported_by: None}, synchronize_session=False)

            db.session.flush()

            # Auto-delete any club the user administered that now has no admin left
            for club_id in administered_club_ids:
                _auto_delete_if_no_admin(club_id)

            db.session.flush()

            db.session.delete(user)
            db.session.commit()

            return jsonify({"message": f"User {user_name} deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

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

        new_club_id = data.get("club_id")

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

        new_team_id = data.get("team_id")

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
            if new_team_id is None:
                # No member row and no team to assign — nothing to do
                return jsonify({"message": "Team succesvol bijgewerkt"}), 200
            # Cannot assign a team without a club — admin must assign club first
            return jsonify({"error": "Gebruiker heeft nog geen club. Wijs eerst een club toe."}), 400

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
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({"error": "E-mailadres is verplicht"}), 400

        request_password_reset(data['email'])

        return jsonify({
            "message": "Als dit e-mailadres bij ons bekend is, ontvang je binnen enkele minuten een resetlink."
        }), 200

    @app.route("/api/auth/reset-password", methods=["POST"])
    def reset_password():
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
        return jsonify(teams_data)

    @app.post("/api/teams")
    @token_required
    def new_team():
        user_id = g.current_user["sub"]
        data = request.get_json()
        if not data or 'team_name' not in data or 'ladder_id' not in data:
            return jsonify({"error": "team_name and ladder_id are required"}), 400

        team_data = create_team(data['team_name'], user_id, data['ladder_id'])

        if team_data["success"]:
            return jsonify(team_data), 201
        else:
            return jsonify(team_data), 400

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

    @app.post("/api/clubs/<int:club_id>/request_join")
    @token_required
    def join_club_(club_id):
        result = request_join(club_id)
        return jsonify(result)

    @app.get("/api/clubs/<int:club_id>/join-requests")
    @token_required
    def get_join_requests(club_id):
        user_id = int(g.current_user['sub'])
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
        if request.content_type and "multipart/form-data" in request.content_type:
            club_name = (request.form.get("club_name") or "").strip()
            city = (request.form.get("city") or "").strip()
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
            club_name = data.get("club_name", "").strip()
            city = data.get("city", "").strip()
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
        action = data.get("action")
        if action not in ("approve", "reject"):
            return jsonify({"error": "action must be 'approve' or 'reject'"}), 400
        result = do_review(request_id, action, mail)
        if result["success"]:
            return jsonify(result), 200
        return jsonify({"error": result.get("error")}), 400

    @app.post("/api/clubs/<int:club_id>/leave")
    @token_required
    def leave_club_(club_id):
        result = leave_club(club_id)
        return jsonify(result)

    @app.delete("/api/clubs/<int:club_id>")
    @token_required
    def delete_club_(club_id):
        user_id = int(g.current_user['sub'])
        is_admin = g.current_user.get('is_admin', False)
        result = delete_club(club_id, user_id, is_admin)
        if result["success"]:
            return jsonify(result), 200
        if result.get("error") == "forbidden":
            return jsonify(result), 403
        if result.get("error") == "club_not_found":
            return jsonify(result), 404
        return jsonify(result), 500

    @app.delete("/api/admin/clubs/<int:club_id>")
    @token_required
    @admin_required
    def admin_delete_club(club_id):
        user_id = int(g.current_user['sub'])
        result = delete_club(club_id, user_id, is_site_admin=True)
        if result["success"]:
            return jsonify(result), 200
        if result.get("error") == "club_not_found":
            return jsonify(result), 404
        return jsonify(result), 500

    @app.route("/api/profile/change-email", methods=["PUT"])
    @token_required
    def change_email():
        data = request.get_json()
        user_id = g.current_user['sub']
        if not data or 'new_email' not in data or 'password' not in data:
            return jsonify({"error": "new_email and password are required"}), 400

        new_email = data['new_email'].lower()
        try:
            res = validate_email(new_email)
            new_email = res.normalized
        except EmailNotValidError:
            return jsonify({"error": "New email is invalid!"}), 400

        result = change_user_email(user_id, new_email, data['password'])
        if result['success']:
            return jsonify({"message": result['message']}), 200
        else:
            return jsonify({"error": result['error']}), 400

    @app.route("/api/profile/change-name", methods=["PUT"])
    @token_required
    def change_name():
        user_id = g.current_user['sub']
        data = request.get_json()
        if not data or 'new_first_name' not in data or 'new_last_name' not in data or 'password' not in data:
            return jsonify({"error": "new_first_name, new_last_name, and password are required"}), 400

        result = change_user_name(user_id, data['new_first_name'], data['new_last_name'], data['password'])
        if result['success']:
            return jsonify({"message": result['message']}), 200
        else:
            return jsonify({"error": result['error']}), 400

    @app.route("/api/profile/change-birthday", methods=["PUT"])
    @token_required
    def change_birthday():
        user_id = g.current_user['sub']
        data = request.get_json()

        if not data or 'new_birthday' not in data or 'password' not in data:
            return jsonify({"error": "new_birthday and password are required"}), 400

        # Converteer string naar date object, hetzelfde zoals register_user
        try:
            new_birthday_date = date.fromisoformat(data['new_birthday'])
        except ValueError:
            return jsonify({"error": "Use YYYY-MM-DD"}), 400

        today = date.today()
        latest_accepting_date = date(today.year - 6, today.month, today.day)

        if new_birthday_date > latest_accepting_date:
            return jsonify(
                {"error": "Invalid date of birth. You have to be at least 6 years old to have an account!"}), 400

        result = change_user_birthday(user_id, new_birthday_date, data['password'])

        if result['success']:
            return jsonify({"message": result['message']}), 200
        else:
            return jsonify({"error": result['error']}), 400

    @app.route("/api/notifications", methods=["GET"])
    @token_required
    def get_notifications():
        user_id = int(g.current_user["sub"])
        result = []

        # club admin: pending join requests
        admin_memberships = db.session.query(Member).filter_by(
            user_id=user_id, is_admin=True
        ).all()

        if admin_memberships:
            admin_club_ids = [m.club_id for m in admin_memberships]
            pending_requests = db.session.query(JoinRequest, User, Club).join(
                User, User.id == JoinRequest.user_id
            ).join(
                Club, Club.id == JoinRequest.club_id
            ).filter(
                JoinRequest.club_id.in_(admin_club_ids),
                JoinRequest.status == 'pending'
            ).all()

            for req, user, club in pending_requests:
                result.append({
                    "type": "join_request",
                    "message": f"{user.first_name} {user.last_name} wil lid worden van {club.name}",
                })

        # team events ongelezen joins/leaves gericht aan jou
        events = db.session.query(TeamEvent, User, Team).join(
            User, User.id == TeamEvent.actor_id
        ).join(
            Team, Team.id == TeamEvent.team_id
        ).filter(
            TeamEvent.target_id == user_id,
            TeamEvent.read == False
        ).all()

        for event, actor, team in events:
            action_nl = "gejoined" if event.action == "joined" else "verlaten"
            result.append({
                "type": "team_event",
                "message": f"{actor.first_name} {actor.last_name} heeft {team.name} {action_nl}",
            })

        return jsonify(result), 200

    @app.patch("/api/notifications/read")
    @token_required
    def mark_notifications_read():
        user_id = int(g.current_user["sub"])
        db.session.query(TeamEvent).filter_by(
            target_id=user_id, read=False
        ).update({"read": True})
        db.session.commit()
        return jsonify({"ok": True}), 200

    @app.route("/api/availability", methods=["POST"])
    @token_required
    def save_availability():
        user_id = int(g.current_user['sub'])
        data = request.get_json()

        if not data or 'dates' not in data:
            return jsonify({"error": "No dates selected."}), 400
        member = db.session.query(Member).filter_by(user_id=user_id).first()
        if not member:
            return jsonify({"error": "You have not joined a club yet."}), 400

        try:
            requested_dates = set()
            for date_str in data['dates']:
                try:
                    requested_dates.add(date.fromisoformat(date_str))
                except ValueError:
                    continue

            existing_records = db.session.query(Availability).filter_by(user_id=user_id).all()
            existing_dates = {record.date for record in existing_records}

            dates_to_add = requested_dates - existing_dates
            dates_to_remove = existing_dates - requested_dates

            if dates_to_remove:
                db.session.query(Availability).filter(
                    Availability.user_id == user_id,
                    Availability.date.in_(dates_to_remove)
                ).delete(synchronize_session=False)

            for d in dates_to_add:
                new_avail = Availability(
                    user_id=user_id,
                    date=d,
                    is_available=True
                )
                db.session.add(new_avail)

            db.session.commit()

            return jsonify({
                "message": f"Succes! {len(dates_to_add)} dates added, {len(dates_to_remove)} removed."
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Error while saving: {str(e)}"}), 500

    @app.route("/api/availability", methods=["GET"])
    @token_required
    def get_availability():
        user_id = int(g.current_user['sub'])

        member = db.session.query(Member).filter_by(user_id=user_id).first()
        if not member:
            return jsonify({"dates": []}), 200

        records = db.session.query(Availability).filter_by(user_id=user_id).all()

        dates = [record.date.isoformat() for record in records]

        return jsonify({"dates": dates}), 200

    @app.get("/api/ladders")
    @token_required
    def get_ladders():
        ladders = db.session.query(Ladder).order_by(Ladder.start_date.desc()).all()
        result = []

        for ladder in ladders:
            teams = db.session.query(Team).filter_by(ladder_id=ladder.id).all()
            sport = db.session.get(Sport, ladder.sport_id)
            teams_data = []

            for team in teams:
                members = (
                    db.session.query(Member, User)
                    .join(TeamMember, TeamMember.member_id == Member.id)
                    .join(User, User.id == Member.user_id)
                    .filter(TeamMember.team_id == team.id)
                    .all()
                )
                avg_elo = round(sum((m.elo or 0) for m, u in members) / len(members)) if members else 0
                member_names = [f"{u.first_name} {u.last_name}" for m, u in members]

                teams_data.append({
                    "id": team.id,
                    "name": team.name,
                    "elo": avg_elo,
                    "members": member_names,
                })

            teams_data.sort(key=lambda x: x["elo"], reverse=True)

            result.append({
                "id": ladder.id,
                "name": ladder.name,
                "start_date": ladder.start_date.isoformat(),
                "end_date": ladder.end_date.isoformat(),
                "team_size": sport.team_size,
                "teams": teams_data,
            })

        return jsonify(result), 200

    @app.post("/api/ladders/<int:ladder_id>/join")
    @token_required
    def join_ladder(ladder_id):
        user_id = int(g.current_user['sub'])

        # Moet in een club zitten
        member = db.session.query(Member).filter_by(user_id=user_id).first()
        if not member or not member.club_id:
            return {"success": False, "error": "not_in_club"}, 400

        # Ladder moet bestaan
        ladder = db.session.get(Ladder, ladder_id)
        if not ladder:
            return jsonify({"error": "ladder_not_found"}), 404

        # Check sport team_size
        sport = db.session.get(Sport, ladder.sport_id)
        if not sport:
            return jsonify({"error": "sport_not_found"}), 404

        if sport.team_size > 1:
            return jsonify({"error": "team_required", "message": "This ladder requires a team"}), 400

        # Check of user al in deze ladder zit
        already = (
            db.session.query(TeamMember)
            .join(Team, Team.id == TeamMember.team_id)
            .filter(TeamMember.member_id == member.id, Team.ladder_id == ladder_id)
            .first()
        )
        if already:
            return jsonify({"error": "already_in_ladder"}), 400

        # Maak solo team aan met naam van gebruiker
        user = db.session.get(User, user_id)
        solo_team = Team(
            name=f"{user.first_name} {user.last_name}",
            ladder_id=ladder_id,
            created_at=date.today()
        )
        db.session.add(solo_team)
        db.session.flush()

        db.session.add(TeamMember(team_id=solo_team.id, member_id=member.id))
        db.session.commit()

        return jsonify({"success": True, "message": "joined_ladder"}), 200

    return app
