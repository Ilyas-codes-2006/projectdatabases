from datetime import date, datetime, timedelta
from flask import g
from db import db, User, Club, Member, Request
from clubs import leave_club, show_clubs, request_join


def test_leave_club_success(app):
    with app.app_context():
        user = User(
            first_name="A",
            last_name="B",
            email="test@example.com",
            password="hashed",
            date_of_birth=date(2000, 1, 1),
            created_at=date.today(),
        )
        club = Club(name="Test Club", city="Antwerp", created_at=datetime.now())
        db.session.add(user)
        db.session.add(club)
        db.session.commit()

        member = Member(
            user_id=user.id,
            club_id=club.id,
            joined_at=date.today(),
            is_admin=False,
            elo=0,
        )
        db.session.add(member)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}

            result = leave_club(club.id)

            assert result["success"] is True
            assert result["message"] == "left_club"

            remaining = db.session.query(Member).filter_by(
                user_id=user.id, club_id=club.id
            ).first()
            assert remaining is None



def test_leave_club_not_a_member(app):
    with app.app_context():
        user = User(
            first_name="A",
            last_name="B",
            email="test2@example.com",
            password="hashed",
            date_of_birth=date(2000, 1, 1),
            created_at=date.today(),
        )
        club = Club(name="Test Club", city="Antwerp", created_at=datetime.now())
        db.session.add(user)
        db.session.add(club)
        db.session.commit()

        with app.test_request_context():
            g.current_user = {"sub": str(user.id)}

            result = leave_club(club.id)

            assert result["success"] is False
            assert result["error"] == "not_a_member"
