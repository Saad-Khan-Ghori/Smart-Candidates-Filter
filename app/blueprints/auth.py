from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute_query

bp = Blueprint("auth", __name__)


def _require_json():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "JSON body required"}), 400)
    return data, None


@bp.route("/register", methods=["POST"])
def register():
    data, err = _require_json()
    if err:
        return err
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip()
    role = (data.get("role") or "").strip().lower()
    if not email or not password or not full_name or role not in ("candidate", "recruiter"):
        return jsonify({"error": "email, password, full_name, role (candidate|recruiter) required"}), 400
    existing = execute_query(
        "SELECT id FROM Users WHERE email=:1",
        [email],
        fetch="one",
        commit=False,
    )
    if existing:
        return jsonify({"error": "Email already registered"}), 409
    pw_hash = generate_password_hash(password)
    user_id = execute_query(
        "INSERT INTO Users (email, password_hash, full_name, role) VALUES (:1,:2,:3,:4) RETURNING id INTO :out_bind",
        [email, pw_hash, full_name, role],
        fetch="none",
        returning_id=True,
    )
    if role == "candidate":
        edu_id = data.get("education_level_id")
        years = data.get("years_experience", 0)
        try:
            edu_id = int(edu_id)
            years = int(years)
        except (TypeError, ValueError):
            return jsonify({"error": "education_level_id and years_experience required for candidates"}), 400
        edu = execute_query(
            "SELECT id FROM EducationLevels WHERE id=:1",
            [edu_id],
            fetch="one",
            commit=False,
        )
        if not edu:
            return jsonify({"error": "Invalid education_level_id"}), 400
        execute_query(
            "INSERT INTO Candidates (user_id, education_level_id, years_experience) VALUES (:1,:2,:3)",
            [user_id, edu_id, max(0, years)],
        )
    return jsonify({"message": "Registered", "user_id": user_id, "role": role}), 201


@bp.route("/login", methods=["POST"])
def login():
    data, err = _require_json()
    if err:
        return err
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400
    row = execute_query(
        """
        SELECT u.id, u.email, u.password_hash, u.full_name, u.role, c.id AS candidate_id
        FROM Users u
        LEFT JOIN Candidates c ON c.user_id = u.id
        WHERE u.email=:1
        """,
        [email],
        fetch="one",
        commit=False,
    )
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    session["user_id"] = int(row["id"])
    session["role"] = row["role"]
    session["full_name"] = row["full_name"]
    session["candidate_id"] = int(row["candidate_id"]) if row["candidate_id"] is not None else None
    return jsonify(
        {
            "user_id": int(row["id"]),
            "role": row["role"],
            "full_name": row["full_name"],
            "candidate_id": row["candidate_id"],
        }
    )


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@bp.route("/me", methods=["GET"])
def me():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"authenticated": False}), 200
    return jsonify(
        {
            "authenticated": True,
            "user_id": uid,
            "role": session.get("role"),
            "full_name": session.get("full_name"),
            "candidate_id": session.get("candidate_id"),
        }
    )
