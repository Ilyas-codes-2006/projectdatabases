import functools
import secrets
from datetime import datetime, timezone, timedelta

import jwt
import psycopg
from flask import request, jsonify, g
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

from config import config_data as config
from db import *

# Mail instance — wordt geïnitialiseerd via mail.init_app(app) in app.py
mail = Mail()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_user(last_name, first_name, password, bio, is_admin, date_of_birth, email):
    # email should have been validated in app.py register()
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

def _generate_token(user_id: int, email: str, first_name: str, is_admin: bool) -> str:
    """Create a signed JWT for the given user."""
    payload = {
        # JWT spec expects the subject ('sub') to be a string
        'sub': str(user_id),
        'email': email,
        'first_name': first_name,
        'is_admin': is_admin,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(hours=config['jwt_expiry_hours']),
    }
    return jwt.encode(payload, config['jwt_secret'], algorithm=config['jwt_algorithm'])


def login_user(email: str, password: str) -> dict:
    # email should have been validated in app.py in login()
    user = User.query.filter_by(email=email).first()

    # We gebruiken user.password omdat dit zo in je db.py model gedefinieerd staat
    if user is None or not check_password_hash(user.password, password):
        return {'success': False, 'error': 'Invalid email or password'}

    token = _generate_token(user.id, user.email, user.first_name, user.is_admin)
    return {
        'success': True,
        'token': token,
        'name': f"{user.first_name} {user.last_name}",
        'user_id': user.id,
        'is_admin': user.is_admin
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

def admin_required(f):
    """
    Decorator that checks if the current user is an admin.
    Must be used after @token_required to ensure g.current_user is set.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        current_user = getattr(g, 'current_user', None)
        if not current_user or not current_user.get('is_admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# Wachtwoord vergeten — stap 1: aanvraag & e-mail versturen
# ---------------------------------------------------------------------------

def request_password_reset(email: str) -> dict:
    user = User.query.filter_by(email=email).first()

    if user is None:
        return {'success': True}

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    # Verwijder eventuele oude tokens
    PasswordResetToken.query.filter_by(user_id=user.id).delete()

    new_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc)
    )

    db.session.add(new_token)
    db.session.commit()

    reset_url = f"{config['frontend_url']}reset-password?token={token}&view=reset-password"

    msg = Message(
        subject="Wachtwoord resetten — MatchUp",
        sender=config['mail_sender'],
        recipients=[email]
    )
    msg.body = f"""Hallo {user.first_name},

Je hebt een wachtwoordreset aangevraagd voor je MatchUp-account.

Klik op de onderstaande link om je wachtwoord in te stellen.
Deze link is 5 minuten geldig en kan maar één keer gebruikt worden.

{reset_url}

Heb je dit niet zelf aangevraagd? Dan kun je deze e-mail veilig negeren.
Je wachtwoord blijft ongewijzigd.

— Het MatchUp Team
"""
    mail.send(msg)
    return {'success': True}


# ---------------------------------------------------------------------------
# Wachtwoord vergeten — stap 2: nieuw wachtwoord instellen
# ---------------------------------------------------------------------------

def reset_password_with_token(token: str, new_password: str) -> dict:
    reset_token = PasswordResetToken.query.filter_by(token=token).first()

    if reset_token is None:
        return {'success': False, 'error': 'Ongeldige of verlopen resetlink.'}

    if reset_token.used:
        return {'success': False, 'error': 'Deze resetlink is al gebruikt.'}

    # 1. Combine the date/time from DB with UTC awareness
    # Note: We use .combine if it's still coming back as a date,
    # but with db.DateTime, it will be a datetime object.
    expires_at = reset_token.expires_at

    # Ensure it is a datetime object and add UTC info if missing
    if isinstance(expires_at, datetime):
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    else:
        # Fallback if DB is still returning a date object
        expires_at = datetime.combine(expires_at, datetime.min.time()).replace(tzinfo=timezone.utc)

    # 2. Compare
    if datetime.now(timezone.utc) > expires_at:
        return {'success': False, 'error': 'Deze resetlink is verlopen.'}

    # 3. Update password
    user = db.session.get(User, reset_token.user_id)
    if user:
        user.password = generate_password_hash(new_password)
        reset_token.used = True
        db.session.commit()
        return {'success': True}

    return {'success': False, 'error': 'Gebruiker niet gevonden.'}

def change_user_email(user_id, new_email, password):
    user = db.session.get(User, user_id)
    if not user:
        return {"success": False, "error": "User not found"}

    # Wachtwoord check zoals in login_user
    if not check_password_hash(user.password, password):
        return {"success": False, "error": "Incorrect password"}

    # Controleer of het nieuwe e-mailadres al bestaat
    if db.session.query(User).filter(User.email == new_email).first():
        return {"success": False, "error": "Email already in use"}

    # Update e-mail
    user.email = new_email
    try:
        db.session.commit()
        return {"success": True, "message": "Email updated successfully"}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}

def change_user_name(user_id, new_first_name, new_last_name, password):
    user = db.session.get(User, user_id)
    if not user:
        return {"success": False, "error": "User not found"}

    # check wachtwoord zoals bij e-mail
    if not check_password_hash(user.password, password):
        return {"success": False, "error": "Incorrect password"}

    # Check of de naam hetzelfde is
    if (user.first_name.lower() == new_first_name.lower() and
        user.last_name.lower() == new_last_name.lower()):
        return {"success": False, "error": "New name is the same as current"}

    # Update de naam
    user.first_name = new_first_name
    user.last_name = new_last_name
    try:
        db.session.commit()
        return {"success": True, "message": "Name updated successfully"}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}
def change_user_birthday(user_id, new_birthday, password):
    user = db.session.get(User, user_id)
    if not user:
        return {"success": False, "error": "User not found"}

    # Check wachtwoord
    if not check_password_hash(user.password, password):
        return {"success": False, "error": "Incorrect password"}

    # Check of het hetzelfde is
    if user.date_of_birth == new_birthday:
        return {"success": False, "error": "New birthday is the same as current"}

    #Verander birthday
    user.date_of_birth = new_birthday
    try:
        db.session.commit()
        return {"success": True, "message": "Birthday updated successfully"}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}
