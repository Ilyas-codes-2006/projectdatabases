from flask import Flask, jsonify
from config import config_data as config
from db import init_db

app = Flask(__name__)

with app.app_context():
    init_db()

@app.get("/")
def root():
    return {"status": "MatchUp backend ok"}

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run("0.0.0.0", debug=config['debug'])