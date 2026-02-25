# Water-borne Disease Monitoring System - app.py

from flask import Flask, request, jsonify, session, send_from_directory, abort
from flask_cors import CORS
import bcrypt
import os
from datetime import datetime
import logging
import mysql.connector
ALLOWED_ORIGINS = ["https://waterbornedisease-production.up.railway.app", "http://127.0.0.1:5000", "http://localhost:5000"]
SESSION_LIFETIME = 3600 

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
            auth_plugin="mysql_native_password"
        )
        return conn
    except Exception as e:
        print(">>> DB ERROR <<<", e)
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
@app.route("/api/villages", methods=["GET"])
def get_villages():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 503
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM villages")
    villages = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(villages)
def calculate_risk(village_id):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor(dictionary=True)
        # 1. Count health reports in 7 days
        cursor.execute("SELECT COUNT(*) as cases FROM health_reports WHERE village_id = %s AND report_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)", (village_id,))
        cases = cursor.fetchone()['cases']
        # 2. Check for bad water reports in 7 days
        cursor.execute("SELECT ph_level, turbidity FROM water_reports WHERE village_id = %s AND report_date >= DATE_SUB(NOW(), INTERVAL 7 DAY) ORDER BY report_date DESC LIMIT 1", (village_id,))
        water = cursor.fetchone()
        bad_water = False
        if water:
            ph, turb = float(water['ph_level']), float(water['turbidity'])
            if ph < 6.5 or ph > 8.5 or turb > 5: bad_water = True
        
        # 3. Determine Risk
        risk_level, message = None, ""
        if cases >= 7:
            risk_level = "HIGH"
            message = f"HIGH RISK: Outbreak ({cases} cases)"
            if bad_water: message += " + Poor Water detected"
            message += "."
        elif cases >= 5 and bad_water:
            risk_level, message = "HIGH", f"HIGH RISK: {cases} cases + Poor Water detected."
        elif cases >= 3:
            risk_level, message = "MEDIUM", f"MEDIUM RISK: {cases} cases reported in 7 days."
        
        if risk_level:
            # Check for existing alert of SAME risk level in last 7 days to update it instead of duplicate
            cursor.execute("SELECT id FROM alerts WHERE village_id = %s AND risk_level = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)", (village_id, risk_level))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE alerts SET message = %s, created_at = %s WHERE id = %s", (message, datetime.now(), existing['id']))
            else:
                cursor.execute("INSERT INTO alerts (village_id, risk_level, message, created_at) VALUES (%s, %s, %s, %s)", (village_id, risk_level, message, datetime.now()))
            conn.commit()
    except Exception as e: print(f"Risk Error: {e}")
    finally: conn.close()

@app.route("/api/asha/risk", methods=["GET"])
def get_asha_risk():
    v_id = session.get("village_id")
    if not v_id: return jsonify({"risk_level": "LOW", "message": "No village assigned."})
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB error"}), 503
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT risk_level, message FROM alerts WHERE village_id = %s ORDER BY created_at DESC LIMIT 1", (v_id,))
    alert = cursor.fetchone()
    conn.close()
    return jsonify(alert or {"risk_level": "LOW", "message": "No active alerts."})

@app.route("/api/reports/recent", methods=["GET"])
def get_recent_reports():
    v_id = session.get("village_id")
    if not v_id: return jsonify([])
    conn = get_db_connection()
    if not conn: return jsonify([])
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT 'health' as type, disease_type as detail, symptoms as extra, report_date FROM health_reports WHERE village_id = %s ORDER BY report_date DESC LIMIT 5", (v_id,))
    h = cursor.fetchall()
    cursor.execute("SELECT 'water' as type, CAST(ph_level AS CHAR) as detail, CAST(turbidity AS CHAR) as extra, report_date FROM water_reports WHERE village_id = %s ORDER BY report_date DESC LIMIT 5", (v_id,))
    w = cursor.fetchall()
    conn.close()
    combined = sorted(h + w, key=lambda x: x['report_date'], reverse=True)
    return jsonify(combined[:10])

@app.route("/api/admin/risk-status", methods=["GET"])
def get_admin_risk_status():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    if not conn: return jsonify([]), 503
    cursor = conn.cursor(dictionary=True)
    
    # Get all villages and their latest risk
    cursor.execute("""
        SELECT v.id as village_id, v.name as village_name, 
               (SELECT COUNT(*) FROM health_reports WHERE village_id = v.id AND report_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)) as total_cases,
               a.risk_level, a.message as reason
        FROM villages v
        LEFT JOIN (
            SELECT village_id, risk_level, message
            FROM alerts a1
            WHERE created_at = (SELECT MAX(created_at) FROM alerts a2 WHERE a2.village_id = a1.village_id)
        ) a ON v.id = a.village_id
    """)
    data = cursor.fetchall()
    conn.close()
    
    # Process defaults for villages without alerts
    for v in data:
        if not v['risk_level']:
            v['risk_level'] = 'LOW'
            v['reason'] = 'No active alerts.'
            
    return jsonify(data)

@app.route("/api/alerts", methods=["GET"])
def get_global_alerts():
    village_id = request.args.get('village_id')
    conn = get_db_connection()
    if not conn: return jsonify([])
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT a.risk_level, a.message, a.created_at, v.name as village_name
        FROM alerts a
        JOIN villages v ON a.village_id = v.id
    """
    params = []
    if village_id:
        query += " WHERE a.village_id = %s"
        params.append(village_id)
        
    query += " ORDER BY a.created_at DESC LIMIT 10"
    
    cursor.execute(query, tuple(params))
    alerts = cursor.fetchall()
    conn.close()
    return jsonify(alerts)

@app.route("/api/village/risk", methods=["GET"])
def get_village_risk():
    village_id = request.args.get('village_id')
    if not village_id:
        return jsonify({"error": "Village ID required"}), 400
        
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB error"}), 503
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT a.risk_level, a.message, a.created_at, v.name as village_name
        FROM alerts a
        JOIN villages v ON a.village_id = v.id
        WHERE a.village_id = %s
        ORDER BY a.created_at DESC LIMIT 1
    """, (village_id,))
    risk = cursor.fetchone()
    conn.close()
    
    if not risk:
        return jsonify({"risk_level": "LOW", "message": "No active alerts."})
    return jsonify(risk)

@app.route("/api/admin/disease-distribution", methods=["GET"])
def get_disease_distribution():
    conn = get_db_connection()
    if not conn: return jsonify([])
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT disease_type, COUNT(*) as count 
        FROM health_reports 
        WHERE report_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY disease_type
    """)
    dist = cursor.fetchall()
    conn.close()
    return jsonify(dist)


@app.route("/api/report/health", methods=["POST"])
def submit_health_report():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    user_id = session["user_id"]
    village_id = data.get("village_id") or session.get("village_id")
    
    if not village_id:
        return jsonify({"error": "Village ID required"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 503
        
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO health_reports (user_id, village_id, symptoms, disease_type, report_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, village_id, data.get("symptoms"), data.get("disease_type"), datetime.now()))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    calculate_risk(village_id)
    return jsonify({"success": True})

@app.route("/api/report/water", methods=["POST"])
def submit_water_report():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json()
    village_id = data.get("village_id") or session.get("village_id")
    
    if not village_id:
        return jsonify({"error": "Village ID required"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 503
        
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO water_reports (village_id, ph_level, turbidity, contamination_type, report_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (village_id, data.get("ph_level"), data.get("turbidity"), data.get("contamination_type"), datetime.now()))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    calculate_risk(village_id)
    return jsonify({"success": True})

@app.route("/api/admin/villages/update", methods=["POST"])
def update_village():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    village_id = data.get("village_id")
    new_name = data.get("new_name")
    
    if not village_id or not new_name:
        return jsonify({"error": "Missing parameters"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 503
        
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE villages SET name = %s WHERE id = %s", (new_name, village_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error updating village: {e}")
        if conn: conn.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/register", methods=["POST"])
def register():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 503

    data = request.get_json()
    logging.info(f"Registration attempt: {data}")
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")
    village_id = data.get("village_id")
    full_name = data.get("name") # Form field is 'name'
    phone_number = data.get("mobile") # Form field is 'mobile' or 'workPhone'
    
    # Handle different phone field names from different registration forms
    if not phone_number:
        phone_number = data.get("workPhone")

    # Validate role
    allowed_roles = ['asha_worker', 'volunteer', 'admin', 'patient']
    if role not in allowed_roles:
        logging.error(f"Invalid role received: {role}")
        return jsonify({"error": f"Invalid role: {role}"}), 400

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM users WHERE username=%s",
        (username,)
    )
    if cursor.fetchone():
        return jsonify({"error": "Username already exists"}), 400

    cursor.execute(
        """
        INSERT INTO users (username, password, role, village_id, full_name, phone_number, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (username, hash_password(password), role, village_id, full_name, phone_number, "active", datetime.now())
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
        session["village_id"] = user["village_id"]
        return jsonify({
            "success": True,
            "role": user["role"],
            "username": user["username"]
        })

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/admin/staff", methods=["GET"])
def get_admin_staff():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    if not conn: return jsonify([]), 503
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT u.id, u.full_name, u.phone_number, u.role, v.name as village_name
        FROM users u
        LEFT JOIN villages v ON u.village_id = v.id
        WHERE u.role IN ('asha_worker', 'volunteer')
        ORDER BY u.role, u.full_name
    """)
    staff = cursor.fetchall()
    conn.close()
    return jsonify(staff)

@app.route("/api/admin/staff/<int:user_id>", methods=["DELETE"])
def delete_staff(user_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 503

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE id = %s AND role IN ('asha_worker', 'volunteer')", (user_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Staff member not found"}), 404

    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/me", methods=["GET"])
def get_me():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB error"}), 503
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.username, u.role, u.village_id, v.name as village_name 
        FROM users u 
        LEFT JOIN villages v ON u.village_id = v.id 
        WHERE u.id = %s
    """, (session["user_id"],))
    user = cursor.fetchone()
    conn.close()
    return jsonify(user)

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/me/update-village", methods=["POST"])
def update_my_village():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    village_id = data.get("village_id")
    if not village_id:
        return jsonify({"error": "Village ID required"}), 400
        
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database unavailable"}), 503
    
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET village_id = %s WHERE id = %s", (village_id, session["user_id"]))
        conn.commit()
        session["village_id"] = village_id # Update session
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        if conn: conn.close()
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────
#  RULE-BASED CHATBOT  (read-only — never writes to DB)
# ─────────────────────────────────────────────────────────────────

def chatbot_response(user_msg: str) -> str:
    """
    Decision-support chatbot for Samaj Health Suraksha.
    Provides information on water-borne diseases, prevention,
    system usage. Does NOT diagnose or confirm outbreaks.
    """
    msg = user_msg.lower().strip()

    # ── GREETING ──────────────────────────────────────────────────
    if any(k in msg for k in ["hi", "hello", "hey", "namaste", "good morning",
                               "good afternoon", "good evening", "greet",
                               "start", "hi there", "helo", "hii"]):
        return ("👋 **Hello! I'm the Samaj Health Suraksha Support Assistant.**\n\n"
                "I can help you with:\n"
                "• 💧 Water-borne disease information (cholera, typhoid, diarrhea…)\n"
                "• 🩺 Symptoms & prevention tips\n"
                "• 📊 Village/region health report statistics\n"
                "• 🔐 How to use the system\n\n"
                "Try asking:\n"
                "*\"Health report of Gorantla region\"*\n"
                "*\"What are cholera symptoms?\"*\n"
                "*\"How to boil water safely?\"*\n\n"
                "⚠️ I provide information only — not medical diagnosis.")

    # ── DISCLAIMER / SAFETY DEFLECTION ────────────────────────────
    if any(k in msg for k in ["diagnos", "confirm outbreak", "am i sick",
                               "do i have", "treat me", "prescribe",
                               "medicine", "medication", "drug", "cure me"]):
        return ("⚠️ I'm an informational assistant only — I cannot diagnose "
                "illness or confirm outbreaks. Please consult a health "
                "administrator or visit your nearest health centre.")

    # ── DB-BACKED: village / region report lookup ─────────────────
    # Handles: "health report of gorantla region", "show reports for X village",
    # "cases in X", "data of X village", "X region report" etc.
    village_trigger = any(k in msg for k in [
        "report of", "report for", "report from", "reports of", "reports for",
        "reports from", "cases in", "cases of", "data of", "data for",
        "region report", "village report", "status of", "status for",
        "situation in", "health of", "health in", "health data",
        "show report", "show data", "show cases", "get report",
        "disease in", "disease of", "outbreak in", "outbreak of",
        "i need health", "i need report", "i want report", "give me report",
        "give data", "tell me about", "info about", "information about",
        "how is", "what is the condition", "what is happening in"
    ])
    if village_trigger:
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                # Get all villages so we can fuzzy-match the name from the message
                cursor.execute("SELECT id, name FROM villages")
                all_villages = cursor.fetchall()
                matched_village = None
                for v in all_villages:
                    if v['name'].lower() in msg:
                        matched_village = v
                        break

                if matched_village:
                    vid = matched_village['id']
                    vname = matched_village['name']
                    # Count health reports in last 7 days
                    cursor.execute("""
                        SELECT COUNT(*) as cnt FROM health_reports
                        WHERE village_id = %s AND report_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    """, (vid,))
                    week_count = cursor.fetchone()['cnt']
                    # Latest risk alert
                    cursor.execute("""
                        SELECT risk_level, message FROM alerts
                        WHERE village_id = %s ORDER BY created_at DESC LIMIT 1
                    """, (vid,))
                    alert = cursor.fetchone()
                    # Most common disease
                    cursor.execute("""
                        SELECT disease_type, COUNT(*) as cnt FROM health_reports
                        WHERE village_id = %s AND report_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                        GROUP BY disease_type ORDER BY cnt DESC LIMIT 1
                    """, (vid,))
                    top_disease = cursor.fetchone()
                    conn.close()

                    risk_level = alert['risk_level'] if alert else 'LOW'
                    risk_emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(risk_level, '🟢')
                    reply = (f"📋 **Health Report — {vname} Village:**\n\n"
                             f"{risk_emoji} **Current Risk Level:** {risk_level}\n"
                             f"📊 **Cases in last 7 days:** {week_count}\n")
                    if top_disease:
                        reply += f"🦠 **Most reported disease:** {top_disease['disease_type']} ({top_disease['cnt']} cases)\n"
                    if alert:
                        reply += f"⚠️ **Latest alert:** {alert['message']}\n"
                    if week_count == 0:
                        reply += "\n✅ No health cases reported in this village in the last 7 days."
                    else:
                        reply += f"\nThis data is updated in real time. Contact your health administrator for full records."
                    return reply
                else:
                    # No village name matched — show a list of all villages with counts
                    cursor.execute("""
                        SELECT v.name,
                            (SELECT COUNT(*) FROM health_reports h
                             WHERE h.village_id = v.id
                             AND h.report_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)) as cnt
                        FROM villages v
                        ORDER BY cnt DESC
                    """)
                    rows = cursor.fetchall()
                    conn.close()
                    if rows:
                        lines = "\n".join(
                            f"• **{r['name']}**: {r['cnt']} case(s) this week"
                            for r in rows
                        )
                        return (f"📋 **Health Reports by Village (last 7 days):**\n\n"
                                f"{lines}\n\n"
                                f"To see details for a specific village, ask:\n"
                                f"*\"Health report of [Village Name]\"*\n\n"
                                f"Available villages: {', '.join(r['name'] for r in rows)}")
                    return "No village data found at the moment. Please try again later."
        except Exception as e:
            return "I couldn't fetch village report data right now. Please try again later."

    # ── DB-BACKED: total report count ─────────────────────────────
    if any(k in msg for k in ["how many reports", "total reports", "number of reports",
                               "reports today", "reports recorded", "count reports",
                               "total cases", "how many cases", "case count",
                               "number of cases", "weekly cases", "monthly cases"]):
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM health_reports")
                total = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT COUNT(*) FROM health_reports "
                    "WHERE report_date >= DATE_SUB(NOW(), INTERVAL 1 DAY)")
                today = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT COUNT(*) FROM health_reports "
                    "WHERE report_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
                week = cursor.fetchone()[0]
                conn.close()
                return (f"📋 **Health Report Statistics:**\n\n"
                        f"• Total reports ever recorded: **{total}**\n"
                        f"• Reports in last 24 hours: **{today}**\n"
                        f"• Reports in last 7 days: **{week}**\n\n"
                        f"To see a specific village's data, ask:\n"
                        f"*\"Health report of [Village Name]\"*")
        except Exception:
            return "I couldn't fetch report data right now. Please try again later."

    # ── DB-BACKED: highest-risk / worst village ───────────────────
    if any(k in msg for k in ["which village", "highest risk", "most reports", "most cases",
                               "worst village", "risky village", "risk level",
                               "risk status", "at risk", "all villages", "list villages",
                               "village list", "show all", "overview"]):
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT v.name, COUNT(h.id) as cnt
                    FROM health_reports h
                    JOIN villages v ON h.village_id = v.id
                    WHERE h.report_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    GROUP BY v.id
                    ORDER BY cnt DESC LIMIT 5
                """)
                rows = cursor.fetchall()
                conn.close()
                if rows:
                    top = rows[0]
                    lines = "\n".join(
                        f"  {i+1}. **{r['name']}** — {r['cnt']} case(s)"
                        for i, r in enumerate(rows)
                    )
                    return (f"🔴 **Top Villages by Case Count (last 7 days):**\n\n"
                            f"{lines}\n\n"
                            f"The highest-risk village is **{top['name']}** "
                            f"with **{top['cnt']} case(s)**. "
                            f"The health administrator has been automatically alerted.")
                return "✅ No significant case clusters detected in any village in the past 7 days."
        except Exception:
            return "I couldn't fetch village risk data right now. Please try again later."

    # ── DB-BACKED: water quality reports ──────────────────────────
    if any(k in msg for k in ["water report", "water quality report", "ph level",
                               "turbidity report", "water test result",
                               "water data", "water situation"]):
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT v.name, wr.ph_level, wr.turbidity, wr.contamination_type, wr.report_date
                    FROM water_reports wr JOIN villages v ON wr.village_id = v.id
                    ORDER BY wr.report_date DESC LIMIT 5
                """)
                rows = cursor.fetchall()
                conn.close()
                if rows:
                    lines = "\n".join(
                        f"• **{r['name']}**: pH {r['ph_level']}, Turbidity {r['turbidity']} NTU"
                        + (f", Note: {r['contamination_type']}" if r['contamination_type'] else "")
                        for r in rows
                    )
                    return (f"🔬 **Latest Water Quality Reports:**\n\n"
                            f"{lines}\n\n"
                            f"Safe ranges: pH 6.5–8.5, Turbidity < 5 NTU.\n"
                            f"Volunteers submit these through their dashboard.")
                return "No water quality reports recorded yet."
        except Exception:
            return "I couldn't fetch water quality data right now. Please try again later."

    # ── DB-BACKED: ASHA worker / staff count ──────────────────────
    if any(k in msg for k in ["how many asha", "asha worker", "number of staff",
                               "staff count", "volunteer count", "total staff",
                               "how many workers", "how many volunteers"]):
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users WHERE role='asha_worker'")
                asha = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM users WHERE role='volunteer'")
                vol = cursor.fetchone()[0]
                conn.close()
                return (f"👥 **Field Staff Summary:**\n\n"
                        f"• ASHA Workers registered: **{asha}**\n"
                        f"• Volunteers registered: **{vol}**\n\n"
                        f"Administrators can view full staff details and contact information "
                        f"on the Admin Dashboard → Field Staff Directory.")
        except Exception:
            return "I couldn't fetch staff data right now. Please try again later."

    # ── DISEASES ───────────────────────────────────────────────────
    if any(k in msg for k in ["diarrhea", "diarrhoea", "loose stool",
                               "loose motion", "running stomach", "loose motions",
                               "watery stool", "dehydration"]):
        return ("💧 **Diarrhea** is one of the most common water-borne symptoms. "
                "It is caused by bacteria like E. coli or Salmonella in contaminated water.\n\n"
                "**What to do:**\n"
                "• Drink only boiled or purified water.\n"
                "• Use ORS (Oral Rehydration Solution) to prevent dehydration.\n"
                "• Report the case to your ASHA worker immediately.\n\n"
                "⚠️ This is information only — please see a doctor if symptoms persist.")

    if "cholera" in msg:
        return ("⚠️ **Cholera** is a severe water-borne disease caused by *Vibrio cholerae*.\n\n"
                "**Symptoms:** Sudden watery diarrhea, vomiting, leg cramps, dehydration.\n\n"
                "**Prevention:**\n"
                "• Drink only boiled or chlorinated water.\n"
                "• Wash hands thoroughly with soap.\n"
                "• Avoid raw/street food near water sources.\n\n"
                "If cholera is suspected, contact the health administrator immediately.")

    if "typhoid" in msg:
        return ("🌡️ **Typhoid** is caused by *Salmonella typhi* spread through contaminated "
                "food and water.\n\n"
                "**Symptoms:** High fever, headache, stomach pain, loss of appetite.\n\n"
                "**Prevention:**\n"
                "• Drink purified water.\n"
                "• Get vaccinated if available in your area.\n"
                "• Report suspected cases to your ASHA worker.")

    if any(k in msg for k in ["jaundice", "hepatitis", "yellow eye", "yellow skin",
                               "liver", "dark urine"]):
        return ("🟡 **Hepatitis A/E** can spread through contaminated drinking water.\n\n"
                "**Symptoms:** Yellow skin/eyes, fatigue, dark urine, nausea.\n\n"
                "**Prevention:**\n"
                "• Always boil drinking water.\n"
                "• Maintain good personal hygiene.\n"
                "• Vaccinations are available — ask your ASHA worker.")

    if any(k in msg for k in ["malaria", "dengue", "mosquito", "chikungunya", "stagnant water"]):
        return ("🦟 **Malaria and Dengue** are spread by mosquitoes, not directly from water, "
                "but stagnant water breeds mosquitoes.\n\n"
                "**Prevention:**\n"
                "• Drain or cover all stagnant water containers.\n"
                "• Use mosquito nets and repellents.\n"
                "• Report fever with chills to your ASHA worker promptly.")

    if any(k in msg for k in ["dysentery", "bloody stool", "blood in stool"]):
        return ("🩸 **Dysentery** is a water-borne infection causing bloody diarrhea, "
                "cramps, and fever.\n\n"
                "**What to do:**\n"
                "• Seek medical attention promptly.\n"
                "• Drink only boiled/treated water.\n"
                "• Report to your ASHA worker immediately.")

    if any(k in msg for k in ["leptospirosis", "leptospira", "rat fever", "flood fever"]):
        return ("🐀 **Leptospirosis** spreads through water contaminated with animal urine, "
                "often after flooding.\n\n"
                "**Symptoms:** Fever, headache, red eyes, muscle pain, jaundice.\n\n"
                "**Prevention:**\n"
                "• Avoid wading in floodwater.\n"
                "• Wear rubber boots in risk areas.\n"
                "• Report any suspected case to your ASHA worker.")

    if any(k in msg for k in ["symptom", "sign of", "signs of", "sick", "ill",
                               "fever", "vomit", "nausea", "cramp",
                               "stomach pain", "stomach ache", "pain", "unwell",
                               "not feeling well", "feeling sick"]):
        return ("🩺 **Common water-borne disease symptoms include:**\n"
                "• Diarrhea or loose stools\n• Vomiting and nausea\n"
                "• Fever and chills\n• Stomach cramps\n• Jaundice (yellow skin/eyes)\n"
                "• Bloody stools (dysentery)\n\n"
                "If you or someone nearby has these symptoms, please report them "
                "through the ASHA dashboard or contact your local health worker.\n\n"
                "⚠️ This is general information only — not a medical diagnosis.")

    if any(k in msg for k in ["what disease", "which disease", "list disease",
                               "waterborne disease", "water borne disease",
                               "water-borne disease", "types of disease",
                               "disease list", "disease name", "common disease"]):
        return ("🦠 **Common Water-Borne Diseases:**\n\n"
                "1. **Cholera** — severe diarrhea, vomiting\n"
                "2. **Typhoid** — high fever, stomach pain\n"
                "3. **Diarrhea (Gastroenteritis)** — loose stools, cramps\n"
                "4. **Hepatitis A/E** — jaundice, liver infection\n"
                "5. **Dysentery** — bloody diarrhea\n"
                "6. **Leptospirosis** — fever, muscle pain\n\n"
                "Ask me about any specific disease for more details.\n"
                "⚠️ If you suspect illness, contact your ASHA worker.")

    # ── WATER SAFETY ───────────────────────────────────────────────
    if any(k in msg for k in ["boil", "purif", "steriliz", "disinfect",
                               "how to purify", "make water safe", "treat water"]):
        return ("🔥 **Boiling Water Instructions:**\n"
                "1. Bring water to a rolling boil.\n"
                "2. Keep boiling for at least **1 full minute** (3 minutes at high altitudes).\n"
                "3. Let it cool in a covered, clean container.\n"
                "4. Do not touch the inside of the container.\n\n"
                "Boiling kills bacteria, viruses, and most harmful pathogens. "
                "It is the safest and cheapest method of water purification.")

    if any(k in msg for k in ["filter", "filtration", "water filter", "biosand",
                               "ceramic filter", "ro filter"]):
        return ("🌊 **Water Filtration Tips:**\n"
                "• Use a certified household filter (ceramic or biosand).\n"
                "• Change filter cartridges as instructed by the manufacturer.\n"
                "• Filtration removes suspended particles — combine with boiling or "
                "chlorination for full protection.\n\n"
                "Clean drinking water is your first defence against water-borne diseases.")

    if any(k in msg for k in ["safe water", "drink water", "drinking water", "water source",
                               "clean water", "water quality", "good water",
                               "tap water", "well water", "river water"]):
        return ("💧 **Safe Water Practices:**\n"
                "• Drink only boiled, filtered, or bottled water.\n"
                "• Store water in clean, covered containers.\n"
                "• Do not use open wells without testing.\n"
                "• Report any change in water colour/smell to your ASHA worker.\n"
                "• Wash hands before preparing food and after using the toilet.\n\n"
                "Your ASHA worker can arrange a water quality test for your village.")

    if any(k in msg for k in ["ph", "turbidity", "ntu", "water test", "test water",
                               "chlorine", "contamination"]):
        return ("🔬 **Water Quality Parameters:**\n"
                "• **pH** should be between 6.5 and 8.5 for safe drinking water.\n"
                "• **Turbidity** should be below 5 NTU (clear water).\n"
                "• **Chlorine residual** should be 0.2–0.5 mg/L for treated water.\n\n"
                "If your water looks cloudy or smells unusual, submit a Water Quality "
                "Report through the ASHA or Volunteer dashboard right away.")

    if any(k in msg for k in ["hygiene", "hand wash", "handwash", "sanitation",
                               "cleanliness", "toilet", "open defecation"]):
        return ("🧼 **Hygiene & Sanitation Tips:**\n"
                "• Wash hands with soap for at least 20 seconds.\n"
                "• Always wash before eating and after using the toilet.\n"
                "• Use proper toilets — avoid open defecation near water sources.\n"
                "• Keep food covered and cook thoroughly.\n"
                "• Dispose of garbage away from water sources.\n\n"
                "Good hygiene is the simplest way to prevent water-borne diseases.")

    # ── PREVENTION ─────────────────────────────────────────────────
    if any(k in msg for k in ["prevent", "avoid", "protect", "precaution",
                               "safety tip", "how to stay safe", "reduce risk",
                               "best practice", "recommendation"]):
        return ("🛡️ **Prevention of Water-Borne Diseases:**\n"
                "1. Drink only purified or boiled water.\n"
                "2. Wash hands with soap before meals and after toileting.\n"
                "3. Cook food thoroughly and avoid raw/unwashed vegetables.\n"
                "4. Keep water storage containers covered and clean.\n"
                "5. Drain stagnant water near your home.\n"
                "6. Report any disease symptoms to your ASHA worker early.\n\n"
                "Early reporting helps the system detect outbreaks before they spread.")

    # ── SYSTEM USAGE ───────────────────────────────────────────────
    if any(k in msg for k in ["how to report", "submit report", "report symptom",
                               "report case", "submit case", "file a report",
                               "send report", "add report", "make a report"]):
        return ("📝 **How to Submit a Health Report:**\n"
                "1. Log in as an **ASHA Worker** from the home page.\n"
                "2. Go to your **ASHA Dashboard**.\n"
                "3. Click **Submit Health Report**.\n"
                "4. Fill in: village, symptoms, and disease type.\n"
                "5. Click **Submit** — the system will automatically assess risk.\n\n"
                "Volunteers can submit **Water Quality Reports** from the Volunteer dashboard.\n"
                "Patients can log symptoms from the **Patient Portal**.")

    if any(k in msg for k in ["how to use", "what is this", "about this system",
                               "about this app", "what does this do", "explain",
                               "help me", "guide me", "tutorial", "features",
                               "what can you do", "what can this do"]):
        return ("ℹ️ **About Samaj Health Suraksha:**\n\n"
                "This is an **Early Warning System** for water-borne diseases in "
                "rural Northeast India.\n\n"
                "**Key features:**\n"
                "• 🏥 ASHA Workers submit health & water reports\n"
                "• 🧑‍🤝‍🧑 Volunteers conduct awareness campaigns\n"
                "• 🖥️ Administrators monitor village-level risk\n"
                "• 🔔 Automatic alerts when case thresholds are exceeded\n"
                "• 💬 This chatbot for disease information support\n\n"
                "**I can answer questions about:** diseases, symptoms, prevention, "
                "safe water, village reports, and system usage.")

    if any(k in msg for k in ["login", "sign in", "register", "sign up", "account",
                               "forgot password", "password", "log in", "access",
                               "how to login", "how to register"]):
        return ("🔐 **Login Information:**\n"
                "• Select your role on the home page (ASHA Worker, Volunteer, "
                "Administrator, or Patient).\n"
                "• Enter your username and password.\n"
                "• If you don't have an account, click **Register here** on the login form.\n\n"
                "For password issues, please contact your health administrator.")

    if any(k in msg for k in ["alert", "emergency", "outbreak", "danger", "critical",
                               "high risk", "warning", "notification"]):
        return ("🚨 **Alerts & Emergency Protocol:**\n"
                "The system automatically generates alerts when:\n"
                "• **3+ health cases** in a village within 7 days → Medium Risk\n"
                "• **7+ cases** or cases + poor water quality → High Risk\n\n"
                "Alerts are visible to administrators in real-time. "
                "If you notice unusual sickness in your community, report it immediately "
                "through the ASHA dashboard.\n\n"
                "⚠️ This chatbot does NOT confirm outbreaks — that is determined by "
                "health administrators reviewing system data.")

    if any(k in msg for k in ["admin", "administrator", "dashboard", "panel",
                               "control", "manage", "management"]):
        return ("🖥️ **Admin Dashboard Features:**\n"
                "• View all village risk levels at a glance\n"
                "• Monitor real-time disease alerts\n"
                "• Manage & delete field staff (ASHA workers/volunteers)\n"
                "• View disease distribution charts\n"
                "• Rename villages\n\n"
                "Access it by logging in as an **Administrator**.\n"
                "Only admin accounts can access sensitive system controls.")

    if any(k in msg for k in ["asha", "worker", "field worker", "health worker", "anm"]):
        return ("👩‍⚕️ **ASHA Workers in this system:**\n"
                "• Submit health reports for their village\n"
                "• Monitor village risk status\n"
                "• Track recent disease cases\n\n"
                "To ask how many ASHA workers are registered, ask:\n"
                "*\"How many ASHA workers are there?\"*\n\n"
                "ASHA workers are the key front-line reporters in this early warning system.")

    if any(k in msg for k in ["volunteer", "ngo"]):
        return ("🧑‍🤝‍🧑 **Volunteers in this system:**\n"
                "• Submit water quality reports (pH, turbidity, contamination)\n"
                "• Monitor village risk status\n"
                "• Conduct community awareness campaigns\n\n"
                "Volunteers log in from the home page and access their own dashboard.")

    if any(k in msg for k in ["patient", "citizen", "community member", "resident"]):
        return ("👤 **Patient / Citizen Portal:**\n"
                "• Patients can log their symptoms directly.\n"
                "• View their village's current health risk status.\n"
                "• See active health alerts in their area.\n\n"
                "Patients log in from the home page using their registered account.")

    if any(k in msg for k in ["thank", "thanks", "ok thank", "ok", "got it",
                               "understood", "noted", "great", "good", "nice",
                               "awesome", "useful", "helpful"]):
        return ("🙏 You're welcome! Remember:\n"
                "• Boil your water before drinking.\n"
                "• Report any illness symptoms to your ASHA worker.\n\n"
                "Ask me anything else about water safety or disease prevention!")

    # ── FALLBACK ──────────────────────────────────────────────────
    return ("🤔 I couldn't find a specific answer for that. Here's what I can help with:\n\n"
            "• 🦠 **Diseases**: *\"What is cholera?\"*, *\"Typhoid symptoms\"*\n"
            "• 📋 **Village reports**: *\"Health report of [Village Name]\"*\n"
            "• 📊 **Statistics**: *\"How many cases this week?\"*\n"
            "• 💧 **Water safety**: *\"How to boil water?\"*\n"
            "• 🛡️ **Prevention**: *\"How to prevent diseases?\"*\n"
            "• 🔐 **System**: *\"How to submit a report?\"*\n\n"
            "For specific medical concerns, contact your "
            "**health administrator** or call: **1800-123-4567**.")




@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Public endpoint — chatbot reads information only, never writes.
    Disclaimer: This chatbot is an informational assistant.
    It does not perform diagnosis or automated risk prediction.
    """
    data = request.get_json(silent=True) or {}
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "Please type a message first."}), 400
    if len(user_msg) > 500:
        return jsonify({"reply": "Message too long. Please keep it under 500 characters."}), 400
    reply = chatbot_response(user_msg)
    return jsonify({"reply": reply})


@app.route("/", defaults={"path": "index.html"})

@app.route("/<path:path>")
def serve_static(path):
    full_path = os.path.join("static", path)
    if os.path.exists(full_path):
        return send_from_directory("static", path)
    return abort(404)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
