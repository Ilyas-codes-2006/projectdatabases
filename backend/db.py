from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from elo import calculate_elo_simple

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.VARCHAR(255))
    first_name = db.Column(db.VARCHAR(255))
    password = db.Column(db.VARCHAR(255))
    bio = db.Column(db.VARCHAR(255))
    is_admin = db.Column(db.BOOLEAN, default=False)
    date_of_birth = db.Column(db.DATE, nullable=False)
    created_at = db.Column(db.DATE, nullable=False)
    email = db.Column(db.VARCHAR(255), unique=True)

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(255))
    city = db.Column(db.VARCHAR(255))
    created_at = db.Column(db.DATE, nullable=False)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    club_id = db.Column(db.Integer, db.ForeignKey(Club.id))
    joined_at = db.Column(db.DATE, nullable=False)
    is_admin = db.Column(db.BOOLEAN, default=False)
    elo = db.Column(db.INTEGER, default=0)

class Sport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(255))
    team_size = db.Column(db.Integer)

class Ladder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(db.Integer, db.ForeignKey(Sport.id))
    club_id = db.Column(db.Integer, db.ForeignKey(Club.id))
    name = db.Column(db.VARCHAR(255))
    start_date = db.Column(db.DATE, nullable=False)
    end_date = db.Column(db.DATE, nullable=False)
    rules = db.Column(db.TEXT)
    challenge_limit = db.Column(db.Integer)

class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DATE, nullable=False)
    is_available = db.Column(db.BOOLEAN, default=False)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ladder_id = db.Column(db.Integer, db.ForeignKey(Ladder.id))
    name = db.Column(db.VARCHAR(255))
    created_at = db.Column(db.DATE, nullable=False)
    availability = db.Column(db.Integer, db.ForeignKey(Availability.id))

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    set = db.Column(db.Integer, unique=True)
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DATE, nullable=False)
    result = db.Column(db.Integer, db.ForeignKey(Score.id))
    ladder_id = db.Column(db.Integer, db.ForeignKey(Ladder.id))
    home_team_id = db.Column(db.Integer, db.ForeignKey(Team.id))
    away_team_id = db.Column(db.Integer, db.ForeignKey(Team.id))
    reported_by = db.Column(db.Integer, db.ForeignKey(User.id))

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey(Team.id))
    member_id = db.Column(db.Integer, db.ForeignKey(Member.id))

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    token = db.Column(db.TEXT, nullable=False, unique=True)
    cexpires_at = db.Column(db.DATE, nullable=False)
    created_at = db.Column(db.DATE, nullable=False)
    used = db.Column(db.BOOLEAN, default=False)

def apply_match_result(match_id: int):
    """
    Verwerkt het resultaat van een afgeronde match op basis van de individuele ELO van de spelers.
    """
    match = Match.query.get(match_id)
    
    if not match or not match.result:
        return

    score = Score.query.get(match.result)
    if not score or score.home_score is None or score.away_score is None:
        return

    # 1. Bepaal winnend en verliezend team ID
    if score.home_score > score.away_score:
        winner_team_id = match.home_team_id
        loser_team_id = match.away_team_id
    elif score.away_score > score.home_score:
        winner_team_id = match.away_team_id
        loser_team_id = match.home_team_id
    else:
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
