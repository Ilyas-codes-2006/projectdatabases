from flask import jsonify, request, g, Blueprint
from datetime import date
from db import *
from auth import register_user, login_user
from email_validator import validate_email, EmailNotValidError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["POST"])
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

@auth_bp.route("/register", methods=["POST"])
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
