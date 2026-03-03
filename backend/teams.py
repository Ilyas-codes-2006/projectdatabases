import psycopg
from flask import jsonify, request, g
from db import get_conn
from auth import token_required

# ---------------------------------------------------------------------------
# TEAMS
# ---------------------------------------------------------------------------

def show_teams():
    """Show all teams"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT t.id,
                               t.name,
                               t.rating,
                               COUNT(tm.user_id) AS member_count
                        FROM teams t
                                 JOIN ladders l ON l.id = t.ladder_id
                                 JOIN sports s ON s.id = l.sport_id AND s.name = 'padel'
                                 LEFT JOIN team_members tm ON tm.team_id = t.id
                        WHERE t.active = TRUE
                        GROUP BY t.id, t.name, t.rating
                        ORDER BY t.name
                        """)
            rows = cur.fetchall()
    teams = []
    for row in rows:
        rating = row[2]
        if row[3] < 2:
            rating = None
        teams.append({
            'team_id': row[0],
            'team_name': row[1],
            'team_rating': rating,
            'member_count': row[3]
        })
    return {"success": True, "teams": teams}
def create_team(user_id, team_name):
    """Create a new team"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT 1
                        FROM team_members tm
                                 JOIN teams t ON t.id = tm.team_id
                                 JOIN ladders l ON l.id = t.ladder_id
                                 JOIN sports s ON s.id = l.sport_id AND s.name = 'padel'
                        WHERE tm.user_id = %s
                        """, (user_id,))
            AlreadyTeam = cur.fetchone()
            if AlreadyTeam is not None:
                return {"success": False, "error": "You are already in a padel team"}
            cur.execute("""
                        SELECT id
                        FROM ladders l
                                 JOIN sports s ON s.id = l.sport_id AND s.name = 'padel'
                        WHERE l.active = TRUE LIMIT 1
                        """)
            ladder_id = cur.fetchone()
            if ladder_id is None:
                return {"success": False, "error": "No active padel ladder found"}
            ladder_id = ladder_id[0]
            cur.execute("""
                        INSERT INTO teams (ladder_id, name)
                        VALUES (%s, %s) RETURNING id
                        """, (ladder_id, team_name))
            team_id = cur.fetchone()[0]
            cur.execute("""
                        INSERT INTO team_members (team_id, user_id)
                        VALUES (%s, %s)
                        """, (team_id, user_id))
        conn.commit()
    return {"success": True, "message": "Team created!", "team_id": team_id}
def join_team(user_id, team_id):
    """Join an existing padel team"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Check if team exists and is active
            cur.execute("""
                SELECT id FROM teams WHERE id = %s AND active = TRUE
            """, (team_id,))
            if cur.fetchone() is None:
                return {"success": False, "error": "Team not found"}

            # Check if user is already in a padel team
            cur.execute("""
                SELECT 1 FROM team_members tm
                JOIN teams t ON t.id = tm.team_id
                JOIN ladders l ON l.id = t.ladder_id
                JOIN sports s ON s.id = l.sport_id AND s.name = 'padel'
                WHERE tm.user_id = %s
            """, (user_id,))
            if cur.fetchone() is not None:
                return {"success": False, "error": "You are already in a padel team"}

            # Check if team is not already full
            cur.execute("""
                SELECT COUNT(*) FROM team_members WHERE team_id = %s
            """, (team_id,))
            if cur.fetchone()[0] >= 2:
                return {"success": False, "error": "This team is already full"}

            # Join the team
            cur.execute("""
                INSERT INTO team_members (team_id, user_id) VALUES (%s, %s)
            """, (team_id, user_id))
        conn.commit()
    return {"success": True, "message": "Successfully joined the team!"}