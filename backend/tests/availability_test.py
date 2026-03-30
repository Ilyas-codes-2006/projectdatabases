import pytest
from datetime import date
from db import db, User, Club, Member, Availability

# help functions

BASE_USER = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@gmail.com",
    "date_of_birth": "1995-10-10",
    "password": "securepass1",
}

def register(client, payload=None):
    payload = payload or BASE_USER
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    return payload

def login(client, email=None, password=None):
    email = email or BASE_USER["email"]
    password = password or BASE_USER["password"]
    return client.post("/api/auth/login", json={"email": email, "password": password})

def auth_header(client, email=None, password=None):
    res = login(client, email, password)
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.get_json()['token']}"}

def setup_club_for_user(app, email=BASE_USER["email"]):
    with app.app_context():
        user = User.query.filter_by(email=email).first()

        club = Club(name="Test Tennis Club", city="Antwerpen")
        db.session.add(club)
        db.session.flush()

        member = Member(user_id=user.id, club_id=club.id)
        db.session.add(member)
        db.session.commit()

        return user.id, club.id

class TestAvailability:
    def test_get_availability_unauthenticated(self, client):
        res = client.get("/api/availability")
        assert res.status_code == 401

    def test_get_availability_no_club(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)

        res = client.get("/api/availability", headers=headers)
        assert res.status_code == 200
        assert res.get_json()["dates"] == []

    def test_post_availability_unauthenticated(self, client):
        res = client.post("/api/availability", json={"dates": ["2026-03-15"]})
        assert res.status_code == 401

    def test_post_availability_no_dates_field(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)

        res = client.post("/api/availability", json={}, headers=headers)
        assert res.status_code == 400
        assert "No dates selected" in res.get_json()["error"]

    def test_post_availability_no_club(self, client, clean_users_db):
        register(client)
        headers = auth_header(client)

        res = client.post("/api/availability", json={"dates": ["2026-03-15"]}, headers=headers)
        assert res.status_code == 400
        assert "not joined a club yet" in res.get_json()["error"]

    def test_post_availability_success(self, client, app, clean_users_db):
        register(client)
        setup_club_for_user(app)
        headers = auth_header(client)

        res = client.post("/api/availability", json={"dates": ["2026-03-15", "2026-03-16"]}, headers=headers)
        assert res.status_code == 200
        assert "Succes!" in res.get_json()["message"]

        res_get = client.get("/api/availability", headers=headers)
        assert res_get.status_code == 200

        dates = res_get.get_json()["dates"]
        assert "2026-03-15" in dates
        assert "2026-03-16" in dates
        assert len(dates) == 2

    def test_post_availability_invalid_dates_ignored(self, client, app, clean_users_db):
        register(client)
        setup_club_for_user(app)
        headers = auth_header(client)

        res = client.post("/api/availability", json={"dates": ["2026-03-15", "niet-een-datum"]}, headers=headers)
        assert res.status_code == 200

        res_get = client.get("/api/availability", headers=headers)
        dates = res_get.get_json()["dates"]
        assert "2026-03-15" in dates
        assert "niet-een-datum" not in dates
        assert len(dates) == 1

    def test_post_availability_update_add_and_remove(self, client, app, clean_users_db):
        register(client)
        setup_club_for_user(app)
        headers = auth_header(client)

        client.post("/api/availability", json={"dates": ["2026-03-10", "2026-03-11"]}, headers=headers)

        res = client.post("/api/availability", json={"dates": ["2026-03-10", "2026-03-12"]}, headers=headers)
        assert res.status_code == 200

        res_get = client.get("/api/availability", headers=headers)
        dates = res_get.get_json()["dates"]

        assert "2026-03-10" in dates
        assert "2026-03-12" in dates
        assert "2026-03-11" not in dates
        assert len(dates) == 2
