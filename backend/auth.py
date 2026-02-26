import functools
from datetime import datetime, timezone, timedelta

import jwt
import psycopg
from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

from config import config_data as config
from db import get_conn


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_user(first_name, last_name, email, age, sport, skill_level, club, password):
    """Register a new user with hashed password."""
    password_hash = generate_password_hash(password)

    with get_conn() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO users (first_name, last_name, email, age, sport, skill_level, club, password_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (first_name, last_name, email, age, sport, skill_level, club, password_hash))
                user_id = cur.fetchone()[0]
                conn.commit()
                return {'success': True, 'user_id': user_id}
            except psycopg.errors.UniqueViolation:
                return {'success': False, 'error': 'Email already registered'}
            except Exception as e:
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
    """Verify credentials and return a JWT on success."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, first_name, last_name, password_hash FROM users WHERE email = %s",
                (email,),
            )
            row = cur.fetchone()

    if row is None:
        return {'success': False, 'error': 'Invalid email or password'}

    user_id, first_name, last_name, password_hash = row

    if not check_password_hash(password_hash, password):
        return {'success': False, 'error': 'Invalid email or password'}

    token = _generate_token(user_id, email, first_name)
    return {
        'success': True,
        'token': token,
        'name': f"{first_name} {last_name}",
        'user_id': user_id,
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
