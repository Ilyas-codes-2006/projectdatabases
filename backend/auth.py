import functools
import secrets
from datetime import datetime, timezone, timedelta

import jwt
import psycopg
from flask import request, jsonify, g
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

from config import config_data as config
from db import get_conn

# Mail instance — wordt geïnitialiseerd via mail.init_app(app) in app.py
mail = Mail()


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


# ---------------------------------------------------------------------------
# Wachtwoord vergeten — stap 1: aanvraag & e-mail versturen
# ---------------------------------------------------------------------------

def request_password_reset(email: str) -> dict:
    """
    Genereert een veilige reset-token, slaat die op in de database
    en stuurt een e-mail met de resetlink.

    BEVEILIGING: We geven altijd dezelfde response terug, ook als het
    e-mailadres niet bestaat. Zo kan niemand raden welke e-mails
    geregistreerd zijn (user enumeration attack voorkomen).
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, first_name FROM users WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()

    # Altijd success teruggeven — zie beveiliging hierboven
    if row is None:
        return {'success': True}

    user_id, first_name = row

    # Genereer een cryptografisch veilige willekeurige token (256 bits)
    token = secrets.token_urlsafe(32)

    # Token verloopt na 5 minuten
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Verwijder eventuele oude tokens voor deze gebruiker
            cur.execute(
                "DELETE FROM password_reset_tokens WHERE user_id = %s",
                (user_id,)
            )
            # Sla de nieuwe token op
            cur.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, token, expires_at)
            )
            conn.commit()

    # Bouw de resetlink
    reset_url = f"{config['frontend_url']}?token={token}&view=reset-password"

    # Verstuur de e-mail
    msg = Message(
        subject="Wachtwoord resetten — MatchUp",
        sender=config['mail_sender'],
        recipients=[email]
    )
    msg.body = f"""Hallo {first_name},

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
    """
    Valideert de reset-token en slaat het nieuwe wachtwoord op.

    Beveiligingschecks:
    1. Token moet bestaan in de database
    2. Token mag niet al gebruikt zijn
    3. Token mag niet verlopen zijn
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, expires_at, used
                FROM password_reset_tokens
                WHERE token = %s
                """,
                (token,)
            )
            row = cur.fetchone()

    if row is None:
        return {'success': False, 'error': 'Ongeldige of verlopen resetlink.'}

    user_id, expires_at, used = row

    # Check: token al gebruikt?
    if used:
        return {'success': False, 'error': 'Deze resetlink is al gebruikt. Vraag een nieuwe aan.'}

    # Check: token verlopen?
    expires_at_aware = expires_at.replace(tzinfo=timezone.utc) if expires_at.tzinfo is None else expires_at
    if datetime.now(timezone.utc) > expires_at_aware:
        return {'success': False, 'error': 'Deze resetlink is verlopen. Vraag een nieuwe aan.'}

    # Alles ok — sla het nieuwe gehashte wachtwoord op
    new_hash = generate_password_hash(new_password)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_hash, user_id)
            )
            # Markeer de token als gebruikt zodat hij nooit hergebruikt kan worden
            cur.execute(
                "UPDATE password_reset_tokens SET used = TRUE WHERE token = %s",
                (token,)
            )
            conn.commit()

    return {'success': True}