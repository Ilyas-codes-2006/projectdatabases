import hashlib
from datetime import datetime, timedelta
from config import config_data as config
from db import get_conn
import psycopg

def hash_password(password: str) -> str:
    #Hash a password using SHA-256.
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    #Verify a password against its hash.
    return hash_password(password) == password_hash

def register_user(first_name, last_name, email, age, sport, skill_level, club, password):
    #Register a new user with hashed password.
    password_hash = hash_password(password)
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