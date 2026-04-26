from flask import Blueprint, jsonify, session

from db import execute_query

bp = Blueprint("admin", __name__)


def _require_admin():
    if session.get("role") != "admin":
        return (jsonify({"error": "Forbidden"}), 403)
    return None


@bp.route("/users", methods=["GET"])
def list_users():
    err = _require_admin()
    if err:
        return err
    rows = execute_query(
        """
        SELECT u.id, u.email, u.full_name, u.role, u.created_at, c.id AS candidate_id
        FROM Users u
        LEFT JOIN Candidates c ON c.user_id = u.id
        ORDER BY u.id
        """,
        fetch="all",
        commit=False,
    )
    return jsonify(rows or [])


@bp.route("/jobs", methods=["GET"])
def list_all_jobs():
    err = _require_admin()
    if err:
        return err
    rows = execute_query(
        """
        SELECT j.id, j.title, j.recruiter_user_id, j.status, j.min_years_experience, j.created_at,
               v.application_count, v.average_score
        FROM Jobs j
        LEFT JOIN vw_JobSummary v ON v.job_id = j.id
        ORDER BY j.id DESC
        """,
        fetch="all",
        commit=False,
    )
    return jsonify(rows or [])


@bp.route("/audit", methods=["GET"])
def audit_log():
    err = _require_admin()
    if err:
        return err
    rows = execute_query(
        """
        SELECT * FROM (
            SELECT l.id, l.application_id, l.old_status, l.new_status, l.changed_at,
                   a.job_id, a.candidate_id
            FROM ApplicationAuditLog l
            INNER JOIN Applications a ON a.id = l.application_id
            ORDER BY l.changed_at DESC
        ) WHERE ROWNUM <= 500
        """,
        fetch="all",
        commit=False,
    )
    return jsonify(rows or [])


@bp.route("/skill-gap/<int:job_id>", methods=["GET"])
def skill_gap(job_id: int):
    err = _require_admin()
    if err:
        return err
    rows = execute_query(
        """
        SELECT job_id, skill_id, skill_name, applicants_with_skill, total_applicants_for_job
        FROM vw_SkillGap
        WHERE job_id=:1
        ORDER BY skill_name
        """,
        [job_id],
        fetch="all",
        commit=False,
    )
    return jsonify(rows or [])
