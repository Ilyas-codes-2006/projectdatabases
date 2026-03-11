import pytest
from sqlalchemy.exc import IntegrityError
from datetime import date, timedelta
from db import db, User, Club, Member, Sport, Ladder, Team, Match, Score, TeamMember

def test_unique_user_club_membership(app):
    """Test of een gebruiker maar één keer lid kan worden van dezelfde club."""
    with app.app_context():
        # 1. Setup: Maak een user en een club
        user = User(first_name="Test", last_name="User", email="test1@test.com", password="pw", date_of_birth=date(2000, 1, 1))
        club = Club(name="TC De Uithof")
        db.session.add_all([user, club])
        db.session.commit()

        # 2. Voeg het lidmaatschap toe (eerste keer moet lukken)
        member1 = Member(user_id=user.id, club_id=club.id)
        db.session.add(member1)
        db.session.commit()

        # 3. Probeer exact hetzelfde lidmaatschap nog een keer toe te voegen
        member2 = Member(user_id=user.id, club_id=club.id)
        db.session.add(member2)

        # Dit MOET een IntegrityError opleveren door onze UniqueConstraint
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback() # Rollback nodig om de sessie te herstellen voor volgende tests


def test_match_teams_cannot_be_same(app):
    """Test of een match geblokkeerd wordt als home en away team hetzelfde zijn."""
    with app.app_context():
        # Setup benodigdheden
        sport = Sport(name="Tennis", team_size=1)
        club = Club(name="TC DubbelFout")
        db.session.add_all([sport, club])
        db.session.commit()

        ladder = Ladder(sport_id=sport.id, club_id=club.id, name="Zomer", start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
        db.session.add(ladder)
        db.session.commit()

        team = Team(ladder_id=ladder.id, name="Team A")
        db.session.add(team)
        db.session.commit()

        # Probeer een match te maken met Team A tegen Team A
        match = Match(date=date.today(), home_team_id=team.id, away_team_id=team.id)
        db.session.add(match)

        # Dit MOET falen door de CheckConstraint('home_team_id != away_team_id')
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_ladder_dates_check(app):
    """Test of een ladder niet kan eindigen voordat hij is begonnen."""
    with app.app_context():
        sport = Sport(name="Padel", team_size=2)
        db.session.add(sport)
        db.session.commit()

        # End date ligt VÓÓR start date
        ladder = Ladder(
            sport_id=sport.id,
            name="Ongeldige Ladder",
            start_date=date(2024, 12, 31),
            end_date=date(2024, 1, 1) # Fout!
        )
        db.session.add(ladder)

        # Dit MOET falen door de CheckConstraint('end_date >= start_date')
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_score_cannot_be_negative(app):
    """Test of negatieve scores onmogelijk zijn."""
    with app.app_context():
        # Setup: minimal match requirements (omzeilen we even door in een match direct team id's in te vullen
        # hoewel foreign keys ons normaal dwingen teams aan te maken, voor de test doen we het netjes)
        sport = Sport(name="Squash", team_size=1)
        db.session.add(sport)
        db.session.commit()

        ladder = Ladder(sport_id=sport.id, name="SquashLadder", start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
        db.session.add(ladder)
        db.session.commit()

        team1 = Team(ladder_id=ladder.id, name="Team 1")
        team2 = Team(ladder_id=ladder.id, name="Team 2")
        db.session.add_all([team1, team2])
        db.session.commit()

        match = Match(date=date.today(), home_team_id=team1.id, away_team_id=team2.id)
        db.session.add(match)
        db.session.commit()

        # Voeg een negatieve score in
        score = Score(match_id=match.id, set=1, home_score=-1, away_score=5)
        db.session.add(score)

        # Dit MOET falen door CheckConstraint op scores >= 0
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_not_null_constraints(app):
    """Test of verplichte velden (NOT NULL) ook echt verplicht zijn."""
    with app.app_context():
        # Maak een user zonder first_name (wat nullable=False is in onze db.py)
        user = User(last_name="Doe", email="no_firstname@test.com", password="pw", date_of_birth=date(2000, 1, 1))
        db.session.add(user)

        # Dit moet direct afketsen
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()
