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

@app.post("/api/matches/<int:match_id>/result")
def report_match_result(match_id):
    """Report the outcome of a match and recalculate ELO ratings."""
    data = request.get_json()
    if not data or "winner_team_id" not in data:
        return jsonify({"error": "winner_team_id is required"}), 400

    winner_team_id = data["winner_team_id"]
    score_home = data.get("score_home")
    score_away = data.get("score_away")

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Verify the match exists and is in a reportable state
            cur.execute("""
                SELECT home_team_id, away_team_id
                FROM   matches
                WHERE  id = %s AND status IN ('pending', 'confirmed')
            """, (match_id,))
            match = cur.fetchone()

            if match is None:
                return jsonify({"error": "Match not found or already completed"}), 404

            home_team_id, away_team_id = match

            # Validate that the winner is actually one of the two teams
            if winner_team_id not in (home_team_id, away_team_id):
                return jsonify({"error": "winner_team_id must be the home or away team"}), 400

            # Mark the match as completed
            cur.execute("""
                UPDATE matches
                SET    status = 'completed',
                       winner_team_id = %s,
                       score_home = %s,
                       score_away = %s
                WHERE  id = %s
            """, (winner_team_id, score_home, score_away, match_id))

        conn.commit()

    # Recalculate ELO ratings and ladder ranks
    apply_match_result(match_id)

    return jsonify({"message": "Match result recorded, ratings updated"}), 200


if __name__ == "__main__":
    app.run("0.0.0.0", debug=config['debug'])