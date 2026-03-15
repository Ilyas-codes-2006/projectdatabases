from db import *
from flask import g
from datetime import date, timedelta

def show_clubs():
    user_id = int(g.current_user['sub'])
    clubs = db.session.query(Club).all()
    clubs_list = []

    requests = db.session.query(Request).filter_by(user_id=user_id).all()
    requests_map = {r.club_id: r.accepted for r in requests}

    # Fetch all memberships in one query instead of one per club
    member = db.session.query(Member).filter_by(user_id=user_id).first()
    user_club = member.club_id if member else None

    for c in clubs:
        ladders = db.session.query(Ladder).filter_by(club_id=c.id).all()
        sports = [db.session.query(Sport).get(l.sport_id).name for l in ladders]

        if member and member.club_id == c.id:
            status = "member"
        elif c.id in requests_map:
            status = "pending" if not requests_map[c.id] else "accepted"
        else:
            status = "none"

        clubs_list.append({
            "id": c.id,
            "name": c.name,
            "city": c.city,
            "sports": sports,
            "request_status": status
        })

    return {
        "success": True,
        "clubs": clubs_list,
        "user_club": user_club,
    }


def join_club(club_id):
    """
    Voeg de huidige gebruiker toe aan een club. Mag alleen als die nog niet in een club zit.
    """
    user_id = int(g.current_user['sub'])  # <-- cast naar int

    # Zorg dat de club bestaat
    club = db.session.query(Club).filter_by(id=club_id).first()
    if not club:
        return {"success": False, "error": "club_not_found"}

    # Check of de gebruiker al in een club zit
    member = db.session.query(Member).filter_by(user_id=user_id).first()
    if member and member.club_id is not None:
        return {"success": False, "error": "already_in_club"}

    # Als er nog geen Member record is, maak er eentje
    if not member:
        member = Member(user_id=user_id, club_id=club_id, joined_at=date.today())
        db.session.add(member)
    else:
        member.club_id = club_id
        member.joined_at = date.today()

    db.session.commit()

    return {"success": True, "message": "joined_club"}


def request_join(club_id):
    """
    Regelt een aanvraag om een club te joinen en maakt een record aan in request.
    De club admin kan deze aanvraag vervolgens goedkeuren of afwijzen.
    """
    user_id = int(g.current_user["sub"])

    club = db.session.query(Club).filter_by(id=club_id).first()
    if not club:
        return {"success": False, "error": "club_not_found"}

    member = db.session.query(Member).filter_by(user_id=user_id, club_id=club_id).first()
    if member:
        return {"success": False, "error": "already_in_club"}

    existing_request = db.session.query(Request).filter_by(
        user_id=user_id, club_id=club_id
    ).first()

    if existing_request:
        return {"success": False, "error": "request_already_exists"}

    new_request = Request(
        user_id=user_id,
        club_id=club_id,
        expires_at=date.today() + timedelta(days=14)
    )
    db.session.add(new_request)
    db.session.commit()

    return {"success": True, "message": "join_request_created"}