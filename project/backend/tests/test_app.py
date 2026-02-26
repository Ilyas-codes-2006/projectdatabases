"""Unit tests for the report_match_result API endpoint."""
import sys
import os
from unittest.mock import MagicMock, patch

# Ensure backend package is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Stub out psycopg and config before importing any backend modules
_psycopg_stub = MagicMock()
sys.modules["psycopg"] = _psycopg_stub

sys.modules["config"] = MagicMock(config_data={"db_connstr": "", "debug": False})

# Now it is safe to import db and app
import db as db_module  # noqa: E402
import app as app_module  # noqa: E402

app_module.app.config["TESTING"] = True
_flask_app = app_module.app


def _client():
    return _flask_app.test_client()


# ---------------------------------------------------------------------------
# Input validation tests (no DB interaction needed)
# ---------------------------------------------------------------------------

def test_missing_winner_team_id_returns_400():
    client = _client()
    resp = client.post(
        "/api/matches/1/result",
        json={},
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert b"winner_team_id" in resp.data


def test_non_integer_winner_team_id_returns_400():
    client = _client()
    resp = client.post(
        "/api/matches/1/result",
        json={"winner_team_id": "not-an-int"},
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert b"integer" in resp.data


def test_negative_score_home_returns_400():
    client = _client()
    with patch("app.get_conn") as mock_conn:
        resp = client.post(
            "/api/matches/1/result",
            json={"winner_team_id": 1, "score_home": -1},
            content_type="application/json",
        )
    assert resp.status_code == 400
    assert b"score_home" in resp.data


def test_negative_score_away_returns_400():
    client = _client()
    resp = client.post(
        "/api/matches/1/result",
        json={"winner_team_id": 1, "score_away": -5},
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert b"score_away" in resp.data


def test_non_integer_score_home_returns_400():
    client = _client()
    resp = client.post(
        "/api/matches/1/result",
        json={"winner_team_id": 1, "score_home": "abc"},
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert b"score_home" in resp.data


# ---------------------------------------------------------------------------
# DB-level tests (cursor mocked)
# ---------------------------------------------------------------------------

def _mock_conn_context(cur_mock):
    """Return a mock context manager that yields a connection with cur_mock."""
    conn_mock = MagicMock()
    conn_mock.__enter__ = MagicMock(return_value=conn_mock)
    conn_mock.__exit__ = MagicMock(return_value=False)
    cursor_ctx = MagicMock()
    cursor_ctx.__enter__ = MagicMock(return_value=cur_mock)
    cursor_ctx.__exit__ = MagicMock(return_value=False)
    conn_mock.cursor.return_value = cursor_ctx
    return conn_mock


def test_match_not_found_returns_404():
    client = _client()
    cur = MagicMock()
    cur.fetchone.return_value = None  # match not found
    conn = _mock_conn_context(cur)

    with patch("app.get_conn", return_value=conn):
        resp = client.post(
            "/api/matches/99/result",
            json={"winner_team_id": 1},
            content_type="application/json",
        )
    assert resp.status_code == 404


def test_wrong_winner_team_returns_400():
    client = _client()
    cur = MagicMock()
    # match found with teams 10 and 20
    cur.fetchone.return_value = (10, 20)
    conn = _mock_conn_context(cur)

    with patch("app.get_conn", return_value=conn):
        resp = client.post(
            "/api/matches/1/result",
            json={"winner_team_id": 99},
            content_type="application/json",
        )
    assert resp.status_code == 400
    assert b"home or away" in resp.data


def test_inactive_team_returns_400():
    client = _client()
    cur = MagicMock()
    # First fetchone: match found
    # fetchall: teams, one inactive
    cur.fetchone.return_value = (10, 20)
    cur.fetchall.return_value = [(10, True), (20, False)]
    conn = _mock_conn_context(cur)

    with patch("app.get_conn", return_value=conn):
        resp = client.post(
            "/api/matches/1/result",
            json={"winner_team_id": 10},
            content_type="application/json",
        )
    assert resp.status_code == 400
    assert b"active" in resp.data


def test_missing_team_returns_400():
    client = _client()
    cur = MagicMock()
    cur.fetchone.return_value = (10, 20)
    cur.fetchall.return_value = [(10, True)]  # only one team found
    conn = _mock_conn_context(cur)

    with patch("app.get_conn", return_value=conn):
        resp = client.post(
            "/api/matches/1/result",
            json={"winner_team_id": 10},
            content_type="application/json",
        )
    assert resp.status_code == 400
    assert b"do not exist" in resp.data


def test_successful_result_returns_200():
    client = _client()
    cur = MagicMock()
    cur.fetchone.return_value = (10, 20)
    cur.fetchall.return_value = [(10, True), (20, True)]
    conn = _mock_conn_context(cur)

    with patch("app.get_conn", return_value=conn), \
         patch("app.apply_match_result") as mock_apply:
        resp = client.post(
            "/api/matches/1/result",
            json={"winner_team_id": 10},
            content_type="application/json",
        )
    assert resp.status_code == 200
    mock_apply.assert_called_once()
