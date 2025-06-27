from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3

app = Flask(__name__)

# ──────────────────────────────────────────────────────────────
# DB INITIALISATION
# ──────────────────────────────────────────────────────────────
def init_db():
    """Create tables on first run and seed one default admin."""
    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()

        # users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email    TEXT NOT NULL,
                password TEXT NOT NULL
            );
        """)

        # login-history table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # admins table  (with EMAIL)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email    TEXT NOT NULL,
                password TEXT NOT NULL
            );
        """)

        # seed one admin if none exists
        cur.execute("SELECT 1 FROM admins LIMIT 1")
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO admins (username, email, password) VALUES (?,?,?)",
                ("admin", "admin@example.com", "admin123")
            )
            print("✅ Seeded default admin (admin / admin123)")
        conn.commit()

# ──────────────────────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────────────────────
def save_user(username: str, email: str, password: str) -> int:
    try:
        with sqlite3.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, email, password) VALUES (?,?,?)",
                (username, email, password)
            )
            conn.commit()
            return cur.lastrowid
    except sqlite3.IntegrityError:
        return -1  # duplicate username


def save_admin(username: str, email: str, password: str) -> int:
    try:
        with sqlite3.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO admins (username, email, password) VALUES (?,?,?)",
                (username, email, password)
            )
            conn.commit()
            return cur.lastrowid
    except sqlite3.IntegrityError:
        return -1

# ──────────────────────────────────────────────────────────────
#  HTML PAGES
# ──────────────────────────────────────────────────────────────
@app.route("/")
def index():                          return render_template("index.html")

@app.route("/Employee_Login")
def signup_form():                    return render_template("SignUp_LogIn_Form.html")

# ── /admin_data  ─────────────────────────────────────────────
@app.route("/admin_data")
def view_admins():
    """Show all admins in a simple table."""
    with sqlite3.connect("users.db") as conn:
        admins = conn.execute(
            "SELECT id, username, email, password FROM admins ORDER BY id"
        ).fetchall()
    return render_template("admin_data.html", admins=admins)


@app.route("/Employee_login", methods=["POST"])
def register_submit():
    username = request.form.get("username")
    email    = request.form.get("email")
    password = request.form.get("password")
    if not all([username, email, password]):
        return redirect(url_for("signup_form"))
    save_user(username, email, password)
    return redirect(url_for("signup_form"))

@app.route("/admin", methods=["GET", "POST"])
def admin_form():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        with sqlite3.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM admins WHERE username=? AND password=?",
                (username, password)
            )
            if cur.fetchone():
                return redirect(url_for("admin_dashboard"))

        return render_template("admin_login.html", message="Invalid login")

    return render_template("admin_login.html")


@app.route("/admin_dashboard")
def admin_dashboard():                return render_template("admin_dashboard.html")

@app.route("/users")
def view_users():
    with sqlite3.connect("users.db") as conn:
        users = conn.execute(
            "SELECT id, username, email, password FROM users"
        ).fetchall()
    return render_template("users.html", users=users)

@app.route("/login", methods=["POST"])
def login_submit():
    username = request.form.get("username")
    password = request.form.get("password")
    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE username=? AND password=?",
                    (username, password))
        if cur.fetchone():
            cur.execute("INSERT INTO logins (username,password) VALUES (?,?)",
                        (username, password))
            conn.commit()
            return redirect(url_for("view_users"))
    return redirect(url_for("signup_form"))

@app.route("/login_history")
def login_history():
    with sqlite3.connect("users.db") as conn:
        logs = conn.execute(
            "SELECT username,password,login_time FROM logins ORDER BY login_time DESC"
        ).fetchall()
    return render_template("login_history.html", logins=logs)


# ──────────────────────────────────────────────────────────────
#  JSON API
# ──────────────────────────────────────────────────────────────
# POST  /api/users  (add employee)
@app.route("/api/users", methods=["POST"])
def api_add_user():
    if not request.is_json:
        return {"msg": "JSON body required"}, 415
    data = request.get_json()
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not all([username, email, password]):
        return {"msg": "username, email, password required"}, 400

    new_id = save_user(username, email, password)
    if new_id == -1:
        return {"msg": "Username already exists"}, 409

    return {"id": new_id, "username": username, "email": email,
            "password": password}, 201

# GET   /api/users  (list employees)
@app.route("/api/users", methods=["GET"])
def api_list_users():
    with sqlite3.connect("users.db") as conn:
        rows = conn.execute(
            "SELECT id, username, email, password FROM users ORDER BY id"
        ).fetchall()
    return jsonify([
        {"id": r[0], "username": r[1], "email": r[2], "password": r[3]}
        for r in rows
    ])

# POST  /api/admins (add admin)
@app.route("/api/admins", methods=["POST"])
def api_add_admin():
    if not request.is_json:
        return {"msg": "JSON body required"}, 415
    data = request.get_json()
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not all([username, email, password]):
        return {"msg": "username, email, password required"}, 400

    new_id = save_admin(username, email, password)
    if new_id == -1:
        return {"msg": "Admin already exists"}, 409

    return {"id": new_id, "username": username, "email": email}, 201

# ──────────────────────────────────────────────────────────────
#  RUN
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
