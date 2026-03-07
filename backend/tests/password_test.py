import secrets
from datetime import datetime, timezone, timedelta

# Importeer direct de database en modellen uit je backend
from db import db, User, PasswordResetToken

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_user(client):
    """Registreer een testgebruiker en geef het e-mailadres + wachtwoord terug."""
    # Aangepast naar de verplichte velden uit app.py
    payload = {
        "first_name": "jan",
        "last_name": "jansen",
        "email": "jan@example.com",
        "date_of_birth": "1995-01-01",
        "password": "oudwachtwoord123"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201, res.get_json()
    return payload["email"], payload["password"]


def get_reset_token(client, email: str) -> str:
    """Haal de meest recente reset-token rechtstreeks uit de database via ORM."""
    with client.application.app_context():
        user = User.query.filter_by(email=email).first()
        assert user is not None, "Gebruiker niet gevonden in database"
        
        token_record = (
            PasswordResetToken.query
            .filter_by(user_id=user.id)
            .order_by(PasswordResetToken.created_at.desc())
            .first()
        )
        assert token_record is not None, "Geen reset-token gevonden in de database"
        return token_record.token


def expire_token(client, token: str):
    """Zet de vervaldatum van een token naar het verleden (simuleer verlopen token)."""
    with client.application.app_context():
        token_record = PasswordResetToken.query.filter_by(token=token).first()
        assert token_record is not None, "Te verlopen token niet gevonden"
        
        # Omdat cexpires_at een DATE is, trekken we er 1 dag af om zeker te zijn in het verleden
        token_record.cexpires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.session.commit()


# ---------------------------------------------------------------------------
# Stap 1: forgot-password endpoint
# ---------------------------------------------------------------------------

def test_forgot_password_known_email(client, clean_users_db):
    """Bekende e-mail → altijd 200 + neutrale boodschap."""
    register_user(client)
    res = client.post("/api/auth/forgot-password", json={"email": "jan@example.com"})
    assert res.status_code == 200, res.get_json()
    assert "message" in res.get_json()


def test_forgot_password_unknown_email(client, clean_users_db):
    """Onbekende e-mail → ook 200 (user enumeration voorkomen)."""
    res = client.post("/api/auth/forgot-password", json={"email": "bestaat.niet@example.com"})
    assert res.status_code == 200, res.get_json()
    assert "message" in res.get_json()


def test_forgot_password_missing_email(client, clean_users_db):
    """Geen e-mail meegeven → 400."""
    res = client.post("/api/auth/forgot-password", json={})
    assert res.status_code == 400, res.get_json()
    assert "error" in res.get_json()


def test_forgot_password_creates_token(client, clean_users_db):
    """Na een aanvraag moet er een token in de database staan."""
    register_user(client)
    client.post("/api/auth/forgot-password", json={"email": "jan@example.com"})
    token = get_reset_token(client, "jan@example.com")
    assert token is not None


# ---------------------------------------------------------------------------
# Stap 2: reset-password endpoint
# ---------------------------------------------------------------------------

def test_reset_password_success(client, clean_users_db):
    """Geldig token + nieuw wachtwoord → 200 en inloggen met nieuw wachtwoord werkt."""
    email, _ = register_user(client)
    client.post("/api/auth/forgot-password", json={"email": email})
    token = get_reset_token(client, email)

    res = client.post("/api/auth/reset-password", json={
        "token": token,
        "new_password": "nieuwwachtwoord123"
    })

    assert res.status_code == 200, res.get_json()
    assert "message" in res.get_json()

    # Controleer of inloggen met het nieuwe wachtwoord werkt
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": "nieuwwachtwoord123"
    })
    assert login_res.status_code == 200, login_res.get_json()


def test_reset_password_old_password_no_longer_works(client, clean_users_db):
    """Na reset mag het oude wachtwoord niet meer werken."""
    email, old_password = register_user(client)
    client.post("/api/auth/forgot-password", json={"email": email})
    token = get_reset_token(client, email)

    client.post("/api/auth/reset-password", json={
        "token": token,
        "new_password": "nieuwwachtwoord123"
    })

    login_res = client.post("/api/auth/login", json={"email": email, "password": old_password})
    assert login_res.status_code == 401, login_res.get_json()


def test_reset_password_token_can_only_be_used_once(client, clean_users_db):
    """Hetzelfde token een tweede keer gebruiken → 400."""
    email, _ = register_user(client)
    client.post("/api/auth/forgot-password", json={"email": email})
    token = get_reset_token(client, email)

    client.post("/api/auth/reset-password", json={"token": token, "new_password": "nieuwwachtwoord123"})

    res2 = client.post("/api/auth/reset-password", json={"token": token, "new_password": "noganders456"})
    assert res2.status_code == 400, res2.get_json()
    assert "error" in res2.get_json()


def test_reset_password_invalid_token(client, clean_users_db):
    """Ongeldig / verzonnen token → 400."""
    res = client.post("/api/auth/reset-password", json={
        "token": "ditisgeengeldigetoken",
        "new_password": "wachtwoord123"
    })
    assert res.status_code == 400, res.get_json()
    assert "error" in res.get_json()


def test_reset_password_expired_token(client, clean_users_db):
    """Verlopen token → 400."""
    email, _ = register_user(client)
    client.post("/api/auth/forgot-password", json={"email": email})
    token = get_reset_token(client, email)

    expire_token(client, token)

    res = client.post("/api/auth/reset-password", json={"token": token, "new_password": "wachtwoord123"})
    assert res.status_code == 400, res.get_json()
    assert "error" in res.get_json()


def test_reset_password_too_short(client, clean_users_db):
    """Nieuw wachtwoord korter dan 8 tekens → 400."""
    email, _ = register_user(client)
    client.post("/api/auth/forgot-password", json={"email": email})
    token = get_reset_token(client, email)

    res = client.post("/api/auth/reset-password", json={"token": token, "new_password": "kort"})
    assert res.status_code == 400, res.get_json()
    assert "error" in res.get_json()


def test_reset_password_missing_fields(client, clean_users_db):
    """Token of new_password ontbreekt → 400."""
    res = client.post("/api/auth/reset-password", json={"token": "abc123"})
    assert res.status_code == 400, res.get_json()
    assert "error" in res.get_json()

    res2 = client.post("/api/auth/reset-password", json={"new_password": "wachtwoord123"})
    assert res2.status_code == 400, res2.get_json()
    assert "error" in res2.get_json()


def test_forgot_password_overwrites_old_token(client, clean_users_db):
    """Twee aanvragen achter elkaar → alleen de laatste token is geldig."""
    email, _ = register_user(client)

    client.post("/api/auth/forgot-password", json={"email": email})
    first_token = get_reset_token(client, email)

    client.post("/api/auth/forgot-password", json={"email": email})
    second_token = get_reset_token(client, email)

    assert first_token != second_token

    # Eerste token mag niet meer werken (verwijderd door de tweede aanvraag in je auth code)
    res = client.post("/api/auth/reset-password", json={"token": first_token, "new_password": "wachtwoord123"})
    assert res.status_code == 400, res.get_json()

    # Tweede token moet wél werken
    res2 = client.post("/api/auth/reset-password", json={"token": second_token, "new_password": "wachtwoord123"})
    assert res2.status_code == 200, res2.get_json()