from db import *
from flask import g
from datetime import date, timedelta
from flask_mail import Message


def request_new_club(club_name: str, city: str, motivation: str, attachments: list, mail_instance):
    """
    Slaat een club-aanvraag op en stuurt een verificatie-email naar alle admins.
    attachments: lijst van {filename, mimetype, data_b64}
    """
    import json, base64 as b64mod

    user_id = int(g.current_user['sub'])
    user = db.session.get(User, user_id)
    if not user:
        return {"success": False, "error": "user_not_found"}

    club_req = ClubRequest(
        user_id=user_id,
        club_name=club_name,
        city=city,
        motivation=motivation or "",
        status='pending',
        created_at=date.today(),
        attachments=json.dumps(attachments) if attachments else None,
    )
    db.session.add(club_req)
    db.session.commit()

    admins = db.session.query(User).filter_by(is_admin=True).all()
    admin_emails = [a.email for a in admins]

    if admin_emails:
        from config import config_data as config
        msg = Message(
            subject=f"[MatchUp] Nieuwe club-aanvraag: {club_name}",
            sender=config['mail_sender'],
            recipients=admin_emails
        )
        msg.body = f"""Hallo Admin,

{user.first_name} {user.last_name} ({user.email}) heeft een aanvraag ingediend om een nieuwe club aan te maken.

Details van de aanvraag (ID #{club_req.id}):
  • Clubnaam  : {club_name}
  • Stad      : {city}
  • Motivatie : {motivation or '(geen motivatie opgegeven)'}
  • Bijlagen  : {len(attachments)} bestand(en)
  • Aangevraagd op: {date.today().isoformat()}

Gelieve deze aanvraag te beoordelen en de club goed te keuren of af te wijzen via het admin-paneel.

— Het MatchUp systeem
"""
        for att in attachments:
            try:
                file_bytes = b64mod.b64decode(att["data_b64"])
                msg.attach(att["filename"], att["mimetype"], file_bytes)
            except Exception:
                pass

        mail_instance.send(msg)

    return {"success": True, "message": "club_request_submitted", "request_id": club_req.id}


def review_club_request(request_id: int, action: str, mail_instance):
    """
    Admin keurt een club-aanvraag goed of af.
    Bij goedkeuring wordt de club aangemaakt en de aanvrager lid gemaakt.
    """
    from config import config_data as config

    club_req = db.session.get(ClubRequest, request_id)
    if not club_req:
        return {"success": False, "error": "request_not_found"}
    if club_req.status != 'pending':
        return {"success": False, "error": "request_already_reviewed"}

    user = db.session.get(User, club_req.user_id)
    if not user:
        return {"success": False, "error": "user_not_found"}

    if action == "approve":
        new_club = Club(name=club_req.club_name, city=club_req.city, created_at=date.today())
        db.session.add(new_club)
        db.session.flush()

        existing_member = db.session.query(Member).filter_by(user_id=user.id).first()
        if not existing_member:
            member = Member(user_id=user.id, club_id=new_club.id, joined_at=date.today(), is_admin=True)
            db.session.add(member)
        else:
            existing_member.club_id = new_club.id
            existing_member.is_admin = True

        club_req.status = 'approved'
        db.session.commit()

        msg = Message(
            subject="[MatchUp] Je club-aanvraag is goedgekeurd!",
            sender=config['mail_sender'],
            recipients=[user.email]
        )
        msg.body = f"""Hallo {user.first_name},

Goed nieuws! Je aanvraag om de club "{club_req.club_name}" in {club_req.city} aan te maken is goedgekeurd.

Je bent automatisch toegevoegd als lid en clubbeheerder.

Veel plezier bij MatchUp!

— Het MatchUp Team
"""
        mail_instance.send(msg)

    else:  # reject
        club_req.status = 'rejected'
        db.session.commit()

        msg = Message(
            subject="[MatchUp] Je club-aanvraag werd niet goedgekeurd",
            sender=config['mail_sender'],
            recipients=[user.email]
        )
        msg.body = f"""Hallo {user.first_name},

Helaas is je aanvraag om de club "{club_req.club_name}" aan te maken niet goedgekeurd door een admin.

Heb je vragen? Neem contact op met ons via {config['mail_sender']}.

— Het MatchUp Team
"""
        mail_instance.send(msg)

    return {"success": True, "action": action}


def show_clubs():
    user_id = int(g.current_user["sub"])
    clubs = db.session.query(Club).all()
    clubs_list = []

    members = db.session.query(Member).filter_by(user_id=user_id).all()
    member_club_ids = {m.club_id for m in members}

    user_club = None
    for club_id in member_club_ids:
        user_club = club_id
        break

    for c in clubs:
        ladders = db.session.query(Ladder).filter_by(club_id=c.id).all()
        sports = [db.session.query(Sport).get(l.sport_id).name for l in ladders]

        is_member = c.id in member_club_ids

        # Check pending JoinRequest
        pending_req = db.session.query(JoinRequest).filter_by(
            user_id=user_id, club_id=c.id, status='pending'
        ).first()

        if is_member:
            status = "member"
        elif pending_req:
            status = "pending"
        else:
            status = "none"

        clubs_list.append({
            "id": c.id,
            "name": c.name,
            "city": c.city,
            "sports": sports,
            "request_status": status,
            "has_pending_request": pending_req is not None,
        })

    return {
        "success": True,
        "clubs": clubs_list,
        "user_club": user_club,
    }


def request_join(club_id):
    """
    Eenvoudige join-aanvraag via de Request tabel (legacy).
    """
    user_id = int(g.current_user["sub"])

    club = db.session.query(Club).filter_by(id=club_id).first()
    if not club:
        return {"success": False, "error": "club_not_found"}

    existing_membership = db.session.query(Member).filter_by(
        user_id=user_id, club_id=club_id
    ).first()
    if existing_membership:
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


def request_join_club(club_id: int, motivation: str, mail_instance):
    """
    Stuurt een join-aanvraag naar de club admin via e-mail (JoinRequest tabel).
    """
    from config import config_data as config

    user_id = int(g.current_user['sub'])
    user = db.session.get(User, user_id)
    if not user:
        return {"success": False, "error": "user_not_found"}

    club = db.session.get(Club, club_id)
    if not club:
        return {"success": False, "error": "club_not_found"}

    existing_member = db.session.query(Member).filter_by(user_id=user_id, club_id=club_id).first()
    if existing_member:
        return {"success": False, "error": "already_member"}

    existing_req = db.session.query(JoinRequest).filter_by(
        user_id=user_id, club_id=club_id, status='pending'
    ).first()
    if existing_req:
        return {"success": False, "error": "request_already_pending"}

    join_req = JoinRequest(
        user_id=user_id,
        club_id=club_id,
        motivation=motivation or "",
        status='pending',
        created_at=date.today(),
    )
    db.session.add(join_req)
    db.session.commit()

    club_admins = db.session.query(User).join(
        Member, Member.user_id == User.id
    ).filter(Member.club_id == club_id, Member.is_admin == True).all()

    admin_emails = [a.email for a in club_admins]
    if admin_emails:
        msg = Message(
            subject=f"[MatchUp] Nieuwe lid-aanvraag voor {club.name}",
            sender=config['mail_sender'],
            recipients=admin_emails,
        )
        msg.body = f"""Hallo Club Admin,

{user.first_name} {user.last_name} ({user.email}) wil lid worden van jouw club "{club.name}".

Motivatie: {motivation or '(geen motivatie opgegeven)'}

Bekijk en beoordeel de aanvraag via het 'My Club' paneel op MatchUp.

— Het MatchUp systeem
"""
        mail_instance.send(msg)

    return {"success": True, "message": "join_request_submitted"}


def review_join_request(join_request_id: int, action: str, mail_instance):
    """
    Club admin keurt een lid-aanvraag goed of af.
    """
    from config import config_data as config

    user_id = int(g.current_user['sub'])

    join_req = db.session.get(JoinRequest, join_request_id)
    if not join_req:
        return {"success": False, "error": "request_not_found"}

    admin_member = db.session.query(Member).filter_by(
        user_id=user_id, club_id=join_req.club_id, is_admin=True
    ).first()
    if not admin_member:
        return {"success": False, "error": "forbidden"}

    if join_req.status != 'pending':
        return {"success": False, "error": "request_already_reviewed"}

    requester = db.session.get(User, join_req.user_id)
    club = db.session.get(Club, join_req.club_id)

    if action == "approve":
        existing = db.session.query(Member).filter_by(user_id=join_req.user_id).first()
        if not existing:
            new_member = Member(
                user_id=join_req.user_id,
                club_id=join_req.club_id,
                joined_at=date.today(),
                is_admin=False,
            )
            db.session.add(new_member)
        else:
            existing.club_id = join_req.club_id
            existing.is_admin = False

        join_req.status = 'approved'
        db.session.commit()

        if requester:
            msg = Message(
                subject=f"[MatchUp] Je bent toegelaten tot {club.name}!",
                sender=config['mail_sender'],
                recipients=[requester.email],
            )
            msg.body = f"""Hallo {requester.first_name},

Goed nieuws! De club admin van "{club.name}" heeft je aanvraag goedgekeurd.
Je bent nu officieel lid van de club.

Veel plezier bij MatchUp!

— Het MatchUp Team
"""
            mail_instance.send(msg)

    else:  # reject
        join_req.status = 'rejected'
        db.session.commit()

        if requester:
            msg = Message(
                subject=f"[MatchUp] Je aanvraag voor {club.name} werd afgewezen",
                sender=config['mail_sender'],
                recipients=[requester.email],
            )
            msg.body = f"""Hallo {requester.first_name},

Helaas heeft de club admin van "{club.name}" je aanvraag niet goedgekeurd.

Heb je vragen? Neem contact op via {config['mail_sender']}.

— Het MatchUp Team
"""
            mail_instance.send(msg)

    return {"success": True, "action": action}


def join_club(club_id):
    """
    Voeg de huidige gebruiker direct toe aan een club.
    """
    user_id = int(g.current_user['sub'])

    club = db.session.query(Club).filter_by(id=club_id).first()
    if not club:
        return {"success": False, "error": "club_not_found"}

    member = db.session.query(Member).filter_by(user_id=user_id).first()
    if member and member.club_id is not None:
        return {"success": False, "error": "already_in_club"}

    if not member:
        member = Member(user_id=user_id, club_id=club_id, joined_at=date.today())
        db.session.add(member)
    else:
        member.club_id = club_id
        member.joined_at = date.today()

    db.session.commit()
    return {"success": True, "message": "joined_club"}


def leave_club(club_id):
    """
    Laat de huidige gebruiker een club verlaten.
    """
    user_id = int(g.current_user["sub"])

    member = db.session.query(Member).filter_by(user_id=user_id, club_id=club_id).first()
    if not member:
        return {"success": False, "error": "not_a_member"}

    db.session.delete(member)
    db.session.commit()

    return {"success": True, "message": "left_club"}