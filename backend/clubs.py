import psycopg
from flask import jsonify, request, g
from db import get_conn
from auth import token_required

def show_clubs():

    user_id = g.current_user['sub']

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id,
                       c.name,
                       c.city,
                       ARRAY_AGG(DISTINCT s.name) AS sports,
                       m.user_id
                FROM clubs c
                LEFT JOIN ladders l ON l.club_id = c.id
                LEFT JOIN sports s ON s.id = l.sport_id
                LEFT JOIN members m 
                    ON m.club_id = c.id AND m.user_id = %s
                GROUP BY c.id, c.name, c.city, m.user_id
                ORDER BY c.name
            """, (user_id,))
            #haal alle clubs met hun bijhorende informatie!
            rows = cur.fetchall()

    clubs = []
    user_club = None

    for row in rows:
        sports = []
        #haal alle sporten
        for sport in row[3]:
            if sport is not None:
                sports.append(sport)
        #zit gebruiker al in club!
        if row[4] is not None:
            user_club = row[0]
        clubs.append({
            "id": row[0],
            "name": row[1],
            "city": row[2],
            "sports": sports
        })

    return {
        "success": True,
        "clubs": clubs,
        "user_club": user_club
    }
def join_club(club_id):

    user_id = g.current_user['sub']

    with get_conn() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT id
                FROM clubs
                WHERE id = %s
            """, (club_id,))
            #bestaat club eigenlijk?
            if cur.fetchone() is None:
                return {"success": False, "error": "club_not_found"}

            cur.execute("""
                SELECT 1
                FROM members
                WHERE user_id = %s
            """, (user_id,))
            #zit user al in een club?
            if cur.fetchone():
                return {"success": False, "error": "already_in_club"}

            cur.execute("""
                INSERT INTO members (user_id, club_id)
                VALUES (%s, %s)
            """, (user_id, club_id))
            #voeg user toe aan de club
        conn.commit()

    return {"success": True, "message": "joined_club"}