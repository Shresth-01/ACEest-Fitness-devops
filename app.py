import os
import sqlite3
from datetime import date, datetime
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["DATABASE"] = os.environ.get("DB_NAME", "aceest_fitness.db")

PROGRAMS = {
    "Fat Loss (FL)": {
        "factor": 22,
        "workout": "Back Squat, Cardio, Bench, Deadlift, Recovery",
        "diet": "Egg Whites, Chicken, Fish Curry",
    },
    "Muscle Gain (MG)": {
        "factor": 35,
        "workout": "Squat, Bench, Deadlift, Press, Rows",
        "diet": "Eggs, Biryani, Mutton Curry",
    },
    "Beginner (BG)": {
        "factor": 26,
        "workout": "Air Squats, Ring Rows, Push-ups",
        "diet": "Balanced Tamil Meals",
    },
}


def get_db():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            age INTEGER,
            height REAL,
            weight REAL,
            program TEXT NOT NULL,
            calories INTEGER,
            membership_status TEXT DEFAULT 'Active'
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            date TEXT NOT NULL,
            workout_type TEXT NOT NULL,
            duration_min INTEGER,
            notes TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            week TEXT NOT NULL,
            adherence INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def calculate_calories(weight, program):
    if not weight or weight <= 0 or program not in PROGRAMS:
        return None
    return int(weight * PROGRAMS[program]["factor"])


def calculate_bmi(height_cm, weight_kg):
    if not height_cm or height_cm <= 0 or not weight_kg or weight_kg <= 0:
        return None
    h_m = height_cm / 100.0
    bmi = round(weight_kg / (h_m * h_m), 1)
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    return {"bmi": bmi, "category": category}


@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "service": "ACEest Fitness & Gym Management API",
            "status": "running",
            "capacity": 150,
            "programs": list(PROGRAMS.keys()),
        }
    ), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/programs", methods=["GET"])
def get_programs():
    return jsonify(PROGRAMS), 200


@app.route("/clients", methods=["GET", "POST"])
def manage_clients():
    init_db()
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        program = (data.get("program") or "").strip()
        age = data.get("age")
        height = data.get("height")
        weight = data.get("weight")
        membership_status = data.get("membership_status", "Active")

        if not name or program not in PROGRAMS:
            conn.close()
            return jsonify({"error": "Valid name and program are required"}), 400

        calories = calculate_calories(weight, program)
        cur.execute(
            """
            INSERT OR REPLACE INTO clients
            (name, age, height, weight, program, calories, membership_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, age, height, weight, program, calories, membership_status),
        )
        conn.commit()
        conn.close()
        return jsonify(
            {
                "message": f"Client {name} saved",
                "client": {
                    "name": name,
                    "program": program,
                    "calories": calories,
                    "membership_status": membership_status,
                },
            }
        ), 201

    cur.execute("SELECT * FROM clients ORDER BY name")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


@app.route("/clients/<name>/bmi", methods=["GET"])
def client_bmi(name):
    init_db()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, height, weight FROM clients WHERE name=?", (name,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Client not found"}), 404

    result = calculate_bmi(row["height"], row["weight"])
    if not result:
        return jsonify({"error": "Valid height and weight required"}), 400

    return jsonify({"client": row["name"], **result}), 200


@app.route("/workouts", methods=["GET", "POST"])
def manage_workouts():
    init_db()
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        client_name = (data.get("client_name") or "").strip()
        workout_type = (data.get("workout_type") or "").strip()
        w_date = data.get("date") or date.today().isoformat()
        duration_min = data.get("duration_min", 60)
        notes = data.get("notes", "")

        if not client_name or not workout_type:
            conn.close()
            return jsonify({"error": "client_name and workout_type are required"}), 400

        cur.execute(
            """
            INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (client_name, w_date, workout_type, duration_min, notes),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Workout logged", "client_name": client_name}), 201

    cur.execute("SELECT * FROM workouts ORDER BY date DESC, id DESC")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


@app.route("/progress", methods=["POST"])
def log_progress():
    init_db()
    data = request.get_json(silent=True) or {}
    client_name = (data.get("client_name") or "").strip()
    adherence = data.get("adherence")
    week = data.get("week") or datetime.now().strftime("Week %U - %Y")

    if not client_name or adherence is None or not (0 <= int(adherence) <= 100):
        return jsonify({"error": "Valid client_name and adherence (0-100) required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
        (client_name, week, int(adherence)),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Weekly progress logged", "week": week}), 201


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)