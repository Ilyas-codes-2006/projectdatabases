import pytest
import psycopg
from app import create_app

TEST_DB_CONNSTR = "postgresql://app:@localhost:5432/matchup_test"

@pytest.fixture()
def db_conn():
    conn = psycopg.connect(TEST_DB_CONNSTR)
    conn.autocommit = False
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()

@pytest.fixture()
def clean_users_db():
    with psycopg.connect(TEST_DB_CONNSTR) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
        conn.commit()

@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "DB_CONNSTR": TEST_DB_CONNSTR
    })

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()