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
