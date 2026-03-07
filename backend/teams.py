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
            #Houdt rekening met teams met leden en zonder leden -> de left join!
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
                SELECT *
                FROM team_members
                WHERE user_id = %s
            """, (user_id,))
            #Check of user in een team -> check of ID in team_member zit eender waar
            if cur.fetchone():
                return {"success": False, "error": "already_in_team"}
            cur.execute("""
                SELECT id
                FROM ladders
                WHERE active = TRUE
                LIMIT 1
            """)
            #check of er een ladder bestaat
            ladder = cur.fetchone()
            if ladder is None:
                return {"success": False, "error": "no_active_ladder"}

            ladder_id = ladder[0]

            cur.execute("""
                INSERT INTO teams (ladder_id, name)
                VALUES (%s, %s)
                RETURNING id
            """, (ladder_id, team_name))
            #maak nieuw team
            team_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO team_members (team_id, user_id)
                VALUES (%s, %s)
            """, (team_id, user_id))
            #voeg maker toe als lid van team!
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
            #check team bestaat
            if cur.fetchone() is None:
                return {"success": False, "error": "team_not_found"}

            cur.execute("""
                SELECT 1
                FROM team_members
                WHERE user_id = %s
            """, (user_id,))
            #check gebruiker in een team!
            if cur.fetchone():
                return {"success": False, "error": "already_in_team"}

            cur.execute("""
                SELECT COUNT(*)
                FROM team_members
                WHERE team_id = %s
            """, (team_id,))
            #tel de leden max 2!
            members = cur.fetchone()[0]
            if members >= 2:
                return {"success": False, "error": "team_full"}

            cur.execute("""
                INSERT INTO team_members (team_id, user_id)
                VALUES (%s, %s)
            """, (team_id, user_id))
            #voeg user toe aan team!
        conn.commit()

    return {"success": True, "message": "joined_team"}