from db import db, Club, Member, Ladder, Sport
from flask import g
from datetime import date

def show_clubs():
    user_id = int(g.current_user['sub'])  # <-- cast naar int
    clubs = db.session.query(Club).all()
    clubs_list = []

    user_club = None
    for c in clubs:
        # Haal ladder/sport info
        ladders = db.session.query(Ladder).filter_by(club_id=c.id).all()
        sports = [db.session.query(Sport).get(l.sport_id).name for l in ladders]

        # Check of gebruiker lid is
        is_member = db.session.query(Member).filter_by(user_id=user_id, club_id=c.id).first()
        if is_member:
            user_club = c.id

        clubs_list.append({
            "id": c.id,
            "name": c.name,
            "city": c.city,
            "sports": sports
        })

    return {
        "success": True,
        "clubs": clubs_list,
        "user_club": user_club
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