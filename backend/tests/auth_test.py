"""
auth_test.py — Tests for authentication and profile-change endpoints.

NOTE: email_validator (used by the app) rejects domains like @example.com and
@test.com as undeliverable. All test emails use real-looking domains such as
@gmail.com or @mail.com.
"""

import pytest
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_USER = {
    "first_name": "Alice",
    "last_name": "Wonder",
    "email": "alice.wonder@gmail.com",
    "date_of_birth": "1990-06-15",
    "password": "securepass1",
}


def register(client, payload=None):
    payload = payload or BASE_USER
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201, res.get_json()
    return payload


def login(client, email=None, password=None):
    email = email or BASE_USER["email"]
    password = password or BASE_USER["password"]
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth_header(client, email=None, password=None):
    res = login(client, email, password)
    assert res.status_code == 200, res.get_json()
    return {"Authorization": f"Bearer {res.get_json()['token']}"}


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success(self, client, clean_users_db):
        register(client)
        res = login(client)
        assert res.status_code == 200
        data = res.get_json()
        assert "token" in data
        assert data["name"] == "Alice Wonder"
        assert data["is_admin"] is False

    def test_login_wrong_password(self, client, clean_users_db):
        register(client)
        res = login(client, password="wrongpassword")
        assert res.status_code == 401
        assert "error" in res.get_json()

    def test_login_unknown_email(self, client, clean_users_db):
        res = login(client, email="nobody@gmail.com", password="somepass")
        assert res.status_code == 401

    def test_login_missing_email(self, client, clean_users_db):
        res = client.post("/api/auth/login", json={"password": "abc"})
        assert res.status_code == 400

    def test_login_missing_password(self, client, clean_users_db):
        res = client.post("/api/auth/login", json={"email": "alice.wonder@gmail.com"})
        assert res.status_code == 400

    def test_login_invalid_email_format(self, client, clean_users_db):
        res = client.post("/api/auth/login", json={"email": "not-an-email", "password": "pass"})
        assert res.status_code == 400

    def test_login_empty_body(self, client, clean_users_db):
        res = client.post("/api/auth/login", json={})
        assert res.status_code == 400

    def test_login_case_insensitive_email(self, client, clean_users_db):
        """Email lookup must be case-insensitive."""
        register(client)
        res = login(client, email="ALICE.WONDER@GMAIL.COM")
        assert res.status_code == 200

    def test_login_returns_user_id(self, client, clean_users_db):
        register(client)
        res = login(client)
        data = res.get_json()
        assert "user_id" in data
        assert isinstance(data["user_id"], int)

    def test_login_admin_flag_false_for_normal_user(self, client, clean_users_db):
        register(client)
        assert login(client).get_json()["is_admin"] is False

    def test_login_no_json_body(self, client, clean_users_db):
        res = client.post("/api/auth/login", data="not json", content_type="application/json")
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# CHANGE EMAIL
# ---------------------------------------------------------------------------

class TestChangeEmail:
    def test_change_email_success(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-email",
            json={"new_email": "alice.new@gmail.com", "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 200
        assert login(client, email="alice.new@gmail.com").status_code == 200

    def test_change_email_old_email_no_longer_works(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        client.put(
            "/api/profile/change-email",
            json={"new_email": "alice.replaced@gmail.com", "password": BASE_USER["password"]},
            headers=headers,
        )
        assert login(client, email=BASE_USER["email"]).status_code == 401

    def test_change_email_wrong_password(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-email",
            json={"new_email": "alice.new@gmail.com", "password": "wrongpassword"},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_email_duplicate_email(self, client, clean_users_db):
        register(client)
        register(client, dict(BASE_USER, email="bob.smith@gmail.com"))
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-email",
            json={"new_email": "bob.smith@gmail.com", "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_email_invalid_format(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-email",
            json={"new_email": "not-an-email", "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_email_missing_new_email(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-email",
            json={"password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_email_missing_password(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-email",
            json={"new_email": "alice.new@gmail.com"},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_email_unauthenticated(self, client, clean_users_db):
        res = client.put(
            "/api/profile/change-email",
            json={"new_email": "alice.new@gmail.com", "password": "pw"},
        )
        assert res.status_code == 401

    def test_change_email_same_email_as_current(self, client, clean_users_db):
        """Same email is already in use by the user — should be blocked."""
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-email",
            json={"new_email": BASE_USER["email"], "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_email_normalises_to_lowercase(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-email",
            json={"new_email": "Alice.Upper@Gmail.COM", "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 200
        assert login(client, email="alice.upper@gmail.com").status_code == 200


# ---------------------------------------------------------------------------
# CHANGE NAME
# ---------------------------------------------------------------------------

class TestChangeName:
    def test_change_name_success(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-name",
            json={"new_first_name": "Alicia", "new_last_name": "Wonderland",
                  "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 200

    def test_change_name_wrong_password(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-name",
            json={"new_first_name": "Bob", "new_last_name": "Builder", "password": "wrong"},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_name_same_as_current(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-name",
            json={"new_first_name": BASE_USER["first_name"],
                  "new_last_name": BASE_USER["last_name"],
                  "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_name_same_case_insensitive(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-name",
            json={"new_first_name": "alice", "new_last_name": "wonder",
                  "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_name_missing_first_name(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-name",
            json={"new_last_name": "Doe", "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_name_missing_last_name(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-name",
            json={"new_first_name": "John", "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_name_missing_password(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-name",
            json={"new_first_name": "John", "new_last_name": "Doe"},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_name_unauthenticated(self, client, clean_users_db):
        res = client.put(
            "/api/profile/change-name",
            json={"new_first_name": "X", "new_last_name": "Y", "password": "pw"},
        )
        assert res.status_code == 401

    def test_change_name_only_first_name_differs(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-name",
            json={"new_first_name": "Alicia", "new_last_name": BASE_USER["last_name"],
                  "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 200

    def test_change_name_only_last_name_differs(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-name",
            json={"new_first_name": BASE_USER["first_name"], "new_last_name": "Smith",
                  "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 200


# ---------------------------------------------------------------------------
# CHANGE BIRTHDAY
# ---------------------------------------------------------------------------

class TestChangeBirthday:
    def test_change_birthday_success(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-birthday",
            json={"new_birthday": "1985-03-20", "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 200

    def test_change_birthday_wrong_password(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-birthday",
            json={"new_birthday": "1985-03-20", "password": "wrongpass"},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_birthday_same_as_current(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-birthday",
            json={"new_birthday": BASE_USER["date_of_birth"], "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_birthday_too_young(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        too_young = (date.today() - timedelta(days=365)).isoformat()
        res = client.put(
            "/api/profile/change-birthday",
            json={"new_birthday": too_young, "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_birthday_invalid_date_format(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-birthday",
            json={"new_birthday": "15-03-1990", "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_birthday_missing_birthday_field(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-birthday",
            json={"password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_birthday_missing_password(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        res = client.put(
            "/api/profile/change-birthday",
            json={"new_birthday": "1985-03-20"},
            headers=headers,
        )
        assert res.status_code == 400

    def test_change_birthday_unauthenticated(self, client, clean_users_db):
        res = client.put(
            "/api/profile/change-birthday",
            json={"new_birthday": "1985-03-20", "password": "pw"},
        )
        assert res.status_code == 401

    def test_change_birthday_boundary_exactly_6_years_ago(self, client, clean_users_db):
        """Exactly 6 years ago today should be accepted (different from BASE_USER dob)."""
        register(client)
        headers = auth_header(client)
        today = date.today()
        exactly_6 = date(today.year - 6, today.month, today.day).isoformat()
        res = client.put(
            "/api/profile/change-birthday",
            json={"new_birthday": exactly_6, "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 200

    def test_change_birthday_future_date(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)
        future = (date.today() + timedelta(days=10)).isoformat()
        res = client.put(
            "/api/profile/change-birthday",
            json={"new_birthday": future, "password": BASE_USER["password"]},
            headers=headers,
        )
        assert res.status_code == 400