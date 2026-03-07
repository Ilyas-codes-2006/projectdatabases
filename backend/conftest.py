import pytest
from sqlalchemy import text
from app import create_app
from db import db as _db, User, PasswordResetToken

TEST_DB_CONNSTR = "postgresql+psycopg://app:@localhost:5432/matchup_test"


@pytest.fixture(scope="session")
def app():
    """Maak één Flask-app aan voor de hele testsessie."""
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": TEST_DB_CONNSTR,
        "DB_CONNSTR": TEST_DB_CONNSTR,
    })

    with application.app_context():
        # DROP SCHEMA CASCADE verwijdert alle tabellen + FK-constraints in één keer,
        # zodat een stale/oude schema geen problemen geeft.
        _db.session.execute(text("DROP SCHEMA public CASCADE"))
        _db.session.execute(text("CREATE SCHEMA public"))
        _db.session.commit()
        _db.create_all()

    yield application

    # Opruimen na de sessie
    with application.app_context():
        _db.session.execute(text("DROP SCHEMA public CASCADE"))
        _db.session.execute(text("CREATE SCHEMA public"))
        _db.session.commit()


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
        # Verwijder in de juiste volgorde vanwege FK-constraints
        PasswordResetToken.query.delete()
        User.query.delete()
        _db.session.commit()
    yield
    # Optioneel ook na de test opruimen
    with app.app_context():
        PasswordResetToken.query.delete()
        User.query.delete()
        _db.session.commit()