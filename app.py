print(">>> RUNNING THIS EXACT app.py FILE <<<")  # 🔥 PROOF LINE

from flask import Flask, request, jsonify, session, send_from_directory, abort
from flask_cors import CORS
import bcrypt
import os
from datetime import datetime
import logging
import mysql.connector
ALLOWED_ORIGINS = ["https://waterbornedisease-production.up.railway.app", "http://127.0.0.1:5000", "http://localhost:5000"]
SESSION_LIFETIME = 3600 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = "fallback-secret-key-2024"
app.config["SESSION_TYPE"] = "filesystem"
app.config["PERMANENT_SESSION_LIFETIME"] = SESSION_LIFETIME
CORS(app, supports_credentials=True, origins=ALLOWED_ORIGINS)
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="Nani1118@",    
            database="waterborne_db",
            port=3306,
            auth_plugin="mysql_native_password",
            charset="utf8mb4",
            connection_timeout=5
        )
        print(">>> DB CONNECTED INSIDE FLASK <<<")  
        return conn
    except Exception as e:
        print(">>> DB ERROR INSIDE FLASK <<<", e)
        return None
def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8")
    )
@app.route("/api/health", methods=["GET"])
def api_health():
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({
            "status": "healthy",
            "database": "disconnected",
            "timestamp": datetime.now().isoformat()
        })

@app.route("/api/register", methods=["POST"])
def register():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 503

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM users WHERE username=%s",
        (username,)
    )
    if cursor.fetchone():
        return jsonify({"error": "Username already exists"}), 400

    cursor.execute(
        """
        INSERT INTO users (username, password, role, status, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (username, hash_password(password), role, "active", datetime.now())
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True}), 201

@app.route("/api/login", methods=["POST"])
def login():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 503

    data = request.get_json()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE username=%s",
        (data.get("username"),)
    )
    user = cursor.fetchone()

    if user and verify_password(data.get("password"), user["password"]):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        return jsonify({"success": True})

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})
@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_static(path):
    full_path = os.path.join("static", path)
    if os.path.exists(full_path):
        return send_from_directory("static", path)
    return abort(404)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
