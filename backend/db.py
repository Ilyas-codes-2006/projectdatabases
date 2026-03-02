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
    email = db.Column(db.VARCHAR(255), primary_key=True)

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
    set = db.Column(db.Integer, primary_key=True)
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
