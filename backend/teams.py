from db import *
from flask import jsonify, g
from datetime import date


def show_teams():
    """
    Haal alle teams op met het aantal leden per team.
    """
    teams_query = db.session.query(
        Team.id,
        Team.name,
        db.func.count(TeamMember.id).label("member_count")
    ).outerjoin(TeamMember, TeamMember.team_id == Team.id).group_by(Team.id).order_by(Team.id)

    teams = []
    for t in teams_query:
        teams.append({
            "team_id": t.id,
            "team_name": t.name,
            "member_count": t.member_count
        })

    return {"success": True, "teams": teams}


def create_team(team_name, user_id):
    """
    Maak een nieuw team aan. De maker wordt automatisch toegevoegd als lid.
    Je mag dit alleen als je nog niet in een team zit.
    """
    user_id = int(user_id)

    # Controleer of de gebruiker al in een team zit
    member = db.session.query(Member).filter_by(user_id=user_id).first()
    if member:
        in_team = db.session.query(TeamMember).filter_by(member_id=member.id).first()
        if in_team:
            return {"success": False, "error": "already_in_team"}
    else:
        # Maak Member record aan als die nog niet bestaat
        member = Member(user_id=user_id, club_id=None, joined_at=date.today())
        db.session.add(member)
        db.session.commit()

    # Pak de laatste ladder als default
    ladder = db.session.query(Ladder).order_by(Ladder.id.desc()).first()
    if not ladder:
        return {"success": False, "error": "no_ladders_exist"}

    # Maak nieuw team
    new_team = Team(
        name=team_name,
        ladder_id=ladder.id,
        created_at=date.today()
    )
    db.session.add(new_team)
    db.session.commit()

    # Voeg maker toe als lid
    team_member = TeamMember(
        team_id=new_team.id,
        member_id=member.id
    )
    db.session.add(team_member)
    db.session.commit()

    return {"success": True, "message": "team_created", "team_id": new_team.id}


def join_team(team_id):
    """
    Voeg de huidige gebruiker toe aan een team (max 2 leden per team).
    Je mag dit alleen als je nog niet in een team zit.
    """
    user_id = int(g.current_user['sub'])

    # Zorg dat de gebruiker een Member record heeft
    member = db.session.query(Member).filter_by(user_id=user_id).first()
    if not member:
        member = Member(user_id=user_id, club_id=None, joined_at=date.today())
        db.session.add(member)
        db.session.commit()

    # Controleer of de gebruiker al in een team zit
    member_in_team = db.session.query(TeamMember).filter_by(member_id=member.id).first()
    if member_in_team:
        return {"success": False, "error": "already_in_team"}

    # Controleer of het team bestaat
    team = db.session.query(Team).filter_by(id=team_id).first()
    if not team:
        return {"success": False, "error": "team_not_found"}

    # Controleer of het team niet vol zit
    members_count = db.session.query(TeamMember).filter_by(team_id=team_id).count()
    if members_count >= 2:
        return {"success": False, "error": "team_full"}

    # Voeg toe
    new_member = TeamMember(
        team_id=team_id,
        member_id=member.id
    )
    db.session.add(new_member)
    db.session.commit()

    return {"success": True, "message": "joined_team"}