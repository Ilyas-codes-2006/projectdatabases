from flask import Blueprint, jsonify, request, g
from datetime import date
from db import *
from auth import token_required, change_user_email, change_user_name, change_user_birthday
from email_validator import validate_email, EmailNotValidError

profile_bp = Blueprint('profile', __name__)

@profile_bp.route("", methods=["GET"])
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

@profile_bp.route("", methods=["PUT"])
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

@profile_bp.get("/club-status")
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

@profile_bp.route("/change-email", methods=["PUT"])
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

@profile_bp.route("/change-name", methods=["PUT"])
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

@profile_bp.route("/change-birthday", methods=["PUT"])
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
