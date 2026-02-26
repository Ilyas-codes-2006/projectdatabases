from flask import Flask, jsonify, request
from config import config_data as config
from db import init_db
from auth import register_user

def create_app(test_config=None):
    app = Flask(__name__)

    # default config
    app.config.from_mapping(
        DEBUG=config["debug"],
        DB_CONNSTR=config["db_connstr"],
    )

    # override config in tests
    if test_config:
        app.config.update(test_config)

    # initialize DB using current config
    with app.app_context():
        init_db()

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
    @app.get("/")
    def root():
        return {"status": "MatchUp backend ok"}

    @app.route("/api/login", methods=["POST"])
    def login():
        pass

    @app.route("/api/auth/register", methods=["POST"])
    def register():
        try:
            # Haal gegevens op uit de JSON-request
            data = request.json
            required_fields = ['first_name', 'last_name', 'email', 'age', 'sport', 'skill_level', 'club', 'password']
            if not data:
                return jsonify({"error": "Invalid JSON"}), 400
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing field: {field}"}), 400
        except Exception:
            return jsonify({"error": "Invalid request format"}), 400

        # Registreer de gebruiker
        result = register_user(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            age=data['age'],
            sport=data['sport'],
            skill_level=data['skill_level'],
            club=data['club'],
            password=data['password']
        )

        if result['success']:
            return jsonify({"message": "User registered successfully"}), 201
        else:
            return jsonify({"error": result['error']}), 400

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app
