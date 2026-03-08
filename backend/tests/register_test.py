def test_register_success(client, clean_users_db):
    payload = {
        "first_name": "john",
        "last_name": "doe",
        "email": "john@example.com",
        "date_of_birth": "2000-05-15",
        "bio": "Ik speel graag tennis",
        "is_admin": False,
        "password": "secret123",
    }

    res = client.post("/api/auth/register", json=payload)

    assert res.status_code == 201, res.get_json()
    data = res.get_json()
    assert data["message"] == "User registered successfully"


def test_register_missing_fields(client, clean_users_db):
    payload = {
        "first_name": "john",
        "last_name": "Doe",
        # email ontbreekt
        "date_of_birth": "2000-05-15",
        "bio": "Ik speel graag tennis",
        "is_admin": False,
        "password": "secret123",
    }

    res = client.post("/api/auth/register", json=payload)

    assert res.status_code == 400, res.get_json()
    data = res.get_json()
    assert data["error"] == "Missing field: email"


def test_register_duplicate_email(client, clean_users_db):
    payload = {
        "first_name": "john",
        "last_name": "doe",
        "email": "john@example.com",
        "date_of_birth": "2000-05-15",
        "bio": "Ik speel graag tennis",
        "is_admin": False,
        "password": "secret123",
    }

    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201, res.get_json()

    # Tweede registratie met hetzelfde e-mail moet mislukken
    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400, res2.get_json()
    data = res2.get_json()
    assert data["error"] == "Email already registered"


def test_register_invalid_json(client, clean_users_db):
    res = client.post("/api/auth/register", data="not a json", content_type="application/json")
    assert res.status_code == 400, res.get_json()
    data = res.get_json()
    assert "error" in data