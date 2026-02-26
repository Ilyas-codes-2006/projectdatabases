from flask import Flask, jsonify, request
from flask_cors import CORS
from config import config_data as config
from db import init_db, get_conn, apply_match_result
from auth import register_user, login_user, token_required

def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app)

    app.config.from_mapping(
        DEBUG=config["debug"],
        DB_CONNSTR=config["db_connstr"],
    )

    if test_config:
        app.config.update(test_config)

    with app.app_context():
        init_db()

    @app.get("/")
    def root():
        return {"status": "MatchUp backend ok"}

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email and password are required"}), 400

        result = login_user(data['email'], data['password'])

        if result['success']:
            return jsonify({
                "token": result['token'],
                "name": result['name'],
                "user_id": result['user_id'],
            }), 200
        else:
            return jsonify({"error": result['error']}), 401

    @app.route("/api/auth/register", methods=["POST"])
    def register():
        try:
            data = request.json
            required_fields = ['first_name', 'last_name', 'email', 'age', 'sport', 'skill_level', 'club', 'password']
            if not data:
                return jsonify({"error": "Invalid JSON"}), 400
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing field: {field}"}), 400
        except Exception:
            return jsonify({"error": "Invalid request format"}), 400

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

    @app.post("/api/matches/<int:match_id>/result")
    @token_required
    def report_match_result(match_id):
        data = request.get_json()
        if not data or "winner_team_id" not in data:
            return jsonify({"error": "winner_team_id is required"}), 400

        winner_team_id = data["winner_team_id"]
        score_home = data.get("score_home")
        score_away = data.get("score_away")

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT home_team_id, away_team_id
                    FROM   matches
                    WHERE  id = %s AND status IN ('pending', 'confirmed')
                """, (match_id,))
                match = cur.fetchone()

                if match is None:
                    return jsonify({"error": "Match not found or already completed"}), 404

                home_team_id, away_team_id = match

                if winner_team_id not in (home_team_id, away_team_id):
                    return jsonify({"error": "winner_team_id must be the home or away team"}), 400

                cur.execute("""
                    UPDATE matches
                    SET    status = 'completed',
                           winner_team_id = %s,
                           score_home = %s,
                           score_away = %s
                    WHERE  id = %s
                """, (winner_team_id, score_home, score_away, match_id))

            conn.commit()

        apply_match_result(match_id)

        return jsonify({"message": "Match result recorded, ratings updated"}), 200

    return app  # ← niet vergeten