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

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    token = db.Column(db.TEXT, nullable=False, unique=True)
    cexpires_at = db.Column(db.DATE, nullable=False)
    created_at = db.Column(db.DATE, nullable=False)
    used = db.Column(db.BOOLEAN, default=False)

def apply_match_result(match_id: int):
    """
    After a match is marked 'completed', update both teams' ratings
    using the simple +25/-25 system and recalculate ladder rankings.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # 1. Fetch match info + current ratings
            cur.execute("""
                SELECT m.home_team_id, m.away_team_id, m.winner_team_id,
                       th.rating AS home_rating, ta.rating AS away_rating,
                       m.ladder_id
                FROM   matches m
                JOIN   teams th ON th.id = m.home_team_id
                JOIN   teams ta ON ta.id = m.away_team_id
                WHERE  m.id = %s AND m.status = 'completed'
            """, (match_id,))
            row = cur.fetchone()
            if row is None:
                return

            home_id, away_id, winner_id, home_rating, away_rating, ladder_id = row

            # No draws
            if winner_id is None:
                return

            # 2. Determine winner/loser ratings
            if winner_id == home_id:
                winner_rating, loser_rating = home_rating, away_rating
                loser_id = away_id
            else:
                winner_rating, loser_rating = away_rating, home_rating
                loser_id = home_id

            # 3. Calculate new ratings
            new_winner_rating, new_loser_rating = calculate_elo_simple(winner_rating, loser_rating)

            # 4. Update team ratings
            cur.execute("UPDATE teams SET rating = %s WHERE id = %s", (new_winner_rating, winner_id))
            cur.execute("UPDATE teams SET rating = %s WHERE id = %s", (new_loser_rating, loser_id))

            # 5. Recalculate ranks for the entire ladder (highest rating = rank 1)
            cur.execute("""
                WITH ranked AS (
                    SELECT id, ROW_NUMBER() OVER (ORDER BY rating DESC) AS new_rank
                    FROM   teams
                    WHERE  ladder_id = %s AND active = TRUE
                )
                UPDATE teams t
                SET    rank = r.new_rank
                FROM   ranked r
                WHERE  t.id = r.id
            """, (ladder_id,))

        conn.commit()
