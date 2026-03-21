from datetime import date, datetime, timedelta
from unittest.mock import MagicMock
from flask import g
from db import db, User, Club, Member, Request, JoinRequest, ClubRequest
from clubs import (
    leave_club,
    show_clubs,
    request_join,
    request_join_club,
    request_new_club,
    review_join_request,
    delete_club,
    _delete_club_cascade,
    _auto_delete_if_no_admin,
)
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email, is_admin=False):
    u = User(
        first_name="A", last_name="B", email=email, password="hashed",
        date_of_birth=date(2000, 1, 1), created_at=date.today(), is_admin=is_admin,
    )
    db.session.add(u)
    db.session.flush()
    return u


def make_club(name="Test Club", city="Antwerp"):
    c = Club(name=name, city=city, created_at=datetime.now())
    db.session.add(c)
    db.session.flush()
    return c


def make_member(user_id, club_id, is_admin=False):
    m = Member(user_id=user_id, club_id=club_id, joined_at=date.today(), is_admin=is_admin, elo=0)
    db.session.add(m)
    db.session.flush()
    return m


def make_join_request(user_id, club_id, status="pending", motivation="test"):
    jr = JoinRequest(user_id=user_id, club_id=club_id, motivation=motivation,
                     status=status, created_at=date.today())
    db.session.add(jr)
    db.session.flush()
    return jr


def make_legacy_request(user_id, club_id):
    r = Request(user_id=user_id, club_id=club_id, expires_at=date.today() + timedelta(days=14))
    db.session.add(r)
    db.session.flush()
    return r


def fake_mail():
    return MagicMock()


# ---------------------------------------------------------------------------
# Fixture: wipe all club-related tables before and after each test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        JoinRequest.query.delete()
        ClubRequest.query.delete()
        Request.query.delete()
        Member.query.delete()
        Club.query.delete()
        User.query.delete()
        db.session.commit()
    yield
    with app.app_context():
        JoinRequest.query.delete()
        ClubRequest.query.delete()
        Request.query.delete()
        Member.query.delete()
        Club.query.delete()
        User.query.delete()
        db.session.commit()


# ===========================================================================
# leave_club
# ===========================================================================

def test_leave_club_success(app):
    with app.app_context():
        user = make_user("leave_ok@test.com")
        club = make_club()
        make_member(user.id, club.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = leave_club(club.id)

        assert result["success"] is True
        assert result["message"] == "left_club"
        assert db.session.query(Member).filter_by(user_id=user.id, club_id=club.id).first() is None


def test_leave_club_not_a_member(app):
    with app.app_context():
        user = make_user("leave_fail@test.com")
        club = make_club()
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = leave_club(club.id)

        assert result["success"] is False
        assert result["error"] == "not_a_member"


def test_leave_club_cleans_up_approved_join_request(app):
    """An approved JoinRequest is deleted on leave so the user can re-apply later."""
    with app.app_context():
        user = make_user("leave_approved_jr@test.com")
        club = make_club()
        make_member(user.id, club.id)
        make_join_request(user.id, club.id, status="approved")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = leave_club(club.id)

        assert result["success"] is True
        assert db.session.query(JoinRequest).filter_by(user_id=user.id, club_id=club.id).first() is None


def test_leave_club_cleans_up_pending_join_request(app):
    """A pending JoinRequest is also cleaned up on leave."""
    with app.app_context():
        user = make_user("leave_pending_jr@test.com")
        club = make_club()
        make_member(user.id, club.id)
        make_join_request(user.id, club.id, status="pending")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = leave_club(club.id)

        assert result["success"] is True
        assert db.session.query(JoinRequest).filter_by(user_id=user.id, club_id=club.id).first() is None


def test_leave_club_auto_deletes_empty_club(app):
    """Club is deleted automatically when the last member leaves."""
    with app.app_context():
        user = make_user("leave_auto@test.com")
        club = make_club()
        club_id = club.id
        make_member(user.id, club.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            leave_club(club_id)

        assert db.session.get(Club, club_id) is None


def test_leave_club_does_not_delete_club_with_remaining_members(app):
    """Club stays when at least one other member remains."""
    with app.app_context():
        user1 = make_user("leave_keep1@test.com")
        user2 = make_user("leave_keep2@test.com")
        club = make_club()
        club_id = club.id
        make_member(user1.id, club.id)
        make_member(user2.id, club.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user1.id)}
            result = leave_club(club_id)

        assert result["success"] is True
        assert db.session.get(Club, club_id) is not None
        assert db.session.query(Member).filter_by(user_id=user2.id, club_id=club_id).first() is not None


def test_leave_club_does_not_affect_other_club_memberships(app):
    """Leaving club A does not remove the user's membership in club B."""
    with app.app_context():
        user = make_user("leave_other@test.com")
        club_a = make_club("Club A")
        club_b = make_club("Club B")
        make_member(user.id, club_a.id)
        make_member(user.id, club_b.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            leave_club(club_a.id)

        assert db.session.query(Member).filter_by(user_id=user.id, club_id=club_b.id).first() is not None


def test_leave_club_join_request_cleanup_only_for_that_club(app):
    """Leaving club A only deletes the JoinRequest for club A, not club B."""
    with app.app_context():
        user = make_user("leave_jr_other@test.com")
        club_a = make_club("Club A")
        club_b = make_club("Club B")
        make_member(user.id, club_a.id)
        make_join_request(user.id, club_a.id, status="approved")
        jr_b = make_join_request(user.id, club_b.id, status="pending")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            leave_club(club_a.id)

        assert db.session.query(JoinRequest).filter_by(user_id=user.id, club_id=club_a.id).first() is None
        assert db.session.get(JoinRequest, jr_b.id) is not None


# ===========================================================================
# request_join (legacy Request table)
# ===========================================================================

def test_request_join_success(app):
    with app.app_context():
        user = make_user("rj_ok@test.com")
        club = make_club()
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join(club.id)

        assert result["success"] is True
        assert result["message"] == "join_request_created"
        assert db.session.query(Request).filter_by(user_id=user.id, club_id=club.id).first() is not None


def test_request_join_already_member(app):
    with app.app_context():
        user = make_user("rj_member@test.com")
        club = make_club()
        make_member(user.id, club.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join(club.id)

        assert result["success"] is False
        assert result["error"] == "already_in_club"


def test_request_join_club_not_found(app):
    with app.app_context():
        user = make_user("rj_noclub@test.com")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join(99999)

        assert result["success"] is False
        assert result["error"] == "club_not_found"


def test_request_join_duplicate_blocked(app):
    with app.app_context():
        user = make_user("rj_dup@test.com")
        club = make_club()
        make_legacy_request(user.id, club.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join(club.id)

        assert result["success"] is False
        assert result["error"] == "request_already_exists"
        assert db.session.query(Request).filter_by(user_id=user.id, club_id=club.id).count() == 1


def test_request_join_does_not_block_request_for_different_club(app):
    """Having a legacy request for club A does not block a request for club B."""
    with app.app_context():
        user = make_user("rj_other_club@test.com")
        club_a = make_club("Club A")
        club_b = make_club("Club B")
        make_legacy_request(user.id, club_a.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join(club_b.id)

        assert result["success"] is True


# ===========================================================================
# request_join_club (JoinRequest table)
# ===========================================================================

def test_request_join_club_success(app):
    with app.app_context():
        user = make_user("rjc_ok@test.com")
        club = make_club()
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join_club(club.id, "I want to join", fake_mail())

        assert result["success"] is True
        assert result["message"] == "join_request_submitted"
        jr = db.session.query(JoinRequest).filter_by(user_id=user.id, club_id=club.id).first()
        assert jr is not None
        assert jr.status == "pending"
        assert jr.motivation == "I want to join"


def test_request_join_club_empty_motivation_stored_as_empty_string(app):
    """Empty motivation is stored as '' not None."""
    with app.app_context():
        user = make_user("rjc_empty@test.com")
        club = make_club()
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join_club(club.id, "", fake_mail())

        assert result["success"] is True
        jr = db.session.query(JoinRequest).filter_by(user_id=user.id, club_id=club.id).first()
        assert jr.motivation == ""


def test_request_join_club_already_member_of_that_club(app):
    with app.app_context():
        user = make_user("rjc_member@test.com")
        club = make_club()
        make_member(user.id, club.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join_club(club.id, "", fake_mail())

        assert result["success"] is False
        assert result["error"] == "already_member"


def test_request_join_club_already_pending(app):
    with app.app_context():
        user = make_user("rjc_pending@test.com")
        club = make_club()
        make_join_request(user.id, club.id, status="pending")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join_club(club.id, "", fake_mail())

        assert result["success"] is False
        assert result["error"] == "request_already_pending"
        assert db.session.query(JoinRequest).filter_by(user_id=user.id, club_id=club.id).count() == 1


def test_request_join_club_reuses_rejected_row(app):
    """A rejected row is reused — no duplicate insert, no UniqueViolation."""
    with app.app_context():
        user = make_user("rjc_reuse_rej@test.com")
        club = make_club()
        old = make_join_request(user.id, club.id, status="rejected")
        old_id = old.id
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join_club(club.id, "trying again", fake_mail())

        assert result["success"] is True
        jr = db.session.query(JoinRequest).filter_by(user_id=user.id, club_id=club.id).first()
        assert jr.id == old_id
        assert jr.status == "pending"
        assert jr.motivation == "trying again"
        assert db.session.query(JoinRequest).filter_by(user_id=user.id, club_id=club.id).count() == 1


def test_request_join_club_reuses_approved_row(app):
    """An approved row (user left and re-applies) is reused — no UniqueViolation."""
    with app.app_context():
        user = make_user("rjc_reuse_app@test.com")
        club = make_club()
        old = make_join_request(user.id, club.id, status="approved")
        old_id = old.id
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join_club(club.id, "rejoining", fake_mail())

        assert result["success"] is True
        jr = db.session.query(JoinRequest).filter_by(user_id=user.id, club_id=club.id).first()
        assert jr.id == old_id
        assert jr.status == "pending"
        assert db.session.query(JoinRequest).filter_by(user_id=user.id, club_id=club.id).count() == 1


def test_request_join_club_not_found(app):
    with app.app_context():
        user = make_user("rjc_noclub@test.com")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join_club(99999, "", fake_mail())

        assert result["success"] is False
        assert result["error"] == "club_not_found"


def test_request_join_club_member_of_different_club_can_still_request(app):
    """Being a member of club A does not block a join request for club B
    (the membership check is scoped to the target club_id)."""
    with app.app_context():
        user = make_user("rjc_other_member@test.com")
        club_a = make_club("Club A")
        club_b = make_club("Club B")
        make_member(user.id, club_a.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join_club(club_b.id, "", fake_mail())

        assert result["success"] is True


def test_request_join_club_pending_for_one_club_does_not_block_another(app):
    """A pending request for club A does not block a request for club B."""
    with app.app_context():
        user = make_user("rjc_two_clubs@test.com")
        club_a = make_club("Club A")
        club_b = make_club("Club B")
        make_join_request(user.id, club_a.id, status="pending")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_join_club(club_b.id, "", fake_mail())

        assert result["success"] is True


# ===========================================================================
# request_new_club
# ===========================================================================

def test_request_new_club_success(app):
    with app.app_context():
        user = make_user("rnc_ok@test.com")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_new_club("My Club", "Brussels", "great idea", [], fake_mail())

        assert result["success"] is True
        assert result["message"] == "club_request_submitted"
        cr = db.session.query(ClubRequest).filter_by(user_id=user.id, status="pending").first()
        assert cr is not None
        assert cr.club_name == "My Club"
        assert cr.city == "Brussels"


def test_request_new_club_blocks_second_pending(app):
    """A second club request is blocked while a pending one already exists."""
    with app.app_context():
        user = make_user("rnc_dup@test.com")
        db.session.add(ClubRequest(user_id=user.id, club_name="First", city="Ghent",
                                   motivation="", status="pending", created_at=date.today()))
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_new_club("Second", "Liège", "", [], fake_mail())

        assert result["success"] is False
        assert result["error"] == "pending_request_exists"
        assert db.session.query(ClubRequest).filter_by(user_id=user.id, status="pending").count() == 1


def test_request_new_club_allowed_after_rejection(app):
    """A new request is allowed after a previous one was rejected."""
    with app.app_context():
        user = make_user("rnc_after_rej@test.com")
        db.session.add(ClubRequest(user_id=user.id, club_name="Old", city="Ghent",
                                   motivation="", status="rejected", created_at=date.today()))
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_new_club("New Club", "Antwerp", "", [], fake_mail())

        assert result["success"] is True


def test_request_new_club_allowed_after_approval(app):
    """A new request is allowed even if a previous one was approved."""
    with app.app_context():
        user = make_user("rnc_after_app@test.com")
        db.session.add(ClubRequest(user_id=user.id, club_name="Old", city="Ghent",
                                   motivation="", status="approved", created_at=date.today()))
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = request_new_club("Another Club", "Bruges", "", [], fake_mail())

        assert result["success"] is True


def test_request_new_club_limit_is_per_user_not_global(app):
    """User A having a pending request does not block user B from submitting one."""
    with app.app_context():
        user_a = make_user("rnc_per_user_a@test.com")
        user_b = make_user("rnc_per_user_b@test.com")
        db.session.add(ClubRequest(user_id=user_a.id, club_name="Club A", city="Ghent",
                                   motivation="", status="pending", created_at=date.today()))
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user_b.id)}
            result = request_new_club("Club B", "Antwerp", "", [], fake_mail())

        assert result["success"] is True


# ===========================================================================
# review_join_request
# ===========================================================================

def test_review_join_request_approve(app):
    with app.app_context():
        admin = make_user("rjr_admin@test.com")
        requester = make_user("rjr_user@test.com")
        club = make_club()
        make_member(admin.id, club.id, is_admin=True)
        jr = make_join_request(requester.id, club.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(admin.id)}
            result = review_join_request(jr.id, "approve", fake_mail())

        assert result["success"] is True
        assert result["action"] == "approve"
        assert db.session.get(JoinRequest, jr.id).status == "approved"
        assert db.session.query(Member).filter_by(user_id=requester.id, club_id=club.id).first() is not None


def test_review_join_request_approve_moves_member_from_other_club(app):
    """Approving a user who is already a Member row (from another club) reuses
    that row instead of inserting a duplicate."""
    with app.app_context():
        admin = make_user("rjr_move_admin@test.com")
        requester = make_user("rjr_move_user@test.com")
        club_a = make_club("Club A")
        club_b = make_club("Club B")
        make_member(admin.id, club_b.id, is_admin=True)
        existing = make_member(requester.id, club_a.id, is_admin=False)
        jr = make_join_request(requester.id, club_b.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(admin.id)}
            result = review_join_request(jr.id, "approve", fake_mail())

        assert result["success"] is True
        updated = db.session.get(Member, existing.id)
        assert updated.club_id == club_b.id
        assert updated.is_admin is False
        assert db.session.query(Member).filter_by(user_id=requester.id).count() == 1


def test_review_join_request_reject(app):
    with app.app_context():
        admin = make_user("rjr_rej_admin@test.com")
        requester = make_user("rjr_rej_user@test.com")
        club = make_club()
        make_member(admin.id, club.id, is_admin=True)
        jr = make_join_request(requester.id, club.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(admin.id)}
            result = review_join_request(jr.id, "reject", fake_mail())

        assert result["success"] is True
        assert result["action"] == "reject"
        assert db.session.get(JoinRequest, jr.id).status == "rejected"
        assert db.session.query(Member).filter_by(user_id=requester.id, club_id=club.id).first() is None


def test_review_join_request_not_found(app):
    with app.app_context():
        admin = make_user("rjr_notfound@test.com")
        club = make_club()
        make_member(admin.id, club.id, is_admin=True)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(admin.id)}
            result = review_join_request(99999, "approve", fake_mail())

        assert result["success"] is False
        assert result["error"] == "request_not_found"


def test_review_join_request_forbidden_for_non_admin(app):
    with app.app_context():
        non_admin = make_user("rjr_non_admin@test.com")
        requester = make_user("rjr_non_admin_req@test.com")
        club = make_club()
        make_member(non_admin.id, club.id, is_admin=False)
        jr = make_join_request(requester.id, club.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(non_admin.id)}
            result = review_join_request(jr.id, "approve", fake_mail())

        assert result["success"] is False
        assert result["error"] == "forbidden"


def test_review_join_request_forbidden_for_admin_of_different_club(app):
    """Admin of club B cannot review a join request that belongs to club A."""
    with app.app_context():
        admin = make_user("rjr_wrong_admin@test.com")
        requester = make_user("rjr_wrong_req@test.com")
        club_a = make_club("Club A")
        club_b = make_club("Club B")
        make_member(admin.id, club_b.id, is_admin=True)
        jr = make_join_request(requester.id, club_a.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(admin.id)}
            result = review_join_request(jr.id, "approve", fake_mail())

        assert result["success"] is False
        assert result["error"] == "forbidden"


def test_review_join_request_already_approved_cannot_be_reviewed_again(app):
    with app.app_context():
        admin = make_user("rjr_re_app_admin@test.com")
        requester = make_user("rjr_re_app_user@test.com")
        club = make_club()
        make_member(admin.id, club.id, is_admin=True)
        jr = make_join_request(requester.id, club.id, status="approved")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(admin.id)}
            result = review_join_request(jr.id, "approve", fake_mail())

        assert result["success"] is False
        assert result["error"] == "request_already_reviewed"


def test_review_join_request_already_rejected_cannot_be_approved(app):
    with app.app_context():
        admin = make_user("rjr_re_rej_admin@test.com")
        requester = make_user("rjr_re_rej_user@test.com")
        club = make_club()
        make_member(admin.id, club.id, is_admin=True)
        jr = make_join_request(requester.id, club.id, status="rejected")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(admin.id)}
            result = review_join_request(jr.id, "approve", fake_mail())

        assert result["success"] is False
        assert result["error"] == "request_already_reviewed"


# ===========================================================================
# delete_club
# ===========================================================================

def test_delete_club_by_club_admin(app):
    with app.app_context():
        user = make_user("dc_admin@test.com")
        club = make_club()
        club_id = club.id
        make_member(user.id, club.id, is_admin=True)
        db.session.commit()

        result = delete_club(club_id, user.id, is_site_admin=False)

        assert result["success"] is True
        assert db.session.get(Club, club_id) is None


def test_delete_club_by_site_admin(app):
    with app.app_context():
        site_admin = make_user("dc_site@test.com", is_admin=True)
        owner = make_user("dc_owner@test.com")
        club = make_club()
        club_id = club.id
        make_member(owner.id, club.id, is_admin=True)
        db.session.commit()

        result = delete_club(club_id, site_admin.id, is_site_admin=True)

        assert result["success"] is True
        assert db.session.get(Club, club_id) is None


def test_delete_club_forbidden_for_regular_member(app):
    with app.app_context():
        user = make_user("dc_forbidden@test.com")
        club = make_club()
        club_id = club.id
        make_member(user.id, club.id, is_admin=False)
        db.session.commit()

        result = delete_club(club_id, user.id, is_site_admin=False)

        assert result["success"] is False
        assert result["error"] == "forbidden"
        assert db.session.get(Club, club_id) is not None


def test_delete_club_forbidden_for_non_member(app):
    """A user with no relation to the club at all cannot delete it."""
    with app.app_context():
        outsider = make_user("dc_outsider@test.com")
        club = make_club()
        club_id = club.id
        db.session.commit()

        result = delete_club(club_id, outsider.id, is_site_admin=False)

        assert result["success"] is False
        assert result["error"] == "forbidden"
        assert db.session.get(Club, club_id) is not None


def test_delete_club_not_found(app):
    with app.app_context():
        user = make_user("dc_notfound@test.com")
        db.session.commit()

        result = delete_club(99999, user.id, is_site_admin=True)

        assert result["success"] is False
        assert result["error"] == "club_not_found"


def test_delete_club_cascades_members_and_join_requests(app):
    """Deleting a club removes all members and all join requests."""
    with app.app_context():
        admin = make_user("dc_cascade_admin@test.com")
        member_user = make_user("dc_cascade_member@test.com")
        requester = make_user("dc_cascade_req@test.com")
        club = make_club()
        club_id = club.id
        make_member(admin.id, club.id, is_admin=True)
        make_member(member_user.id, club.id, is_admin=False)
        make_join_request(requester.id, club.id, status="pending")
        db.session.commit()

        result = delete_club(club_id, admin.id, is_site_admin=False)

        assert result["success"] is True
        assert db.session.get(Club, club_id) is None
        assert db.session.query(Member).filter_by(club_id=club_id).count() == 0
        assert db.session.query(JoinRequest).filter_by(club_id=club_id).count() == 0


def test_delete_club_cascades_legacy_requests(app):
    """Deleting a club also removes legacy Request rows."""
    with app.app_context():
        admin = make_user("dc_legacy_admin@test.com")
        outsider = make_user("dc_legacy_outsider@test.com")
        club = make_club()
        club_id = club.id
        make_member(admin.id, club.id, is_admin=True)
        make_legacy_request(outsider.id, club.id)
        db.session.commit()

        result = delete_club(club_id, admin.id, is_site_admin=False)

        assert result["success"] is True
        assert db.session.query(Request).filter_by(club_id=club_id).count() == 0


def test_delete_club_multiple_join_requests_all_statuses_cleaned_up(app):
    """Join requests in all statuses (pending, rejected, approved) are all removed."""
    with app.app_context():
        admin = make_user("dc_multi_admin@test.com")
        req1 = make_user("dc_multi_r1@test.com")
        req2 = make_user("dc_multi_r2@test.com")
        req3 = make_user("dc_multi_r3@test.com")
        club = make_club()
        club_id = club.id
        make_member(admin.id, club.id, is_admin=True)
        make_join_request(req1.id, club.id, status="pending")
        make_join_request(req2.id, club.id, status="rejected")
        make_join_request(req3.id, club.id, status="approved")
        db.session.commit()

        result = delete_club(club_id, admin.id, is_site_admin=False)

        assert result["success"] is True
        assert db.session.query(JoinRequest).filter_by(club_id=club_id).count() == 0


def test_delete_club_does_not_affect_other_clubs(app):
    """Deleting club A leaves club B and all its data intact."""
    with app.app_context():
        admin = make_user("dc_other_admin@test.com")
        other_user = make_user("dc_other_user@test.com")
        club_a = make_club("Club A")
        club_b = make_club("Club B")
        club_b_id = club_b.id
        make_member(admin.id, club_a.id, is_admin=True)
        make_member(other_user.id, club_b.id, is_admin=False)
        make_join_request(other_user.id, club_a.id, status="pending")
        db.session.commit()

        delete_club(club_a.id, admin.id, is_site_admin=False)

        assert db.session.get(Club, club_b_id) is not None
        assert db.session.query(Member).filter_by(club_id=club_b_id).count() == 1


def test_delete_club_admin_of_other_club_cannot_delete_this_club(app):
    """Being admin of club B does not grant permission to delete club A."""
    with app.app_context():
        admin = make_user("dc_wrong_admin@test.com")
        owner = make_user("dc_actual_owner@test.com")
        club_a = make_club("Club A")
        club_b = make_club("Club B")
        make_member(owner.id, club_a.id, is_admin=True)
        make_member(admin.id, club_b.id, is_admin=True)
        db.session.commit()

        result = delete_club(club_a.id, admin.id, is_site_admin=False)

        assert result["success"] is False
        assert result["error"] == "forbidden"
        assert db.session.get(Club, club_a.id) is not None


# ===========================================================================
# _auto_delete_if_no_admin
# ===========================================================================

def test_auto_delete_if_no_admin_deletes_club_with_no_members(app):
    with app.app_context():
        club = make_club()
        club_id = club.id
        db.session.commit()

        _auto_delete_if_no_admin(club_id)
        db.session.commit()

        assert db.session.get(Club, club_id) is None


def test_auto_delete_if_no_admin_deletes_club_with_only_regular_members(app):
    with app.app_context():
        user = make_user("ada_nonadmin@test.com")
        club = make_club()
        club_id = club.id
        make_member(user.id, club.id, is_admin=False)
        db.session.commit()

        _auto_delete_if_no_admin(club_id)
        db.session.commit()

        assert db.session.get(Club, club_id) is None
        assert db.session.query(Member).filter_by(club_id=club_id).count() == 0


def test_auto_delete_if_no_admin_keeps_club_with_admin(app):
    with app.app_context():
        user = make_user("ada_keep@test.com")
        club = make_club()
        club_id = club.id
        make_member(user.id, club.id, is_admin=True)
        db.session.commit()

        _auto_delete_if_no_admin(club_id)
        db.session.commit()

        assert db.session.get(Club, club_id) is not None


def test_auto_delete_if_no_admin_keeps_club_when_one_of_many_is_admin(app):
    """Club is kept if at least one member is admin, even with other non-admins."""
    with app.app_context():
        admin = make_user("ada_mixed_admin@test.com")
        regular = make_user("ada_mixed_regular@test.com")
        club = make_club()
        club_id = club.id
        make_member(admin.id, club.id, is_admin=True)
        make_member(regular.id, club.id, is_admin=False)
        db.session.commit()

        _auto_delete_if_no_admin(club_id)
        db.session.commit()

        assert db.session.get(Club, club_id) is not None


# ===========================================================================
# show_clubs
# ===========================================================================

def test_show_clubs_status_none(app):
    with app.app_context():
        user = make_user("sc_none@test.com")
        make_club("Club A")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = show_clubs()

        assert result["success"] is True
        assert result["user_club"] is None
        assert result["clubs"][0]["request_status"] == "none"
        assert result["clubs"][0]["has_pending_request"] is False


def test_show_clubs_status_member(app):
    with app.app_context():
        user = make_user("sc_member@test.com")
        club = make_club("Club B")
        make_member(user.id, club.id)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = show_clubs()

        assert result["user_club"] == club.id
        entry = next(c for c in result["clubs"] if c["id"] == club.id)
        assert entry["request_status"] == "member"
        assert entry["has_pending_request"] is False


def test_show_clubs_status_pending(app):
    with app.app_context():
        user = make_user("sc_pending@test.com")
        club = make_club("Club C")
        make_join_request(user.id, club.id, status="pending")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = show_clubs()

        entry = next(c for c in result["clubs"] if c["id"] == club.id)
        assert entry["request_status"] == "pending"
        assert entry["has_pending_request"] is True


def test_show_clubs_rejected_request_shows_as_none(app):
    """A rejected JoinRequest must not show the club as pending."""
    with app.app_context():
        user = make_user("sc_rejected@test.com")
        club = make_club("Club D")
        make_join_request(user.id, club.id, status="rejected")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = show_clubs()

        entry = next(c for c in result["clubs"] if c["id"] == club.id)
        assert entry["request_status"] == "none"
        assert entry["has_pending_request"] is False


def test_show_clubs_approved_request_with_membership_shows_as_member(app):
    """An approved JoinRequest alongside an active membership shows as 'member'."""
    with app.app_context():
        user = make_user("sc_approved@test.com")
        club = make_club("Club E")
        make_member(user.id, club.id)
        make_join_request(user.id, club.id, status="approved")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = show_clubs()

        entry = next(c for c in result["clubs"] if c["id"] == club.id)
        assert entry["request_status"] == "member"
        assert entry["has_pending_request"] is False


def test_show_clubs_mixed_statuses_across_multiple_clubs(app):
    """Each club shows the correct independent status for the same user."""
    with app.app_context():
        user = make_user("sc_mixed@test.com")
        club_member   = make_club("Member Club")
        club_pending  = make_club("Pending Club")
        club_none     = make_club("None Club")
        club_rejected = make_club("Rejected Club")

        make_member(user.id, club_member.id)
        make_join_request(user.id, club_pending.id, status="pending")
        make_join_request(user.id, club_rejected.id, status="rejected")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = show_clubs()

        by_id = {c["id"]: c for c in result["clubs"]}
        assert by_id[club_member.id]["request_status"]   == "member"
        assert by_id[club_pending.id]["request_status"]  == "pending"
        assert by_id[club_none.id]["request_status"]     == "none"
        assert by_id[club_rejected.id]["request_status"] == "none"


def test_show_clubs_user_with_no_membership_sees_all_clubs(app):
    """A user with no membership sees all clubs with status none."""
    with app.app_context():
        user = make_user("sc_all_none@test.com")
        make_club("Alpha")
        make_club("Beta")
        make_club("Gamma")
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}
            result = show_clubs()

        assert len(result["clubs"]) == 3
        assert all(c["request_status"] == "none" for c in result["clubs"])
        assert result["user_club"] is None