from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy.sql import func
from elo import calculate_elo_simple

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.VARCHAR(255), nullable=False)
    first_name = db.Column(db.VARCHAR(255), nullable=False)
    password = db.Column(db.VARCHAR(255), nullable=False)
    bio = db.Column(db.VARCHAR(255))
    photo_url = db.Column(db.VARCHAR(500), default='')
    is_admin = db.Column(db.BOOLEAN, default=False)
    date_of_birth = db.Column(db.DATE, nullable=False)
    created_at = db.Column(db.DATE, nullable=False, default=func.current_date())
    email = db.Column(db.VARCHAR(255), unique=True, nullable=False)

class Club(db.Model):
    __tablename__ = 'club'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(255), nullable=False)
    city = db.Column(db.VARCHAR(255))
    created_at = db.Column(db.DATE, nullable=False, default=func.current_date())

class Member(db.Model):
    __tablename__ = 'member'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    joined_at = db.Column(db.DATE, nullable=False, default=func.current_date())
    is_admin = db.Column(db.BOOLEAN, default=False)
    elo = db.Column(db.INTEGER, default=0)

    __table_args__ = (
        UniqueConstraint('user_id', 'club_id', name='uq_user_club_membership'),
    )

class Sport(db.Model):
    __tablename__ = 'sport'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(255), nullable=False)
    team_size = db.Column(db.Integer, nullable=False)

class Ladder(db.Model):
    __tablename__ = 'ladder'
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(db.Integer, db.ForeignKey('sport.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'))
    name = db.Column(db.VARCHAR(255), nullable=False)
    start_date = db.Column(db.DATE, nullable=False)
    end_date = db.Column(db.DATE, nullable=False)
    rules = db.Column(db.TEXT)
    challenge_limit = db.Column(db.Integer)

    __table_args__ = (
        CheckConstraint('end_date >= start_date', name='check_ladder_dates'),
    )

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    ladder_id = db.Column(db.Integer, db.ForeignKey('ladder.id'), nullable=False)
    name = db.Column(db.VARCHAR(255), nullable=False)
    created_at = db.Column(db.DATE, nullable=False, default=func.current_date())

class TeamMember(db.Model):
    __tablename__ = 'team_member'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', name='uq_team_user'),
    )

class Availability(db.Model):
    __tablename__ = 'availability'
    team_member_id = db.Column(db.Integer, db.ForeignKey('team_member.id'), primary_key=True)
    date = db.Column(db.DATE, nullable=False, primary_key=True)
    is_available = db.Column(db.BOOLEAN, default=False)

class Match(db.Model):
    __tablename__ = 'match'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DATE, nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    cancelled = db.Column(db.BOOLEAN, default=False)

    __table_args__ = (
        CheckConstraint('home_team_id != away_team_id', name='check_teams_not_same'),
    )

class Score(db.Model):
    __tablename__ = 'score'
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), primary_key=True)
    set = db.Column(db.Integer, primary_key=True)
    home_score = db.Column(db.Integer, nullable=False)
    away_score = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        CheckConstraint('home_score >= 0 AND away_score >= 0', name='check_positive_scores'),
    )

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_token'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.TEXT, nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False) # Typfout gecorrigeerd
    created_at = db.Column(db.DATE, nullable=False, default=func.current_date())
    used = db.Column(db.BOOLEAN, default=False)

class Request(db.Model):
    __tablename__ = 'request'
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), primary_key=True) # ForeignKey toegevoegd
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True) # ForeignKey toegevoegd
    expires_at = db.Column(db.DateTime, nullable=False)
    accepted = db.Column(db.BOOLEAN, default=False) # Naam gelijkgetrokken met ER-diagram

class ClubRequest(db.Model):
    __tablename__ = 'club_request'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    club_name = db.Column(db.VARCHAR(255), nullable=False)
    city = db.Column(db.VARCHAR(255), nullable=False)
    motivation = db.Column(db.TEXT)
    status = db.Column(db.VARCHAR(50), nullable=False, default='pending')  # pending / approved / rejected
    created_at = db.Column(db.DATE, nullable=False, default=func.current_date())
    # JSON list of {filename, mimetype, data_b64}
    attachments = db.Column(db.TEXT, nullable=True)

class JoinRequest(db.Model):
    """A user requesting to join an existing club."""
    __tablename__ = 'join_request'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    motivation = db.Column(db.TEXT)
    status = db.Column(db.VARCHAR(50), nullable=False, default='pending')  # pending / approved / rejected
    created_at = db.Column(db.DATE, nullable=False, default=func.current_date())

    __table_args__ = (
        UniqueConstraint('user_id', 'club_id', name='uq_join_request_user_club'),
    )

def apply_match_result(match_id: int):
    """
    Verwerkt het resultaat van een afgeronde match op basis van de individuele ELO van de spelers.
    """
    match = Match.query.get(match_id)
    if not match:
        return

    # Haal alle scores op voor deze specifieke match
    scores = Score.query.filter_by(match_id=match.id).all()
    if not scores:
        return

    # Bereken de totale score over alle sets om een winnaar te bepalen
    home_total = sum(s.home_score for s in scores)
    away_total = sum(s.away_score for s in scores)

    # 1. Bepaal winnend en verliezend team ID
    if home_total > away_total:
        winner_team_id = match.home_team_id
        loser_team_id = match.away_team_id
    elif away_total > home_total:
        winner_team_id = match.away_team_id
        loser_team_id = match.home_team_id
    else:
        # Gelijkspel afhandeling indien nodig (nu overgeslagen)
        return

    # 2. Haal de leden van beide teams op via de koppeltabel TeamMember
    winner_members = Member.query.join(TeamMember).filter(TeamMember.team_id == winner_team_id).all()
    loser_members = Member.query.join(TeamMember).filter(TeamMember.team_id == loser_team_id).all()

    if not winner_members or not loser_members:
        return

    # 3. Bereken het gemiddelde ELO per team vóór de wedstrijd
    winner_avg_elo = sum(m.elo for m in winner_members) / len(winner_members)
    loser_avg_elo = sum(m.elo for m in loser_members) / len(loser_members)

    # 4. Bereken nieuwe ELO met jouw elo-functie
    new_winner_avg_elo, new_loser_avg_elo = calculate_elo_simple(winner_avg_elo, loser_avg_elo)

    # 5. Bereken hoeveel punten er gewonnen of verloren zijn
    winner_delta = new_winner_avg_elo - winner_avg_elo
    loser_delta = new_loser_avg_elo - loser_avg_elo

    # 6. Pas de puntenwijziging toe op de individuele leden
    for m in winner_members:
        m.elo = int(m.elo + winner_delta)

    for m in loser_members:
        m.elo = int(m.elo + loser_delta)

    db.session.commit()