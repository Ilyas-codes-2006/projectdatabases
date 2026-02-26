import hashlib
from datetime import datetime, timedelta
from config import config_data as config
from db import get_conn
import psycopg
from werkzeug.security import generate_password_hash, check_password_hash


def register_user(first_name, last_name, email, age, sport, skill_level, club, password):
    #Register a new user with hashed password.
    password_hash = generate_password_hash(password)
    #Insert user into database (not implemented here)

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
                id = cur.fetchone()[0]
                conn.commit()
                return {'success': True, 'user_id': id}
            except psycopg.errors.UniqueViolation:
                return {'success': False, 'error': 'Email already registered'}
            except Exception as e:
                return {'success': False, 'error': str(e)}