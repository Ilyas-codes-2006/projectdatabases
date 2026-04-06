from sms import MoceanSMSError


ADMIN_USER = {
    "first_name": "Admin",
    "last_name": "Tester",
    "email": "admin.tester@gmail.com",
    "date_of_birth": "1988-01-15",
    "password": "securepass1",
    "is_admin": True,
}

NORMAL_USER = {
    "first_name": "Normal",
    "last_name": "Tester",
    "email": "normal.tester@gmail.com",
    "date_of_birth": "1992-04-20",
    "password": "securepass1",
    "is_admin": False,
}


def register(client, payload):
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201, res.get_json()
    return payload


def auth_header(client, payload):
    res = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert res.status_code == 200, res.get_json()
    return {"Authorization": f"Bearer {res.get_json()['token']}"}


class TestSmsAdminRoute:
    def test_test_sms_success(self, client, clean_users_db, monkeypatch):
        register(client, ADMIN_USER)
        headers = auth_header(client, ADMIN_USER)

        captured = {}

        def fake_send_sms(phone_number, message, sender=None, timeout=10):
            captured["phone_number"] = phone_number
            captured["message"] = message
            captured["sender"] = sender
            captured["timeout"] = timeout
            return {"http_status": 200, "response": {"status": "0", "message": "queued"}}

        monkeypatch.setattr("app.sms_service.send_sms", fake_send_sms)

        res = client.post(
            "/api/admin/test-sms",
            json={"phone_number": "+32470000000", "message": "MatchUp SMS test"},
            headers=headers,
        )

        assert res.status_code == 200, res.get_json()
        data = res.get_json()
        assert data["message"] == "SMS sent successfully"
        assert data["provider_response"]["http_status"] == 200
        assert captured["phone_number"] == "+32470000000"
        assert captured["message"] == "MatchUp SMS test"
        assert captured["sender"] is None

    def test_test_sms_missing_phone_number(self, client, clean_users_db):
        register(client, ADMIN_USER)
        headers = auth_header(client, ADMIN_USER)

        res = client.post(
            "/api/admin/test-sms",
            json={"message": "MatchUp SMS test"},
            headers=headers,
        )

        assert res.status_code == 400
        assert res.get_json()["error"] == "phone_number is required"

    def test_test_sms_missing_message(self, client, clean_users_db):
        register(client, ADMIN_USER)
        headers = auth_header(client, ADMIN_USER)

        res = client.post(
            "/api/admin/test-sms",
            json={"phone_number": "+32470000000"},
            headers=headers,
        )

        assert res.status_code == 400
        assert res.get_json()["error"] == "message is required"

    def test_test_sms_requires_authentication(self, client, clean_users_db):
        res = client.post(
            "/api/admin/test-sms",
            json={"phone_number": "+32470000000", "message": "MatchUp SMS test"},
        )

        assert res.status_code == 401

    def test_test_sms_requires_admin(self, client, clean_users_db):
        register(client, NORMAL_USER)
        headers = auth_header(client, NORMAL_USER)

        res = client.post(
            "/api/admin/test-sms",
            json={"phone_number": "+32470000000", "message": "MatchUp SMS test"},
            headers=headers,
        )

        assert res.status_code == 403
        assert res.get_json()["error"] == "Admin privileges required"

    def test_test_sms_provider_failure_returns_502(self, client, clean_users_db, monkeypatch):
        register(client, ADMIN_USER)
        headers = auth_header(client, ADMIN_USER)

        def fake_send_sms(*args, **kwargs):
            raise MoceanSMSError("Mocean is unavailable")

        monkeypatch.setattr("app.sms_service.send_sms", fake_send_sms)

        res = client.post(
            "/api/admin/test-sms",
            json={"phone_number": "+32470000000", "message": "MatchUp SMS test"},
            headers=headers,
        )

        assert res.status_code == 502
        assert "Mocean is unavailable" in res.get_json()["error"]


