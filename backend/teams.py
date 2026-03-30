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
        Team.ladder_id,
        db.func.count(TeamMember.id).label("member_count")
    ).outerjoin(TeamMember, TeamMember.team_id == Team.id).group_by(Team.id).order_by(Team.id)

    teams = []
    for t in teams_query:
        ladder = db.session.get(Ladder, t.ladder_id)
        ladder_name = ladder.name if ladder else "Unknown"
        members_q = (
            db.session.query(Member, User)
            .join(TeamMember, TeamMember.member_id == Member.id)
            .join(User, User.id == Member.user_id)
            .filter(TeamMember.team_id == t.id)
            .all()
        )
        member_names = [f"{user.first_name} {user.last_name}" for member, user in members_q]
        teams.append({
            "team_id": t.id,
            "team_name": t.name,
            "member_count": t.member_count,
            "members": member_names,
            "ladder_name": ladder_name,
        })

    return {"success": True, "teams": teams}


def create_team(team_name, user_id, ladder_id):
    """
    Maak een nieuw team aan. De maker wordt automatisch toegevoegd als lid.
    Je mag dit alleen als je nog niet in een team zit.
    """
    user_id = int(user_id)

    #In een club?
    member = db.session.query(Member).filter_by(user_id=user_id).first()
    if not member or not member.club_id:
        return {"success": False, "error": "not_in_club"}

    ladder = db.session.get(Ladder, ladder_id)
    if not ladder:
        return {"success": False, "error": "ladder_not_found"}

    in_team_this_ladder = (
        db.session.query(TeamMember)
        .join(Team, Team.id == TeamMember.team_id)
        .filter(TeamMember.member_id == member.id, Team.ladder_id == ladder_id)
        .first()
    )
    if in_team_this_ladder:
        return {"success": False, "error": "already_in_team_in_this_ladder"}
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

    #Moet in club!
    member = db.session.query(Member).filter_by(user_id=user_id).first()
    if not member or not member.club_id:
        return {"success": False, "error": "not_in_club"}

    # Controleer of de gebruiker al in een team zit
    #member_in_team = db.session.query(TeamMember).filter_by(member_id=member.id).first()
    #if member_in_team:
    #   return {"success": False, "error": "already_in_team"}

    # Controleer of het team bestaat
    team = db.session.query(Team).filter_by(id=team_id).first()
    if not team:
        return {"success": False, "error": "team_not_found"}

    #check in de ladder die je joint
    in_team_this_ladder = (
        db.session.query(TeamMember)
        .join(Team, Team.id == TeamMember.team_id)
        .filter(TeamMember.member_id == member.id, Team.ladder_id == team.ladder_id)
        .first()
    )
    if in_team_this_ladder:
        return {"success": False, "error": "already_in_team_in_this_ladder"}

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