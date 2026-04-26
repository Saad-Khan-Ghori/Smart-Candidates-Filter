from flask import Blueprint, jsonify, request, session

import oracledb
from db import execute_query, get_connection

bp = Blueprint("jobs", __name__)


def _require_login(*roles):
    uid = session.get("user_id")
    role = session.get("role")
    if not uid:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    if roles and role not in roles:
        return None, (jsonify({"error": "Forbidden"}), 403)
    return (uid, role), None


@bp.route("/skills", methods=["GET"])
def list_skills():
    rows = execute_query(
        "SELECT id, name FROM Skills ORDER BY name",
        fetch="all",
        commit=False,
    )
    return jsonify(rows or [])


@bp.route("/education-levels", methods=["GET"])
def list_education_levels():
    rows = execute_query(
        "SELECT id, code, label, score_weight FROM EducationLevels ORDER BY id",
        fetch="all",
        commit=False,
    )
    return jsonify(rows or [])


@bp.route("", methods=["GET"])
def list_jobs():
    """Open jobs for candidates; recruiters can pass mine=1 for dashboard summary."""
    mine = request.args.get("mine")
    if mine == "1":
        info, err = _require_login("recruiter", "admin")
        if err:
            return err
        uid, _ = info
        rows = execute_query(
            """
            SELECT v.* FROM vw_JobSummary v
            INNER JOIN Jobs j ON j.id = v.job_id
            WHERE j.recruiter_user_id = :1
            ORDER BY v.job_id DESC
            """,
            [uid],
            fetch="all",
            commit=False,
        )
        return jsonify(rows or [])
    rows = execute_query(
        """
        SELECT j.id AS job_id, j.title, j.description, j.min_years_experience, j.status, j.created_at,
               COALESCE(v.application_count, 0) AS application_count,
               COALESCE(v.average_score, 0) AS average_score
        FROM Jobs j
        LEFT JOIN vw_JobSummary v ON v.job_id = j.id
        WHERE j.status = 'open'
        ORDER BY j.id DESC
        """,
        fetch="all",
        commit=False,
    )
    return jsonify(rows or [])


@bp.route("/<int:job_id>", methods=["GET"])
def get_job(job_id: int):
    job = execute_query(
        """
        SELECT j.id, j.title, j.description, j.min_years_experience, j.status, j.recruiter_user_id, j.created_at
        FROM Jobs j WHERE j.id=:1
        """,
        [job_id],
        fetch="one",
        commit=False,
    )
    if not job:
        return jsonify({"error": "Job not found"}), 404
    skills = execute_query(
        """
        SELECT s.id, s.name FROM JobSkills js
        INNER JOIN Skills s ON s.id = js.skill_id
        WHERE js.job_id=:1 ORDER BY s.name
        """,
        [job_id],
        fetch="all",
        commit=False,
    )
    job["skills"] = skills or []
    return jsonify(job)


@bp.route("", methods=["POST"])
def create_job():
    info, err = _require_login("recruiter", "admin")
    if err:
        return err
    uid, _ = info
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    min_years = data.get("min_years_experience", 1)
    skill_ids = data.get("skill_ids") or []
    if not title:
        return jsonify({"error": "title required"}), 400
    try:
        min_years = int(min_years)
    except (TypeError, ValueError):
        return jsonify({"error": "min_years_experience must be int"}), 400
    if min_years < 0:
        min_years = 0
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            out_bind = cur.var(oracledb.NUMBER)
            cur.execute(
                """
                INSERT INTO Jobs (recruiter_user_id, title, description, min_years_experience)
                VALUES (:1,:2,:3,:4) RETURNING id INTO :5
                """,
                [uid, title, description or None, min_years, out_bind],
            )
            job_id = int(out_bind.getvalue()[0])
            for sid in skill_ids:
                try:
                    sid_int = int(sid)
                except (TypeError, ValueError):
                    continue
                cur.execute(
                    "INSERT INTO JobSkills (job_id, skill_id) SELECT :1, :2 FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM JobSkills WHERE job_id=:1 AND skill_id=:2)",
                    [job_id, sid_int],
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return jsonify({"job_id": job_id, "message": "Job created"}), 201
