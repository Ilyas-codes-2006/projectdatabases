"""
notifications_test.py — Tests for the notification endpoints.

  GET  /api/notifications
  PATCH /api/notifications/read

"""

import pytest
from datetime import date
from werkzeug.security import generate_password_hash
from db import db, User, Club, Member, Sport, Ladder, Team, JoinRequest, TeamEvent, TeamMember, Match

pytestmark = pytest.mark.usefixtures("clean_db")


# Helpers

def make_user(email, first="Test", last="User"):
    u = User(
        first_name=first, last_name=last, email=email,
        password=generate_password_hash("password123"),
        date_of_birth=date(1995, 1, 1),
    )
    db.session.add(u)
    db.session.flush()
    return u


def make_club_with_admin(admin_user):
    """Create a club and make admin_user its admin."""
    club = Club(name="TC Test", city="Antwerp", created_at=date.today())
    db.session.add(club)
    db.session.flush()
    db.session.add(Member(
        user_id=admin_user.id, club_id=club.id,
        joined_at=date.today(), is_admin=True, elo=0,
    ))
    db.session.flush()
    return club


def make_team_event(app, target_id, actor_email, read=False):
    """Insert a TeamEvent for target_id in a fresh club/ladder/team."""
    with app.app_context():
        actor = make_user(actor_email, first="Actor", last="User")
        club = Club(name=f"TC {actor_email[:6]}", city="Gent", created_at=date.today())
        db.session.add(club)
        db.session.flush()
        sport = Sport(name="Tennis", team_size=1)
        db.session.add(sport)
        db.session.flush()
        ladder = Ladder(
            sport_id=sport.id, club_id=club.id, name="Ladder",
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        db.session.add(ladder)
        db.session.flush()
        team = Team(ladder_id=ladder.id, name="Team A", created_at=date.today())
        db.session.add(team)
        db.session.flush()
        db.session.add(TeamEvent(
            team_id=team.id, actor_id=actor.id,
            target_id=target_id, action="joined", read=read,
        ))
        db.session.commit()


def register_and_login(client, email, first="Test", last="User"):
    client.post("/api/auth/register", json={
        "first_name": first, "last_name": last,
        "email": email, "date_of_birth": "1995-01-01", "password": "password123",
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert res.status_code == 200, res.get_json()
    return {"Authorization": f"Bearer {res.get_json()['token']}"}


# Fixture

@pytest.fixture()
def clean_db(app):
    _wipe(app)
    yield
    _wipe(app)


def _wipe(app):
    with app.app_context():
        for model in (TeamEvent, JoinRequest, Member, Team, Ladder, Sport, Club, User, Match, TeamMember):
            db.session.query(model).delete()
        db.session.commit()


# GET /api/notifications

def test_get_notifications_requires_auth(client):
    assert client.get("/api/notifications").status_code == 401


def test_get_notifications_empty_for_plain_user(client):
    headers = register_and_login(client, "plain.user@gmail.com")
    res = client.get("/api/notifications", headers=headers)
    assert res.status_code == 200
    assert res.get_json() == []


def test_club_admin_sees_pending_join_request(client, app):
    headers = register_and_login(client, "admin@gmail.com", first="Admin", last="A")

    with app.app_context():
        admin = User.query.filter_by(email="admin@gmail.com").first()
        club = make_club_with_admin(admin)
        requester = make_user("bob@gmail.com", first="Bob", last="Smith")
        db.session.add(JoinRequest(
            user_id=requester.id, club_id=club.id,
            motivation="", status="pending", created_at=date.today(),
        ))
        db.session.commit()

    data = client.get("/api/notifications", headers=headers).get_json()
    assert len(data) == 1
    assert data[0]["type"] == "join_request"
    assert "Bob Smith" in data[0]["message"]


def test_non_pending_join_requests_not_shown(client, app):
    """Approved and rejected join requests must not appear."""
    headers = register_and_login(client, "admin2@gmail.com", first="Admin", last="B")

    with app.app_context():
        admin = User.query.filter_by(email="admin2@gmail.com").first()
        club = make_club_with_admin(admin)
        for status in ("approved", "rejected"):
            u = make_user(f"{status}.user@gmail.com")
            db.session.add(JoinRequest(
                user_id=u.id, club_id=club.id,
                motivation="", status=status, created_at=date.today(),
            ))
        db.session.commit()

    assert client.get("/api/notifications", headers=headers).get_json() == []


def test_unread_team_event_shown(client, app):
    headers = register_and_login(client, "target@gmail.com", first="Target", last="T")

    with app.app_context():
        target_id = User.query.filter_by(email="target@gmail.com").first().id

    make_team_event(app, target_id, "actor@gmail.com")

    data = client.get("/api/notifications", headers=headers).get_json()
    assert len(data) == 1
    assert data[0]["type"] == "team_event"


def test_already_read_team_event_not_shown(client, app):
    headers = register_and_login(client, "target2@gmail.com", first="Target", last="U")

    with app.app_context():
        target_id = User.query.filter_by(email="target2@gmail.com").first().id

    make_team_event(app, target_id, "actor2@gmail.com", read=True)

    assert client.get("/api/notifications", headers=headers).get_json() == []


# PATCH /api/notifications/read

def test_mark_read_requires_auth(client):
    assert client.patch("/api/notifications/read").status_code == 401


def test_mark_read_returns_ok(client):
    headers = register_and_login(client, "reader@gmail.com")
    res = client.patch("/api/notifications/read", headers=headers)
    assert res.status_code == 200
    assert res.get_json().get("ok") is True


def test_mark_read_clears_team_events(client, app):
    headers = register_and_login(client, "clearer@gmail.com", first="Clear", last="C")

    with app.app_context():
        target_id = User.query.filter_by(email="clearer@gmail.com").first().id

    make_team_event(app, target_id, "actor3@gmail.com")

    assert len(client.get("/api/notifications", headers=headers).get_json()) == 1
    client.patch("/api/notifications/read", headers=headers)
    assert client.get("/api/notifications", headers=headers).get_json() == []


def test_mark_read_does_not_clear_join_request_notifications(client, app):
    """PATCH only marks TeamEvents as read; join-request notifications are live queries."""
    headers = register_and_login(client, "admin3@gmail.com", first="Admin", last="C")

    with app.app_context():
        admin = User.query.filter_by(email="admin3@gmail.com").first()
        club = make_club_with_admin(admin)
        requester = make_user("req@gmail.com")
        db.session.add(JoinRequest(
            user_id=requester.id, club_id=club.id,
            motivation="", status="pending", created_at=date.today(),
        ))
        db.session.commit()

    client.patch("/api/notifications/read", headers=headers)

    data = client.get("/api/notifications", headers=headers).get_json()
    assert any(n["type"] == "join_request" for n in data)