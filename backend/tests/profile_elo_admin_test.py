"""
profile_elo_admin_test.py — Tests for profile GET/PUT, ELO calculation,
and admin endpoints.
"""

import pytest
from datetime import date
from werkzeug.security import generate_password_hash
from db import (
    db, User, Club, Member, Sport, Ladder, Team, TeamMember,
    Match, Score, apply_match_result,
)
from elo import calculate_elo_simple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_and_login(client, email="user.one@gmail.com", password="pass1234",
                        first="Test", last="User", dob="1990-01-01"):
    client.post("/api/auth/register", json={
        "first_name": first, "last_name": last,
        "email": email, "date_of_birth": dob, "password": password,
    })
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.get_json()
    return {"Authorization": f"Bearer {res.get_json()['token']}"}


def make_club():
    c = Club(name="ProClub", city="Brussels", created_at=date.today())
    db.session.add(c)
    db.session.flush()
    return c


def make_sport():
    s = Sport(name="Padel", team_size=2)
    db.session.add(s)
    db.session.flush()
    return s


def make_ladder(sport_id, club_id=None):
    l = Ladder(
        sport_id=sport_id, club_id=club_id, name="Ladder",
        start_date=date(2024, 1, 1), end_date=date(2024, 12, 31),
    )
    db.session.add(l)
    db.session.flush()
    return l


def make_member(user_id, club_id, is_admin=False, elo=1000):
    m = Member(user_id=user_id, club_id=club_id, joined_at=date.today(),
               is_admin=is_admin, elo=elo)
    db.session.add(m)
    db.session.flush()
    return m


def make_team(ladder_id, name="Team"):
    t = Team(ladder_id=ladder_id, name=name, created_at=date.today())
    db.session.add(t)
    db.session.flush()
    return t


def make_team_member(team_id, member_id):
    tm = TeamMember(team_id=team_id, member_id=member_id)
    db.session.add(tm)
    db.session.flush()
    return tm


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        Score.query.delete()
        Match.query.delete()
        TeamMember.query.delete()
        Team.query.delete()
        Ladder.query.delete()
        Sport.query.delete()
        Member.query.delete()
        Club.query.delete()
        from db import PasswordResetToken, Request, JoinRequest, ClubRequest
        JoinRequest.query.delete()
        ClubRequest.query.delete()
        Request.query.delete()
        PasswordResetToken.query.delete()
        User.query.delete()
        db.session.commit()
    yield
    with app.app_context():
        Score.query.delete()
        Match.query.delete()
        TeamMember.query.delete()
        Team.query.delete()
        Ladder.query.delete()
        Sport.query.delete()
        Member.query.delete()
        Club.query.delete()
        from db import PasswordResetToken, Request, JoinRequest, ClubRequest
        JoinRequest.query.delete()
        ClubRequest.query.delete()
        Request.query.delete()
        PasswordResetToken.query.delete()
        User.query.delete()
        db.session.commit()


# ===========================================================================
# GET /api/profile
# ===========================================================================

class TestGetProfile:
    def test_get_profile_success(self, client):
        headers = register_and_login(client, "prof.jane@gmail.com", first="Jane", last="Doe")
        res = client.get("/api/profile", headers=headers)
        assert res.status_code == 200
        data = res.get_json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Doe"
        assert data["email"] == "prof.jane@gmail.com"
        assert "bio" in data
        assert "photo_url" in data
        assert "date_of_birth" in data

    def test_get_profile_unauthenticated(self, client):
        res = client.get("/api/profile")
        assert res.status_code == 401

    def test_get_profile_bio_defaults_to_empty_string(self, client):
        headers = register_and_login(client, "bio.default@gmail.com")
        res = client.get("/api/profile", headers=headers)
        assert res.get_json()["bio"] == ""

    def test_get_profile_photo_url_defaults_to_empty(self, client):
        headers = register_and_login(client, "photo.default@gmail.com")
        res = client.get("/api/profile", headers=headers)
        assert res.get_json()["photo_url"] == ""

    def test_get_profile_contains_id(self, client):
        headers = register_and_login(client, "idcheck.user@gmail.com")
        res = client.get("/api/profile", headers=headers)
        assert "id" in res.get_json()


# ===========================================================================
# PUT /api/profile
# ===========================================================================

class TestUpdateProfile:
    def test_update_bio(self, client):
        headers = register_and_login(client, "updbio.user@gmail.com")
        res = client.put("/api/profile", json={"bio": "I love tennis!"}, headers=headers)
        assert res.status_code == 200
        assert client.get("/api/profile", headers=headers).get_json()["bio"] == "I love tennis!"

    def test_update_photo_url(self, client):
        headers = register_and_login(client, "updphoto.user@gmail.com")
        url = "https://example.com/photo.jpg"
        res = client.put("/api/profile", json={"photo_url": url}, headers=headers)
        assert res.status_code == 200
        assert client.get("/api/profile", headers=headers).get_json()["photo_url"] == url

    def test_update_both_bio_and_photo(self, client):
        headers = register_and_login(client, "updboth.user@gmail.com")
        res = client.put("/api/profile", json={
            "bio": "Padel fanatic",
            "photo_url": "https://cdn.example.com/me.jpg",
        }, headers=headers)
        assert res.status_code == 200
        data = client.get("/api/profile", headers=headers).get_json()
        assert data["bio"] == "Padel fanatic"
        assert data["photo_url"] == "https://cdn.example.com/me.jpg"

    def test_update_profile_empty_body_returns_400(self, client):
        """The backend checks `if not data` which is True for {}, so it returns 400."""
        headers = register_and_login(client, "emptyupd.user@gmail.com")
        res = client.put("/api/profile", json={}, headers=headers)
        assert res.status_code == 400

    def test_update_profile_unauthenticated(self, client):
        res = client.put("/api/profile", json={"bio": "nope"})
        assert res.status_code == 401

    def test_update_bio_empty_string(self, client):
        headers = register_and_login(client, "bioempty.user@gmail.com")
        client.put("/api/profile", json={"bio": "Something"}, headers=headers)
        res = client.put("/api/profile", json={"bio": ""}, headers=headers)
        assert res.status_code == 200
        assert client.get("/api/profile", headers=headers).get_json()["bio"] == ""

    def test_profile_update_does_not_change_name_or_email(self, client):
        headers = register_and_login(client, "stable.name@gmail.com", first="Stable", last="Name")
        client.put("/api/profile", json={"bio": "Changed"}, headers=headers)
        data = client.get("/api/profile", headers=headers).get_json()
        assert data["first_name"] == "Stable"
        assert data["last_name"] == "Name"
        assert data["email"] == "stable.name@gmail.com"


# ===========================================================================
# ELO — unit tests for calculate_elo_simple
# ===========================================================================

class TestCalculateEloSimple:
    def test_winner_gains_25(self):
        new_w, new_l = calculate_elo_simple(1000, 1000)
        assert new_w == 1025

    def test_loser_loses_25(self):
        new_w, new_l = calculate_elo_simple(1000, 1000)
        assert new_l == 975

    def test_winner_always_gains(self):
        for w, l in [(500, 2000), (1000, 1000), (2000, 500)]:
            new_w, _ = calculate_elo_simple(w, l)
            assert new_w > w

    def test_loser_always_loses(self):
        for w, l in [(500, 2000), (1000, 1000), (2000, 500)]:
            _, new_l = calculate_elo_simple(w, l)
            assert new_l < l

    def test_elo_change_is_symmetric(self):
        w, l = 1200, 800
        new_w, new_l = calculate_elo_simple(w, l)
        assert (new_w - w) == (l - new_l)

    def test_zero_elo_winner(self):
        new_w, _ = calculate_elo_simple(0, 1000)
        assert new_w > 0

    def test_very_high_elo_values(self):
        new_w, new_l = calculate_elo_simple(3000, 2500)
        assert new_w > 3000
        assert new_l < 2500


# ===========================================================================
# apply_match_result — integration
# ===========================================================================

class TestApplyMatchResult:
    def _setup_match(self, app):
        with app.app_context():
            u1 = User(first_name="A", last_name="B", email="mr1.player@gmail.com",
                      password="x", date_of_birth=date(1990, 1, 1), created_at=date.today())
            u2 = User(first_name="C", last_name="D", email="mr2.player@gmail.com",
                      password="x", date_of_birth=date(1990, 1, 1), created_at=date.today())
            db.session.add_all([u1, u2])
            db.session.flush()
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            t1 = make_team(ladder.id, "T1")
            t2 = make_team(ladder.id, "T2")
            m1 = make_member(u1.id, club.id, elo=1000)
            m2 = make_member(u2.id, club.id, elo=1000)
            make_team_member(t1.id, m1.id)
            make_team_member(t2.id, m2.id)
            match = Match(date=date.today(), home_team_id=t1.id, away_team_id=t2.id)
            db.session.add(match)
            db.session.commit()
            return match.id, m1.id, m2.id

    def test_winner_elo_increases(self, app):
        match_id, m1_id, _ = self._setup_match(app)
        with app.app_context():
            score = Score(match_id=match_id, set=1, home_score=6, away_score=0)
            db.session.add(score)
            db.session.commit()
            apply_match_result(match_id)
            assert db.session.get(Member, m1_id).elo > 1000

    def test_loser_elo_decreases(self, app):
        match_id, _, m2_id = self._setup_match(app)
        with app.app_context():
            score = Score(match_id=match_id, set=1, home_score=6, away_score=0)
            db.session.add(score)
            db.session.commit()
            apply_match_result(match_id)
            assert db.session.get(Member, m2_id).elo < 1000

    def test_away_team_wins(self, app):
        match_id, m1_id, m2_id = self._setup_match(app)
        with app.app_context():
            score = Score(match_id=match_id, set=1, home_score=0, away_score=6)
            db.session.add(score)
            db.session.commit()
            apply_match_result(match_id)
            assert db.session.get(Member, m2_id).elo > 1000
            assert db.session.get(Member, m1_id).elo < 1000

    def test_no_score_no_change(self, app):
        match_id, m1_id, m2_id = self._setup_match(app)
        with app.app_context():
            apply_match_result(match_id)
            assert db.session.get(Member, m1_id).elo == 1000
            assert db.session.get(Member, m2_id).elo == 1000

    def test_invalid_match_id_no_crash(self, app):
        with app.app_context():
            apply_match_result(99999)


# ===========================================================================
# Admin — user management
# ===========================================================================

class TestAdminUsers:
    def _make_admin(self, app, email="admin.superuser@gmail.com", password="adminpass99"):
        with app.app_context():
            admin = User(
                first_name="Admin", last_name="Super", email=email,
                password=generate_password_hash(password),
                date_of_birth=date(1980, 1, 1), created_at=date.today(), is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()
        return email, password

    def _admin_headers(self, client, app):
        email, password = self._make_admin(app)
        res = client.post("/api/auth/login", json={"email": email, "password": password})
        assert res.status_code == 200, res.get_json()
        return {"Authorization": f"Bearer {res.get_json()['token']}"}

    def test_list_users_requires_admin(self, client):
        headers = register_and_login(client, "norma.user@gmail.com")
        res = client.get("/api/admin/users", headers=headers)
        assert res.status_code == 403

    def test_list_users_unauthenticated(self, client):
        res = client.get("/api/admin/users")
        assert res.status_code == 401

    def test_list_users_success(self, client, app):
        headers = self._admin_headers(client, app)
        register_and_login(client, "listme.user@gmail.com")
        res = client.get("/api/admin/users", headers=headers)
        assert res.status_code == 200
        emails = [u["email"] for u in res.get_json()]
        assert "listme.user@gmail.com" in emails

    def test_delete_user_success(self, client, app):
        headers = self._admin_headers(client, app)
        reg_headers = register_and_login(client, "todelete.user@gmail.com")
        profile = client.get("/api/profile", headers=reg_headers).get_json()
        user_id = profile["id"]

        res = client.delete(f"/api/admin/users/{user_id}", headers=headers)
        assert res.status_code == 200

        users = client.get("/api/admin/users", headers=headers).get_json()
        assert all(u["email"] != "todelete.user@gmail.com" for u in users)

    def test_delete_user_not_found(self, client, app):
        headers = self._admin_headers(client, app)
        res = client.delete("/api/admin/users/99999", headers=headers)
        assert res.status_code == 404

    def test_admin_cannot_self_delete(self, client, app):
        headers = self._admin_headers(client, app)
        admin_profile = client.get("/api/profile", headers=headers).get_json()
        admin_id = admin_profile["id"]
        res = client.delete(f"/api/admin/users/{admin_id}", headers=headers)
        assert res.status_code == 400

    def test_delete_user_requires_admin(self, client):
        headers = register_and_login(client, "delnonadm.user@gmail.com")
        res = client.delete("/api/admin/users/1", headers=headers)
        assert res.status_code == 403

    def test_list_clubs_admin_only(self, client, app):
        headers = self._admin_headers(client, app)
        res = client.get("/api/admin/clubs", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.get_json(), list)

    def test_list_clubs_requires_admin(self, client):
        headers = register_and_login(client, "norma2.user@gmail.com")
        res = client.get("/api/admin/clubs", headers=headers)
        assert res.status_code == 403

    def test_list_teams_admin_only(self, client, app):
        headers = self._admin_headers(client, app)
        res = client.get("/api/admin/teams", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.get_json(), list)

    def test_update_user_club_to_valid_club(self, client, app):
        headers = self._admin_headers(client, app)
        with app.app_context():
            club = make_club()
            db.session.commit()
            club_id = club.id

        reg_headers = register_and_login(client, "assignclub.user@gmail.com")
        profile = client.get("/api/profile", headers=reg_headers).get_json()
        user_id = profile["id"]

        res = client.put(
            f"/api/admin/users/{user_id}/club",
            json={"club_id": club_id}, headers=headers,
        )
        assert res.status_code == 200

    def test_update_user_club_nonexistent_club(self, client, app):
        headers = self._admin_headers(client, app)
        reg_headers = register_and_login(client, "badclub.user@gmail.com")
        profile = client.get("/api/profile", headers=reg_headers).get_json()
        user_id = profile["id"]

        res = client.put(
            f"/api/admin/users/{user_id}/club",
            json={"club_id": 99999}, headers=headers,
        )
        assert res.status_code == 404

    def test_update_user_club_null_fails_db_constraint(self, client, app):
        """club_id=null with no existing member row causes 500 (NOT NULL violation)."""
        headers = self._admin_headers(client, app)
        reg_headers = register_and_login(client, "clubnull.user@gmail.com")
        profile = client.get("/api/profile", headers=reg_headers).get_json()
        user_id = profile["id"]

        res = client.put(
            f"/api/admin/users/{user_id}/club",
            json={"club_id": None}, headers=headers,
        )
        assert res.status_code == 500

    def test_update_user_team_to_valid_team(self, client, app):
        headers = self._admin_headers(client, app)
        with app.app_context():
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            team = make_team(ladder.id, "AdminTeam")
            db.session.commit()
            team_id = team.id
            club_id = club.id

        reg_headers = register_and_login(client, "assignteam.user@gmail.com")
        profile = client.get("/api/profile", headers=reg_headers).get_json()
        user_id = profile["id"]

        # Assign club first so the member row has a valid club_id
        client.put(f"/api/admin/users/{user_id}/club",
                   json={"club_id": club_id}, headers=headers)

        res = client.put(
            f"/api/admin/users/{user_id}/team",
            json={"team_id": team_id}, headers=headers,
        )
        assert res.status_code == 200

    def test_update_user_team_nonexistent(self, client, app):
        headers = self._admin_headers(client, app)
        reg_headers = register_and_login(client, "badteam.user@gmail.com")
        profile = client.get("/api/profile", headers=reg_headers).get_json()
        user_id = profile["id"]

        res = client.put(
            f"/api/admin/users/{user_id}/team",
            json={"team_id": 99999}, headers=headers,
        )
        assert res.status_code == 404

    def test_update_user_team_null_no_member_row_returns_200(self, client, app):
        """
        Sending team_id=null for a user with no member row is a no-op and
        returns 200 (nothing to remove).
        """
        headers = self._admin_headers(client, app)
        reg_headers = register_and_login(client, "teamnull.user@gmail.com")
        profile = client.get("/api/profile", headers=reg_headers).get_json()
        user_id = profile["id"]

        res = client.put(
            f"/api/admin/users/{user_id}/team",
            json={"team_id": None}, headers=headers,
        )
        assert res.status_code == 200

    def test_update_user_team_set_team_without_club_returns_400(self, client, app):
        """
        Assigning a team to a user who has no member row (no club) returns 400 —
        admin must assign a club first.
        """
        headers = self._admin_headers(client, app)
        with app.app_context():
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            team = make_team(ladder.id, "SomeTeam")
            db.session.commit()
            team_id = team.id

        reg_headers = register_and_login(client, "teamnoclub.user@gmail.com")
        profile = client.get("/api/profile", headers=reg_headers).get_json()
        user_id = profile["id"]

        res = client.put(
            f"/api/admin/users/{user_id}/team",
            json={"team_id": team_id}, headers=headers,
        )
        assert res.status_code == 400

    def test_get_user_details_admin(self, client, app):
        headers = self._admin_headers(client, app)
        reg_headers = register_and_login(client, "details.user@gmail.com")
        profile = client.get("/api/profile", headers=reg_headers).get_json()
        user_id = profile["id"]

        res = client.get(f"/api/admin/users/{user_id}/details", headers=headers)
        assert res.status_code == 200
        data = res.get_json()
        assert "club_id" in data
        assert "team_id" in data

    def test_get_user_details_not_found(self, client, app):
        headers = self._admin_headers(client, app)
        res = client.get("/api/admin/users/99999/details", headers=headers)
        assert res.status_code == 404


# ===========================================================================
# GET /api/profile/club-status
# ===========================================================================

class TestClubStatus:
    def test_club_status_not_club_admin(self, client):
        headers = register_and_login(client, "nostatus.user@gmail.com")
        res = client.get("/api/profile/club-status", headers=headers)
        assert res.status_code == 200
        data = res.get_json()
        assert data["is_club_admin"] is False
        assert data["club_id"] is None
        assert data["club_name"] is None

    def test_club_status_is_club_admin(self, client, app):
        headers = register_and_login(client, "clubstatus.user@gmail.com")
        profile = client.get("/api/profile", headers=headers).get_json()
        user_id = profile["id"]

        with app.app_context():
            club = make_club()
            make_member(user_id, club.id, is_admin=True)
            db.session.commit()
            club_id = club.id
            club_name = club.name

        res = client.get("/api/profile/club-status", headers=headers)
        assert res.status_code == 200
        data = res.get_json()
        assert data["is_club_admin"] is True
        assert data["club_id"] == club_id
        assert data["club_name"] == club_name

    def test_club_status_requires_auth(self, client):
        res = client.get("/api/profile/club-status")
        assert res.status_code == 401

    def test_club_status_regular_member_not_admin(self, client, app):
        headers = register_and_login(client, "regmember.user@gmail.com")
        profile = client.get("/api/profile", headers=headers).get_json()
        user_id = profile["id"]

        with app.app_context():
            club = make_club()
            make_member(user_id, club.id, is_admin=False)
            db.session.commit()

        res = client.get("/api/profile/club-status", headers=headers)
        assert res.get_json()["is_club_admin"] is False