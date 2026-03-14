import pytest
from sqlalchemy import text
from app import create_app
from db import db as _db, User, PasswordResetToken

TEST_DB_CONNSTR = "postgresql+psycopg://app:@localhost:5432/matchup_test"


import pytest
from app import create_app
from db import db as _db, User,Member, PasswordResetToken

TEST_DB_CONNSTR = "postgresql+psycopg://app:@localhost:5432/matchup_test"


@pytest.fixture(scope="session")
def app():
    """Maak één Flask-app aan voor de hele testsessie."""
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": TEST_DB_CONNSTR,
        "DB_CONNSTR": TEST_DB_CONNSTR,
        "MAIL_SUPPRESS_SEND": True,
    })

    with application.app_context():
        _db.drop_all()
        _db.create_all()

    yield application

    with application.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture()
def clean_users_db(app):
    """
    Leeg alle tabellen via SQLAlchemy (werkt binnen dezelfde connectie als de app).
    Wordt uitgevoerd vóór elke test die hem gebruikt.
    """
    with app.app_context():
        PasswordResetToken.query.delete()
        Member.query.delete()
        User.query.delete()
        _db.session.commit()
    yield
    # Optioneel ook na de test opruimen
    with app.app_context():
        PasswordResetToken.query.delete()
        User.query.delete()
        _db.session.commit()