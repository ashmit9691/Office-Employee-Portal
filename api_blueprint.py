from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from auth_utils import admin_required
import sqlite3

api = Blueprint("admin_api", __name__, url_prefix="/api/admin")

# ── ADD EMPLOYEE ─────────────────────────────────────────────
@api.route("/users", methods=["POST"])
@jwt_required()
@admin_required
def create_employee():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not (username and email and password):
        return {"msg": "Missing fields"}, 400

    try:
        with sqlite3.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username,email,password) VALUES (?,?,?)",
                (username, email, password)
            )
            conn.commit()
            new_id = cur.lastrowid
        return jsonify(id=new_id, username=username, email=email), 201
    except sqlite3.IntegrityError as e:
        return {"msg": str(e)}, 409
