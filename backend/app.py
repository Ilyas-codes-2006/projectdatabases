from flask import Flask, jsonify, request
from config import config_data as config
from db import init_db
from auth import register_user

app = Flask(__name__)

with app.app_context():
    init_db()

@app.get("/")
def root():
    return {"status": "MatchUp backend ok"}

@app.route("/api/login", methods=["POST"])
def login():
    pass

@app.route("/api/register", methods=["POST"])
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
    except Exception as e:
        # Foutafhandeling
        return jsonify({"error": str(e)}), 500

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

if __name__ == "__main__":
    app.run("0.0.0.0", debug=config['debug'])