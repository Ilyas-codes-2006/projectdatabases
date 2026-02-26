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