from flask import jsonify, request, g, Blueprint
from db import *
from auth import token_required, mail
from clubs import show_clubs, request_new_club, request_join_club, request_join, review_join_request, leave_club, \
    delete_club

club_bp = Blueprint('clubs', __name__)

@club_bp.get("/<int:club_id>/members")
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

@club_bp.get("")
@token_required
def get_clubs():
    clubs_data = show_clubs()
    return jsonify(clubs_data)

@club_bp.post("/<int:club_id>/join-request")
@token_required
def request_join_club_(club_id):
    data = request.get_json() or {}
    motivation = data.get("motivation", "").strip()
    result = request_join_club(club_id, motivation, mail)
    if result["success"]:
        return jsonify(result), 201
    return jsonify({"error": result.get("error")}), 400

@club_bp.post("/<int:club_id>/request_join")
@token_required
def join_club_(club_id):
    result = request_join(club_id)
    return jsonify(result)

@club_bp.get("/<int:club_id>/join-requests")
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

@club_bp.post("/join-requests/<int:join_request_id>/review")
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

@club_bp.post("/request")
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

@club_bp.post("/<int:club_id>/leave")
@token_required
def leave_club_(club_id):
    result = leave_club(club_id)
    return jsonify(result)

@club_bp.delete("/<int:club_id>")
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

@club_bp.post("/<int:club_id>/ladders")
@token_required
def create_club_ladder(club_id):
    """
    Club admin creates a new ladder for their club.
    Body: { name, team_size, rules, start_date, end_date }
    """
    from datetime import date as _date

    user_id = int(g.current_user["sub"])

    # Must be admin of this specific club
    admin_member = db.session.query(Member).filter_by(
        user_id=user_id, club_id=club_id, is_admin=True
    ).first()
    if not admin_member:
        return jsonify({"error": "forbidden"}), 403

    club = db.session.get(Club, club_id)
    if not club:
        return jsonify({"error": "club_not_found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    name = (data.get("name") or "").strip()
    team_size = data.get("team_size")
    rules = (data.get("rules") or "").strip()
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")

    if not name:
        return jsonify({"error": "name is required"}), 400
    if not team_size or not isinstance(team_size, int) or team_size < 1:
        return jsonify({"error": "team_size must be a positive integer"}), 400
    if not start_date_str or not end_date_str:
        return jsonify({"error": "start_date and end_date are required"}), 400

    try:
        start_date = _date.fromisoformat(start_date_str)
        end_date = _date.fromisoformat(end_date_str)
    except ValueError:
        return jsonify({"error": "Dates must be YYYY-MM-DD"}), 400

    if end_date < start_date:
        return jsonify({"error": "end_date must be >= start_date"}), 400

    # Reuse or create a Sport with the requested team_size
    sport = db.session.query(Sport).filter_by(team_size=team_size).first()
    if not sport:
        sport = Sport(
            name=f"Sport (team size {team_size})",
            team_size=team_size
        )
        db.session.add(sport)
        db.session.flush()

    ladder = Ladder(
        sport_id=sport.id,
        club_id=club_id,
        name=name,
        start_date=start_date,
        end_date=end_date,
        rules=rules or None,
    )
    db.session.add(ladder)
    try:
        db.session.commit()
        return jsonify({"success": True, "ladder_id": ladder.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@club_bp.get("/<int:club_id>/ladders")
@token_required
def get_club_ladders(club_id):
    """Return all ladders that belong to a specific club."""
    club = db.session.get(Club, club_id)
    if not club:
        return jsonify({"error": "club_not_found"}), 404

    ladders = db.session.query(Ladder).filter_by(club_id=club_id).all()
    result = []
    for l in ladders:
        sport = db.session.get(Sport, l.sport_id)
        team_count = db.session.query(Team).filter_by(ladder_id=l.id).count()
        result.append({
            "id": l.id,
            "name": l.name,
            "start_date": l.start_date.isoformat(),
            "end_date": l.end_date.isoformat(),
            "team_size": sport.team_size if sport else 1,
            "rules": l.rules or "",
            "team_count": team_count,
        })
    return jsonify({"success": True, "ladders": result}), 200
