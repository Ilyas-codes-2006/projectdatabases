"""
teams_test.py — Tests for team endpoints and underlying team functions.
"""

import pytest
from datetime import date
from db import db, User, Club, Member, Sport, Ladder, Team, TeamMember, Score, Match
from flask import g
from teams import show_teams, create_team, join_team


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email, is_admin=False):
    u = User(
        first_name="T", last_name="U", email=email, password="hashed",
        date_of_birth=date(1995, 1, 1), created_at=date.today(), is_admin=is_admin,
    )
    db.session.add(u)
    db.session.flush()
    return u


def make_club(name="TC Test"):
    c = Club(name=name, city="TestCity", created_at=date.today())
    db.session.add(c)
    db.session.flush()
    return c


def make_sport(name="Tennis"):
    s = Sport(name=name, team_size=2)
    db.session.add(s)
    db.session.flush()
    return s


def make_ladder(sport_id, club_id=None, name="Ladder"):
    l = Ladder(
        sport_id=sport_id, club_id=club_id, name=name,
        start_date=date(2024, 1, 1), end_date=date(2024, 12, 31),
    )
    db.session.add(l)
    db.session.flush()
    return l


def make_member(user_id, club_id):
    m = Member(user_id=user_id, club_id=club_id, joined_at=date.today(), elo=0)
    db.session.add(m)
    db.session.flush()
    return m


def make_team(ladder_id, name="Team Alpha"):
    t = Team(ladder_id=ladder_id, name=name, created_at=date.today())
    db.session.add(t)
    db.session.flush()
    return t


def make_team_member(team_id, member_id):
    tm = TeamMember(team_id=team_id, member_id=member_id)
    db.session.add(tm)
    db.session.flush()
    return tm


def register_and_login(client, email="user.one@gmail.com", password="pass1234",
                        first="Test", last="User", dob="1990-01-01"):
    client.post("/api/auth/register", json={
        "first_name": first, "last_name": last,
        "email": email, "date_of_birth": dob, "password": password,
    })
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.get_json()
    return {"Authorization": f"Bearer {res.get_json()['token']}"}


def api_register_and_login(client, email="player.one@gmail.com", password="pass1234"):
    client.post("/api/auth/register", json={
        "first_name": "Player", "last_name": "One",
        "email": email, "date_of_birth": "1995-01-01", "password": password,
    })
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.get_json()
    return {"Authorization": f"Bearer {res.get_json()['token']}"}


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
        User.query.delete()
        db.session.commit()


# ===========================================================================
# show_teams
# ===========================================================================

class TestShowTeams:
    def test_show_teams_empty(self, app):
        with app.app_context():
            result = show_teams()
        assert result["success"] is True
        assert result["teams"] == []

    def test_show_teams_single_team_no_members(self, app):
        with app.app_context():
            sport = make_sport()
            ladder = make_ladder(sport.id)
            make_team(ladder.id, "Solo Team")
            db.session.commit()
            result = show_teams()

        assert len(result["teams"]) == 1
        assert result["teams"][0]["team_name"] == "Solo Team"
        assert result["teams"][0]["member_count"] == 0

    def test_show_teams_member_count_accurate(self, app):
        with app.app_context():
            u1 = make_user("tc1@gmail.com")
            u2 = make_user("tc2@gmail.com")
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            team = make_team(ladder.id, "Full Team")
            m1 = make_member(u1.id, club.id)
            m2 = make_member(u2.id, club.id)
            make_team_member(team.id, m1.id)
            make_team_member(team.id, m2.id)
            db.session.commit()
            result = show_teams()

        entry = next(t for t in result["teams"] if t["team_name"] == "Full Team")
        assert entry["member_count"] == 2

    def test_show_teams_multiple_teams(self, app):
        with app.app_context():
            sport = make_sport()
            ladder = make_ladder(sport.id)
            make_team(ladder.id, "Team A")
            make_team(ladder.id, "Team B")
            make_team(ladder.id, "Team C")
            db.session.commit()
            result = show_teams()

        assert len(result["teams"]) == 3

    def test_show_teams_partial_members(self, app):
        with app.app_context():
            u = make_user("partial@gmail.com")
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            team = make_team(ladder.id)
            m = make_member(u.id, club.id)
            make_team_member(team.id, m.id)
            db.session.commit()
            result = show_teams()

        assert result["teams"][0]["member_count"] == 1


# ===========================================================================
# create_team (function-level)
# ===========================================================================

class TestCreateTeam:
    def test_create_team_success(self, app):
        with app.app_context():
            u = make_user("ct.ok@gmail.com")
            u_id = u.id
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            ladder_id = ladder.id
            make_member(u_id, club.id)
            db.session.commit()

            with app.test_request_context():
                g.current_user = {"sub": str(u_id)}
                result = create_team("MyTeam", u_id, ladder_id)

        assert result["success"] is True
        assert "team_id" in result

    def test_create_team_creates_team_member_record(self, app):
        with app.app_context():
            u = make_user("ct.member@gmail.com")
            u_id = u.id
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            ladder_id = ladder.id
            make_member(u_id, club.id)
            db.session.commit()

            with app.test_request_context():
                g.current_user = {"sub": str(u_id)}
                result = create_team("AutoJoin", u_id, ladder_id)

            team_id = result["team_id"]
            member = db.session.query(Member).filter_by(user_id=u_id).first()
            assert db.session.query(TeamMember).filter_by(
                team_id=team_id, member_id=member.id
            ).first() is not None

    def test_create_team_already_in_team(self, app):
        with app.app_context():
            u = make_user("ct.already@gmail.com")
            u_id = u.id
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            ladder_id = ladder.id
            make_member(u_id, club.id)
            db.session.commit()

            with app.test_request_context():
                g.current_user = {"sub": str(u_id)}
                create_team("First", u_id, ladder_id)
                result = create_team("Second", u_id, ladder_id)

        assert result["success"] is False
        assert result["error"] == "already_in_team_in_this_ladder"

    def test_create_team_no_ladder_exists(self, app):
        with app.app_context():
            u = make_user("ct.noladder@gmail.com")
            u_id = u.id
            club = make_club()
            make_member(u_id, club.id)
            db.session.commit()

            with app.test_request_context():
                g.current_user = {"sub": str(u_id)}
                result = create_team("Orphan", u_id,99999)

        assert result["success"] is False
        assert result["error"] in ("no_ladders_exist","ladder_not_found")

    def test_create_team_no_club_exists(self, app):
        with app.app_context():
            u = make_user("ct.noclub@gmail.com")
            u_id = u.id
            db.session.commit()

            with app.test_request_context():
                g.current_user = {"sub": str(u_id)}
                result = create_team("NoClub", u_id,1)

        assert result["success"] is False
        assert result["error"] == "not_in_club"

    def test_create_team_uses_latest_ladder(self, app):
        with app.app_context():
            u = make_user("ct.latest@gmail.com")
            u_id = u.id
            club = make_club()
            sport = make_sport()
            make_ladder(sport.id, club.id, "Old Ladder")
            l2 = make_ladder(sport.id, club.id, "New Ladder")
            l2_id = l2.id
            make_member(u_id, club.id)
            db.session.commit()

            with app.test_request_context():
                g.current_user = {"sub": str(u_id)}
                result = create_team("LatestLadder", u_id,l2_id)

            team = db.session.get(Team, result["team_id"])
            assert team.ladder_id == l2_id

    def test_create_team_user_without_existing_member_record(self, app):
        with app.app_context():
            u = make_user("ct.nomember@gmail.com")
            u_id = u.id
            make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id)
            ladder_id = ladder.id
            db.session.commit()

            assert db.session.query(Member).filter_by(user_id=u_id).first() is None

            with app.test_request_context():
                g.current_user = {"sub": str(u_id)}
                result = create_team("AutoMember", u_id, ladder_id)

            assert result["success"] is False
            assert result["error"] == "not_in_club"


# ===========================================================================
# join_team (function-level)
# ===========================================================================

class TestJoinTeam:
    def test_join_team_success(self, app):
        with app.app_context():
            u = make_user("jt.ok@gmail.com")
            u_id = u.id
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            team = make_team(ladder.id)
            team_id = team.id
            make_member(u_id, club.id)
            db.session.commit()

            with app.test_request_context():
                g.current_user = {"sub": str(u_id)}
                result = join_team(team_id)

        assert result["success"] is True
        assert result["message"] == "joined_team"

    def test_join_team_already_in_team(self, app):
        with app.app_context():
            u = make_user("jt.already@gmail.com")
            u_id = u.id
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            t1 = make_team(ladder.id, "T1")
            t2 = make_team(ladder.id, "T2")
            t2_id = t2.id
            m = make_member(u_id, club.id)
            make_team_member(t1.id, m.id)
            db.session.commit()

            with app.test_request_context():
                g.current_user = {"sub": str(u_id)}
                result = join_team(t2_id)

        assert result["success"] is False
        assert result["error"] == "already_in_team_in_this_ladder"

    def test_join_team_full(self, app):
        with app.app_context():
            u1 = make_user("jt.full1@gmail.com")
            u2 = make_user("jt.full2@gmail.com")
            u3 = make_user("jt.full3@gmail.com")
            u3_id = u3.id
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            team = make_team(ladder.id)
            team_id = team.id
            m1 = make_member(u1.id, club.id)
            m2 = make_member(u2.id, club.id)
            make_member(u3_id, club.id)
            make_team_member(team_id, m1.id)
            make_team_member(team_id, m2.id)
            db.session.commit()

            with app.test_request_context():
                g.current_user = {"sub": str(u3_id)}
                result = join_team(team_id)

        assert result["success"] is False
        assert result["error"] == "team_full"

    def test_join_team_not_found(self, app):
        with app.app_context():
            u = make_user("jt.notfound@gmail.com")
            u_id = u.id
            club = make_club()
            make_member(u_id, club.id)
            db.session.commit()

            with app.test_request_context():
                g.current_user = {"sub": str(u_id)}
                result = join_team(99999)

        assert result["success"] is False
        assert result["error"] == "team_not_found"

    def test_join_team_exactly_one_slot_remaining(self, app):
        with app.app_context():
            u1 = make_user("jt.1slot1@gmail.com")
            u2 = make_user("jt.1slot2@gmail.com")
            u2_id = u2.id
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            team = make_team(ladder.id)
            team_id = team.id
            m1 = make_member(u1.id, club.id)
            make_member(u2_id, club.id)
            make_team_member(team_id, m1.id)
            db.session.commit()

            with app.test_request_context():
                g.current_user = {"sub": str(u2_id)}
                result = join_team(team_id)

        assert result["success"] is True

    def test_join_team_correct_team_member_row_created(self, app):
        with app.app_context():
            u = make_user("jt.row@gmail.com")
            u_id = u.id
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            team = make_team(ladder.id)
            team_id = team.id
            make_member(u_id, club.id)
            db.session.commit()

            with app.test_request_context():
                g.current_user = {"sub": str(u_id)}
                join_team(team_id)

            member = db.session.query(Member).filter_by(user_id=u_id).first()
            assert db.session.query(TeamMember).filter_by(
                team_id=team_id, member_id=member.id
            ).first() is not None


# ===========================================================================
# API-level team tests
# ===========================================================================

class TestTeamsAPI:
    def test_get_teams_requires_auth(self, client):
        res = client.get("/api/teams")
        assert res.status_code == 401

    def test_post_teams_requires_auth(self, client):
        res = client.post("/api/teams", json={"team_name": "X"})
        assert res.status_code == 401

    def test_post_teams_missing_team_name(self, client, app):
        with app.app_context():
            make_club()
            sport = make_sport()
            make_ladder(sport.id)
            db.session.commit()
        headers = api_register_and_login(client)
        res = client.post("/api/teams", json={}, headers=headers)
        assert res.status_code == 400

    def test_post_teams_creates_and_shows_in_list(self, client, app):
        with app.app_context():
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            db.session.commit()
            ladder_id = ladder.id
            club_id = club.id

        email = "smashers.user@gmail.com"
        headers = api_register_and_login(client, email)

        with app.app_context():
            user = db.session.query(User).filter_by(email=email).first()
            member = Member(user_id=user.id, club_id=club_id)
            db.session.add(member)
            db.session.commit()

        res = client.post("/api/teams", json={"team_name": "Team1","ladder_id":ladder_id}, headers=headers)
        assert res.get_json()["success"] is True

        teams = client.get("/api/teams", headers=headers).get_json()["teams"]
        assert len(teams) == 1
        assert teams[0]["team_name"] == "Team1"


    def test_join_team_api_nonexistent_team(self, client, app):
        """A club must exist so join_team reaches the team_not_found check."""
        with app.app_context():
            club = make_club()
            db.session.commit()
            club_id = club.id

        email = "join.none@gmail.com"
        headers = api_register_and_login(client, email)

        with app.app_context():
            user = db.session.query(User).filter_by(email=email).first()
            member = Member(user_id=user.id, club_id=club_id)
            db.session.add(member)
            db.session.commit()

        res = client.post("/api/teams/99999/join", headers=headers)
        assert res.status_code == 404 or res.get_json()["success"] is False
        assert res.get_json()["error"] == "team_not_found"


    def test_create_then_join_different_team_blocked(self, client, app):
        with app.app_context():
            club = make_club()
            sport = make_sport()
            ladder = make_ladder(sport.id, club.id)
            db.session.commit()
            ladder_id = ladder.id
            club_id = club.id

        creator_email = "creator.user@gmail.com"
        joiner_email = "joiner.user@gmail.com"

        h1 = api_register_and_login(client, creator_email)
        headers_joiner = api_register_and_login(client, joiner_email)

        with app.app_context():
            creator = db.session.query(User).filter_by(email=creator_email).first()
            creator_member = Member(user_id=creator.id, club_id=club_id)
            db.session.add(creator_member)

            joiner = db.session.query(User).filter_by(email=joiner_email).first()
            joiner_member = Member(user_id=joiner.id, club_id=club_id)
            db.session.add(joiner_member)
            db.session.commit()

        client.post("/api/teams", json={"team_name": "Team1", "ladder_id": ladder_id}, headers=h1)
        client.post("/api/teams", json={"team_name": "Team2", "ladder_id": ladder_id}, headers=headers_joiner)

        teams = client.get("/api/teams", headers=h1).get_json()["teams"]
        team_id = teams[0]["team_id"]

        res = client.post(f"/api/teams/{team_id}/join", headers=headers_joiner)

        assert res.get_json()["success"] is False
        assert res.get_json()["error"] == "already_in_team_in_this_ladder"

    def test_join_team_api_requires_auth(self, client):
        res = client.post("/api/teams/1/join")
        assert res.status_code == 401


# ===========================================================================
# Admin tests (duplicated here because teams_test.py imported profile tests)
# ===========================================================================

from werkzeug.security import generate_password_hash
from elo import calculate_elo_simple
from db import apply_match_result


def make_ladder_for_admin(sport_id, club_id=None):
    l = Ladder(
        sport_id=sport_id, club_id=club_id, name="Ladder",
        start_date=date(2024, 1, 1), end_date=date(2024, 12, 31),
    )
    db.session.add(l)
    db.session.flush()
    return l


def make_member_admin(user_id, club_id, is_admin=False, elo=1000):
    m = Member(user_id=user_id, club_id=club_id, joined_at=date.today(),
               is_admin=is_admin, elo=elo)
    db.session.add(m)
    db.session.flush()
    return m


class TestGetProfile:
    def test_get_profile_success(self, client):
        headers = register_and_login(client, "prof.jane@gmail.com", first="Jane", last="Doe")
        res = client.get("/api/profile", headers=headers)
        assert res.status_code == 200
        data = res.get_json()
        assert data["first_name"] == "Jane"

    def test_get_profile_unauthenticated(self, client):
        assert client.get("/api/profile").status_code == 401

    def test_get_profile_bio_defaults_to_empty_string(self, client):
        headers = register_and_login(client, "bio.default2@gmail.com")
        assert client.get("/api/profile", headers=headers).get_json()["bio"] == ""

    def test_get_profile_photo_url_defaults_to_empty(self, client):
        headers = register_and_login(client, "photo.default2@gmail.com")
        assert client.get("/api/profile", headers=headers).get_json()["photo_url"] == ""

    def test_get_profile_contains_id(self, client):
        headers = register_and_login(client, "idcheck2.user@gmail.com")
        assert "id" in client.get("/api/profile", headers=headers).get_json()


class TestUpdateProfile:
    def test_update_bio(self, client):
        headers = register_and_login(client, "updbio2.user@gmail.com")
        res = client.put("/api/profile", json={"bio": "I love tennis!"}, headers=headers)
        assert res.status_code == 200
        assert client.get("/api/profile", headers=headers).get_json()["bio"] == "I love tennis!"

    def test_update_photo_url(self, client):
        headers = register_and_login(client, "updphoto2.user@gmail.com")
        url = "https://example.com/photo.jpg"
        res = client.put("/api/profile", json={"photo_url": url}, headers=headers)
        assert res.status_code == 200
        assert client.get("/api/profile", headers=headers).get_json()["photo_url"] == url

    def test_update_both_bio_and_photo(self, client):
        headers = register_and_login(client, "updboth2.user@gmail.com")
        res = client.put("/api/profile", json={"bio": "Padel fanatic", "photo_url": "https://x.com/me.jpg"}, headers=headers)
        assert res.status_code == 200

    def test_update_profile_empty_body_returns_400(self, client):
        headers = register_and_login(client, "emptyupd2.user@gmail.com")
        assert client.put("/api/profile", json={}, headers=headers).status_code == 400

    def test_update_profile_unauthenticated(self, client):
        assert client.put("/api/profile", json={"bio": "nope"}).status_code == 401

    def test_update_bio_empty_string(self, client):
        headers = register_and_login(client, "bioempty2.user@gmail.com")
        client.put("/api/profile", json={"bio": "Something"}, headers=headers)
        assert client.put("/api/profile", json={"bio": ""}, headers=headers).status_code == 200

    def test_profile_update_does_not_change_name_or_email(self, client):
        headers = register_and_login(client, "stable2.name@gmail.com", first="Stable", last="Name")
        client.put("/api/profile", json={"bio": "Changed"}, headers=headers)
        data = client.get("/api/profile", headers=headers).get_json()
        assert data["first_name"] == "Stable"
        assert data["email"] == "stable2.name@gmail.com"


class TestCalculateEloSimple:
    def test_winner_gains_25(self):
        assert calculate_elo_simple(1000, 1000)[0] == 1025

    def test_loser_loses_25(self):
        assert calculate_elo_simple(1000, 1000)[1] == 975

    def test_winner_always_gains(self):
        for w, l in [(500, 2000), (1000, 1000), (2000, 500)]:
            assert calculate_elo_simple(w, l)[0] > w

    def test_loser_always_loses(self):
        for w, l in [(500, 2000), (1000, 1000), (2000, 500)]:
            assert calculate_elo_simple(w, l)[1] < l

    def test_elo_change_is_symmetric(self):
        w, l = 1200, 800
        new_w, new_l = calculate_elo_simple(w, l)
        assert (new_w - w) == (l - new_l)

    def test_zero_elo_winner(self):
        assert calculate_elo_simple(0, 1000)[0] > 0

    def test_very_high_elo_values(self):
        new_w, new_l = calculate_elo_simple(3000, 2500)
        assert new_w > 3000 and new_l < 2500


class TestApplyMatchResult:
    def _setup(self, app):
        with app.app_context():
            u1 = User(first_name="A", last_name="B", email="mr1b.player@gmail.com",
                      password="x", date_of_birth=date(1990, 1, 1), created_at=date.today())
            u2 = User(first_name="C", last_name="D", email="mr2b.player@gmail.com",
                      password="x", date_of_birth=date(1990, 1, 1), created_at=date.today())
            db.session.add_all([u1, u2])
            db.session.flush()
            club = make_club("Club2")
            sport = make_sport("Sport2")
            ladder = make_ladder_for_admin(sport.id, club.id)
            t1 = make_team(ladder.id, "TA")
            t2 = make_team(ladder.id, "TB")
            m1 = make_member_admin(u1.id, club.id, elo=1000)
            m2 = make_member_admin(u2.id, club.id, elo=1000)
            make_team_member(t1.id, m1.id)
            make_team_member(t2.id, m2.id)
            match = Match(date=date.today(), home_team_id=t1.id, away_team_id=t2.id)
            db.session.add(match)
            db.session.commit()
            return match.id, m1.id, m2.id

    def test_winner_elo_increases(self, app):
        mid, m1, _ = self._setup(app)
        with app.app_context():
            db.session.add(Score(match_id=mid, set=1, home_score=6, away_score=0))
            db.session.commit()
            apply_match_result(mid)
            assert db.session.get(Member, m1).elo > 1000

    def test_loser_elo_decreases(self, app):
        mid, _, m2 = self._setup(app)
        with app.app_context():
            db.session.add(Score(match_id=mid, set=1, home_score=6, away_score=0))
            db.session.commit()
            apply_match_result(mid)
            assert db.session.get(Member, m2).elo < 1000

    def test_away_team_wins(self, app):
        mid, m1, m2 = self._setup(app)
        with app.app_context():
            db.session.add(Score(match_id=mid, set=1, home_score=0, away_score=6))
            db.session.commit()
            apply_match_result(mid)
            assert db.session.get(Member, m2).elo > 1000
            assert db.session.get(Member, m1).elo < 1000

    def test_no_score_no_change(self, app):
        mid, m1, m2 = self._setup(app)
        with app.app_context():
            apply_match_result(mid)
            assert db.session.get(Member, m1).elo == 1000
            assert db.session.get(Member, m2).elo == 1000

    def test_invalid_match_id_no_crash(self, app):
        with app.app_context():
            apply_match_result(99999)


class TestAdminUsers:
    def _make_admin(self, app, email="admin2.superuser@gmail.com", password="adminpass99"):
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
        headers = register_and_login(client, "norma3.user@gmail.com")
        assert client.get("/api/admin/users", headers=headers).status_code == 403

    def test_list_users_unauthenticated(self, client):
        assert client.get("/api/admin/users").status_code == 401

    def test_list_users_success(self, client, app):
        headers = self._admin_headers(client, app)
        register_and_login(client, "listme2.user@gmail.com")
        res = client.get("/api/admin/users", headers=headers)
        assert res.status_code == 200
        assert any(u["email"] == "listme2.user@gmail.com" for u in res.get_json())

    def test_delete_user_success(self, client, app):
        headers = self._admin_headers(client, app)
        rh = register_and_login(client, "todelete2.user@gmail.com")
        uid = client.get("/api/profile", headers=rh).get_json()["id"]
        assert client.delete(f"/api/admin/users/{uid}", headers=headers).status_code == 200

    def test_delete_user_not_found(self, client, app):
        headers = self._admin_headers(client, app)
        assert client.delete("/api/admin/users/99999", headers=headers).status_code == 404

    def test_admin_cannot_self_delete(self, client, app):
        headers = self._admin_headers(client, app)
        aid = client.get("/api/profile", headers=headers).get_json()["id"]
        assert client.delete(f"/api/admin/users/{aid}", headers=headers).status_code == 400

    def test_delete_user_requires_admin(self, client):
        headers = register_and_login(client, "delnonadm2.user@gmail.com")
        assert client.delete("/api/admin/users/1", headers=headers).status_code == 403

    def test_list_clubs_admin_only(self, client, app):
        headers = self._admin_headers(client, app)
        res = client.get("/api/admin/clubs", headers=headers)
        assert res.status_code == 200 and isinstance(res.get_json(), list)

    def test_list_clubs_requires_admin(self, client):
        headers = register_and_login(client, "norma4.user@gmail.com")
        assert client.get("/api/admin/clubs", headers=headers).status_code == 403

    def test_list_teams_admin_only(self, client, app):
        headers = self._admin_headers(client, app)
        res = client.get("/api/admin/teams", headers=headers)
        assert res.status_code == 200 and isinstance(res.get_json(), list)

    def test_update_user_club_to_valid_club(self, client, app):
        headers = self._admin_headers(client, app)
        with app.app_context():
            club = make_club("Club3")
            db.session.commit()
            cid = club.id
        rh = register_and_login(client, "assignclub2.user@gmail.com")
        uid = client.get("/api/profile", headers=rh).get_json()["id"]
        res = client.put(f"/api/admin/users/{uid}/club", json={"club_id": cid}, headers=headers)
        assert res.status_code == 200

    def test_update_user_club_nonexistent_club(self, client, app):
        headers = self._admin_headers(client, app)
        rh = register_and_login(client, "badclub2.user@gmail.com")
        uid = client.get("/api/profile", headers=rh).get_json()["id"]
        assert client.put(f"/api/admin/users/{uid}/club", json={"club_id": 99999}, headers=headers).status_code == 404

    def test_update_user_club_null_fails_db_constraint(self, client, app):
        headers = self._admin_headers(client, app)
        rh = register_and_login(client, "clubnull2.user@gmail.com")
        uid = client.get("/api/profile", headers=rh).get_json()["id"]
        assert client.put(f"/api/admin/users/{uid}/club", json={"club_id": None}, headers=headers).status_code == 500

    def test_update_user_team_to_valid_team(self, client, app):
        headers = self._admin_headers(client, app)
        with app.app_context():
            club = make_club("Club4")
            sport = make_sport("Sport4")
            ladder = make_ladder_for_admin(sport.id, club.id)
            team = make_team(ladder.id, "AdminTeam2")
            db.session.commit()
            tid, cid = team.id, club.id
        rh = register_and_login(client, "assignteam2.user@gmail.com")
        uid = client.get("/api/profile", headers=rh).get_json()["id"]
        client.put(f"/api/admin/users/{uid}/club", json={"club_id": cid}, headers=headers)
        assert client.put(f"/api/admin/users/{uid}/team", json={"team_id": tid}, headers=headers).status_code == 200

    def test_update_user_team_nonexistent(self, client, app):
        headers = self._admin_headers(client, app)
        rh = register_and_login(client, "badteam2.user@gmail.com")
        uid = client.get("/api/profile", headers=rh).get_json()["id"]
        assert client.put(f"/api/admin/users/{uid}/team", json={"team_id": 99999}, headers=headers).status_code == 404

    def test_update_user_team_null_no_member_row_returns_200(self, client, app):
        """team_id=null with no member row → 200 (no-op)."""
        headers = self._admin_headers(client, app)
        rh = register_and_login(client, "teamnull2.user@gmail.com")
        uid = client.get("/api/profile", headers=rh).get_json()["id"]
        assert client.put(f"/api/admin/users/{uid}/team", json={"team_id": None}, headers=headers).status_code == 200

    def test_update_user_team_set_team_without_club_returns_400(self, client, app):
        """team_id set but user has no club → 400."""
        headers = self._admin_headers(client, app)
        with app.app_context():
            club = make_club("Club5")
            sport = make_sport("Sport5")
            ladder = make_ladder_for_admin(sport.id, club.id)
            team = make_team(ladder.id, "SomeTeam2")
            db.session.commit()
            tid = team.id
        rh = register_and_login(client, "teamnoclub2.user@gmail.com")
        uid = client.get("/api/profile", headers=rh).get_json()["id"]
        assert client.put(f"/api/admin/users/{uid}/team", json={"team_id": tid}, headers=headers).status_code == 400

    def test_get_user_details_admin(self, client, app):
        headers = self._admin_headers(client, app)
        rh = register_and_login(client, "details2.user@gmail.com")
        uid = client.get("/api/profile", headers=rh).get_json()["id"]
        res = client.get(f"/api/admin/users/{uid}/details", headers=headers)
        assert res.status_code == 200
        assert "club_id" in res.get_json() and "team_id" in res.get_json()

    def test_get_user_details_not_found(self, client, app):
        headers = self._admin_headers(client, app)
        assert client.get("/api/admin/users/99999/details", headers=headers).status_code == 404


class TestClubStatus:
    def test_club_status_not_club_admin(self, client):
        headers = register_and_login(client, "nostatus2.user@gmail.com")
        data = client.get("/api/profile/club-status", headers=headers).get_json()
        assert data["is_club_admin"] is False

    def test_club_status_is_club_admin(self, client, app):
        headers = register_and_login(client, "clubstatus2.user@gmail.com")
        uid = client.get("/api/profile", headers=headers).get_json()["id"]
        with app.app_context():
            club = make_club("Club6")
            make_member_admin(uid, club.id, is_admin=True)
            db.session.commit()
            cid, cname = club.id, club.name
        data = client.get("/api/profile/club-status", headers=headers).get_json()
        assert data["is_club_admin"] is True and data["club_id"] == cid

    def test_club_status_requires_auth(self, client):
        assert client.get("/api/profile/club-status").status_code == 401

    def test_club_status_regular_member_not_admin(self, client, app):
        headers = register_and_login(client, "regmember2.user@gmail.com")
        uid = client.get("/api/profile", headers=headers).get_json()["id"]
        with app.app_context():
            club = make_club("Club7")
            make_member_admin(uid, club.id, is_admin=False)
            db.session.commit()
        assert client.get("/api/profile/club-status", headers=headers).get_json()["is_club_admin"] is False
