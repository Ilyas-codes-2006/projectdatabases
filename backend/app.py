from flask import Flask, jsonify, request, g
import jwt
from flask_cors import CORS
from flask_mail import Mail
from config import config_data as config
from datetime import date
from db import *
from auth import token_required, mail
from teams import show_teams, create_team, join_team
from routes import _auth, admin, club, profile

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

    app.register_blueprint(_auth.auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin.admin_bp, url_prefix="/api/admin")
    app.register_blueprint(club.club_bp, url_prefix="/api/clubs")
    app.register_blueprint(profile.profile_bp, url_prefix="/api/profile")

    with app.app_context():
        db.create_all()

    @app.get("/")
    def root():
        return {"status": "MatchUp backend ok"}

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

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
