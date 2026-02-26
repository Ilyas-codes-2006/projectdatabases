from flask import Flask, jsonify, request
from config import config_data as config
from db import init_db, get_conn, apply_match_result

app = Flask(__name__)

with app.app_context():
    init_db()

@app.get("/")
def root():
    return {"status": "MatchUp backend ok"}

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})

MAX_MATCH_SCORE = 1000  # reasonable upper bound to prevent nonsensical scores

@app.post("/api/matches/<int:match_id>/result")
def report_match_result(match_id):
    """Report the outcome of a match and recalculate ELO ratings."""
    data = request.get_json()
    if not data or "winner_team_id" not in data:
        return jsonify({"error": "winner_team_id is required"}), 400

    winner_team_id = data["winner_team_id"]
    if not isinstance(winner_team_id, int):
        return jsonify({"error": "winner_team_id must be an integer"}), 400

    # Validate optional score fields
    raw_score_home = data.get("score_home")
    raw_score_away = data.get("score_away")
    score_home = None
    score_away = None
    max_score = MAX_MATCH_SCORE

    if raw_score_home is not None:
        try:
            score_home = int(raw_score_home)
        except (TypeError, ValueError):
            return jsonify({"error": "score_home must be an integer"}), 400
        if score_home < 0 or score_home > max_score:
            return jsonify({"error": f"score_home must be between 0 and {max_score}"}), 400

    if raw_score_away is not None:
        try:
            score_away = int(raw_score_away)
        except (TypeError, ValueError):
            return jsonify({"error": "score_away must be an integer"}), 400
        if score_away < 0 or score_away > max_score:
            return jsonify({"error": f"score_away must be between 0 and {max_score}"}), 400

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Lock the match row to prevent concurrent result submissions
            cur.execute("""
                SELECT home_team_id, away_team_id
                FROM   matches
                WHERE  id = %s AND status IN ('pending', 'confirmed')
                FOR UPDATE
            """, (match_id,))
            match = cur.fetchone()

            if match is None:
                return jsonify({"error": "Match not found or already completed"}), 404

            home_team_id, away_team_id = match

            # Validate that the winner is actually one of the two teams
            if winner_team_id not in (home_team_id, away_team_id):
                return jsonify({"error": "winner_team_id must be the home or away team"}), 400

            # Verify that both teams exist and are active
            cur.execute("""
                SELECT id, active
                FROM   teams
                WHERE  id IN (%s, %s)
            """, (home_team_id, away_team_id))
            teams = cur.fetchall()

            if len(teams) != 2:
                return jsonify({"error": "One or both teams do not exist"}), 400

            if any(not active for (_, active) in teams):
                return jsonify({"error": "Both teams must be active to report a result"}), 400

            # Mark the match as completed and update ratings in a single transaction
            cur.execute("""
                UPDATE matches
                SET    status = 'completed',
                       winner_team_id = %s,
                       score_home = %s,
                       score_away = %s
                WHERE  id = %s
            """, (winner_team_id, score_home, score_away, match_id))

            apply_match_result(match_id, cur)

        conn.commit()

    return jsonify({"message": "Match result recorded, ratings updated"}), 200


if __name__ == "__main__":
    app.run("0.0.0.0", debug=config['debug'])