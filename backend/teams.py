import psycopg
from flask import jsonify, request, g
from db import get_conn
from auth import token_required


def show_teams():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.id,
                       t.name,
                       t.rating,
                       COUNT(tm.user_id) AS member_count
                FROM teams t
                LEFT JOIN team_members tm ON tm.team_id = t.id
                WHERE t.active = TRUE
                GROUP BY t.id
                ORDER BY t.id
            """)
            rows = cur.fetchall()
    teams = []
    for row in rows:
        teams.append({
            "team_id": row[0],
            "team_name": row[1],
            "team_rating": row[2],
            "member_count": row[3]
        })
    return {"success": True, "teams": teams}

def create_team(team_name, user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM team_members
                WHERE user_id = %s
            """, (user_id,))
            if cur.fetchone():
                return {"success": False, "error": "already_in_team"}
            cur.execute("""
                SELECT id
                FROM ladders
                WHERE active = TRUE
                LIMIT 1
            """)
            ladder = cur.fetchone()
            if ladder is None:
                return {"success": False, "error": "no_active_ladder"}

            ladder_id = ladder[0]

            cur.execute("""
                INSERT INTO teams (ladder_id, name)
                VALUES (%s, %s)
                RETURNING id
            """, (ladder_id, team_name))
            team_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO team_members (team_id, user_id)
                VALUES (%s, %s)
            """, (team_id, user_id))

        conn.commit()

    return {"success": True, "message": "team_created", "team_id": team_id}

def join_team(team_id):

    user_id = g.current_user['sub']

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id
                FROM teams
                WHERE id = %s AND active = TRUE
            """, (team_id,))
            if cur.fetchone() is None:
                return {"success": False, "error": "team_not_found"}

            cur.execute("""
                SELECT 1
                FROM team_members
                WHERE user_id = %s
            """, (user_id,))
            if cur.fetchone():
                return {"success": False, "error": "already_in_team"}

            cur.execute("""
                SELECT COUNT(*)
                FROM team_members
                WHERE team_id = %s
            """, (team_id,))
            members = cur.fetchone()[0]
            if members >= 2:
                return {"success": False, "error": "team_full"}

            cur.execute("""
                INSERT INTO team_members (team_id, user_id)
                VALUES (%s, %s)
            """, (team_id, user_id))

        conn.commit()

    return {"success": True, "message": "joined_team"}