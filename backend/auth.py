import functools
from datetime import datetime, timezone, timedelta

import jwt
import psycopg
from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

from config import config_data as config
from db import db


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_user(last_name, first_name, password, bio, is_admin, date_of_birth, email):
    password_hash = generate_password_hash(password)
    
    if User.query.filter_by(email=email).first():
        return {'success': False, 'error': 'Email already registered'}

    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        date_of_birth=date_of_birth,
        bio=bio,
        is_admin=is_admin,
        created_at=datetime.now(),
        password=password_hash
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return {'success': True, 'user_id': new_user.id}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def _generate_token(user_id: int, email: str, first_name: str) -> str:
    """Create a signed JWT for the given user."""
    payload = {
        'sub': user_id,
        'email': email,
        'first_name': first_name,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(hours=config['jwt_expiry_hours']),
    }
    return jwt.encode(payload, config['jwt_secret'], algorithm=config['jwt_algorithm'])


def login_user(email: str, password: str) -> dict:
    # Haal de gebruiker op via het model
    user = User.query.filter_by(email=email).first()

    # Gebruiker niet gevonden of ongeldig wachtwoord
    if user is None or not check_password_hash(user.password_hash, password):
        return {'success': False, 'error': 'Invalid email or password'}

    # _generate_token blijft hetzelfde
    token = _generate_token(user.id, user.email, user.first_name)
    return {
        'success': True,
        'token': token,
        'name': f"{user.first_name} {user.last_name}",
        'user_id': user.id,
    }


# ---------------------------------------------------------------------------
# JWT middleware decorator
# ---------------------------------------------------------------------------

def token_required(f):
    """Decorator that validates the Authorization Bearer token.
    On success, ``g.current_user`` is set to the decoded JWT payload.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid token'}), 401
        token = auth_header.split(' ', 1)[1]
        try:
            payload = jwt.decode(token, config['jwt_secret'], algorithms=[config['jwt_algorithm']])
            g.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated
