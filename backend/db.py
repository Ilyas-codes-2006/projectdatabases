import psycopg
from config import config_data as config
from elo import calculate_elo_simple
from flask import current_app

def get_conn():
    return psycopg.connect(current_app.config["DB_CONNSTR"])

def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id            SERIAL PRIMARY KEY,
        first_name    VARCHAR(100) NOT NULL,
        last_name     VARCHAR(100) NOT NULL,
        email         VARCHAR(255) NOT NULL UNIQUE,
        age           INTEGER NOT NULL,
        sport         VARCHAR(20) NOT NULL CHECK (sport IN ('tennis', 'padel', 'both')),
        skill_level   VARCHAR(20) NOT NULL CHECK (skill_level IN ('beginner', 'intermediate', 'advanced', 'competitive', 'professional')),
        club          VARCHAR(100) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        is_admin      BOOLEAN NOT NULL DEFAULT FALSE,
        elo           INTEGER NOT NULL DEFAULT 1200,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS clubs (
        id         SERIAL PRIMARY KEY,
        name       VARCHAR(100) NOT NULL UNIQUE,
        city       VARCHAR(100),
        created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS members (
        user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        club_id   INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
        is_admin  BOOLEAN NOT NULL DEFAULT FALSE,
        joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (user_id, club_id)
    );

    CREATE TABLE IF NOT EXISTS sports (
        id        SERIAL PRIMARY KEY,
        name      VARCHAR(50) NOT NULL UNIQUE,
        team_size INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS ladders (
        id                   SERIAL PRIMARY KEY,
        club_id              INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
        sport_id             INTEGER NOT NULL REFERENCES sports(id),
        name                 VARCHAR(100) NOT NULL,
        challenge_limit      INTEGER NOT NULL DEFAULT 3,
        scheduling_freq_days INTEGER NOT NULL DEFAULT 14,
        k_factor             INTEGER NOT NULL DEFAULT 32,
        active               BOOLEAN NOT NULL DEFAULT TRUE,
        created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS teams (
        id         SERIAL PRIMARY KEY,
        ladder_id  INTEGER NOT NULL REFERENCES ladders(id) ON DELETE CASCADE,
        name       VARCHAR(100) NOT NULL,
        rating     INTEGER NOT NULL DEFAULT 1200,
        rank       INTEGER,
        active     BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS team_members (
        team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        PRIMARY KEY (team_id, user_id)
    );

    CREATE TABLE IF NOT EXISTS team_availability (
        team_id     INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
        day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
        PRIMARY KEY (team_id, day_of_week)
    );

    CREATE TABLE IF NOT EXISTS matches (
        id             SERIAL PRIMARY KEY,
        ladder_id      INTEGER NOT NULL REFERENCES ladders(id) ON DELETE CASCADE,
        home_team_id   INTEGER NOT NULL REFERENCES teams(id),
        away_team_id   INTEGER NOT NULL REFERENCES teams(id),
        scheduled_at   TIMESTAMPTZ,
        status         VARCHAR(20) NOT NULL DEFAULT 'pending'
                           CHECK (status IN ('pending','confirmed','completed','declined','disputed')),
        winner_team_id INTEGER REFERENCES teams(id),
        score_home     VARCHAR(50),
        score_away     VARCHAR(50),
        reported_by    INTEGER REFERENCES users(id),
        created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    -- Tabel voor wachtwoord-reset tokens
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id         SERIAL PRIMARY KEY,
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token      TEXT NOT NULL UNIQUE,
        expires_at TIMESTAMPTZ NOT NULL,
        used       BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(schema)
        conn.commit()
    print("[db] Schema initialized.")


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