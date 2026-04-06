from flask import jsonify, request, g, Blueprint
from db import *
from auth import token_required, admin_required
from clubs import _auto_delete_if_no_admin


admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/users", methods=["GET"])
@token_required
@admin_required
def list_users():
    """
    Alleen toegankelijk voor admin gebruikers. Toont een lijst van alle geregistreerde gebruikers.
    """
    print("Admin user is accessing the user list")
    users = db.session.query(
        User.id,
        User.first_name,
        User.last_name,
        User.email,
        User.date_of_birth,
        User.created_at
    ).all()

    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "date_of_birth": user.date_of_birth.isoformat(),
            "created_at": user.created_at.isoformat()
        })
    return jsonify(user_list), 200

@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@token_required
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    current_admin_id = int(g.current_user['sub'])
    if user.id == current_admin_id:
        return jsonify({"error": "You cannot delete yourself"}), 400

    user_name = f"{user.first_name} {user.last_name}"

    try:
        members = Member.query.filter_by(user_id=user_id).all()
        administered_club_ids = [m.club_id for m in members if m.is_admin and m.club_id]

        Match.query.filter_by(reported_by=user_id).update({Match.reported_by: None}, synchronize_session=False)

        db.session.delete(user)
        db.session.flush()

        for club_id in administered_club_ids:
            _auto_delete_if_no_admin(club_id)

        db.session.commit()

        return jsonify({"message": f"User {user_name} deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/users/<int:user_id>/details", methods=["GET"])
@token_required
@admin_required
def get_user_details(user_id):
    """Haal huidige club en team op van een specifieke gebruiker."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Gebruiker niet gevonden"}), 404

    member = db.session.query(Member).filter_by(user_id=user_id).first()

    club_id = None
    team_id = None

    if member:
        club_id = member.club_id
        team_member = db.session.query(TeamMember).filter_by(member_id=member.id).first()
        if team_member:
            team_id = team_member.team_id

    return jsonify({"club_id": club_id, "team_id": team_id}), 200

@admin_bp.route("/clubs", methods=["GET"])
@token_required
@admin_required
def list_all_clubs():
    """Haal alle clubs op voor de admin dropdown."""
    clubs = db.session.query(Club).all()
    return jsonify([
        {"id": c.id, "name": c.name, "city": c.city}
        for c in clubs
    ]), 200

@admin_bp.route("/teams", methods=["GET"])
@token_required
@admin_required
def list_all_teams():
    """Haal alle teams op met hun ledenaantal voor de admin dropdown."""
    teams = db.session.query(
        Team.id,
        Team.name,
        db.func.count(TeamMember.id).label("member_count")
    ).outerjoin(TeamMember, TeamMember.team_id == Team.id).group_by(Team.id).all()

    return jsonify([
        {"id": t.id, "name": t.name, "member_count": t.member_count}
        for t in teams
    ]), 200

@admin_bp.route("/users/<int:user_id>/club", methods=["PUT"])
@token_required
@admin_required
def update_user_club(user_id):
    """
    Pas de club van een gebruiker aan.
    Stuur club_id: null om de gebruiker uit zijn club te verwijderen.
    """
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Geen data meegegeven"}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Gebruiker niet gevonden"}), 404

    new_club_id = data.get("club_id")

    if new_club_id is not None:
        club = db.session.get(Club, new_club_id)
        if not club:
            return jsonify({"error": "Club niet gevonden"}), 404

    member = db.session.query(Member).filter_by(user_id=user_id).first()
    if member:
        member.club_id = new_club_id
    else:
        from datetime import date
        member = Member(user_id=user_id, club_id=new_club_id, joined_at=date.today())
        db.session.add(member)

    try:
        db.session.commit()
        return jsonify({"message": "Club succesvol bijgewerkt"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/users/<int:user_id>/team", methods=["PUT"])
@token_required
@admin_required
def update_user_team(user_id):
    """
    Pas het team van een gebruiker aan.
    Stuur team_id: null om de gebruiker uit zijn team te verwijderen.
    """
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Geen data meegegeven"}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Gebruiker niet gevonden"}), 404

    new_team_id = data.get("team_id")

    if new_team_id is not None:
        team = db.session.get(Team, new_team_id)
        if not team:
            return jsonify({"error": "Team niet gevonden"}), 404

        count = db.session.query(TeamMember).filter_by(team_id=new_team_id).count()
        if count >= 2:
            return jsonify({"error": "Dit team zit al vol (max 2 leden)"}), 400

    # Zorg dat member record bestaat
    from datetime import date
    member = db.session.query(Member).filter_by(user_id=user_id).first()
    if not member:
        if new_team_id is None:
            # No member row and no team to assign — nothing to do
            return jsonify({"message": "Team succesvol bijgewerkt"}), 200
        # Cannot assign a team without a club — admin must assign club first
        return jsonify({"error": "Gebruiker heeft nog geen club. Wijs eerst een club toe."}), 400

    # Verwijder huidig team membership
    db.session.query(TeamMember).filter_by(member_id=member.id).delete()

    # Voeg toe aan nieuw team indien opgegeven
    if new_team_id is not None:
        db.session.add(TeamMember(team_id=new_team_id, member_id=member.id))

    try:
        db.session.commit()
        return jsonify({"message": "Team succesvol bijgewerkt"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
