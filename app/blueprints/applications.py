import os
import threading
import uuid
from werkzeug.utils import secure_filename

from flask import Blueprint, current_app, jsonify, request, session

from db import execute_query, get_connection
from app.resume_processor import sync_skills_from_resume

bp = Blueprint("applications", __name__)


def _require_login(*roles):
    uid = session.get("user_id")
    role = session.get("role")
    if not uid:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    if roles and role not in roles:
        return None, (jsonify({"error": "Forbidden"}), 403)
    return {"user_id": uid, "role": role, "candidate_id": session.get("candidate_id")}, None


def _process_resume_async(candidate_id: int, resume_path: str, job_id: int) -> None:
    try:
        sync_skills_from_resume(candidate_id, resume_path)
        
        # Recalculate ranking immediately after skills are processed
        from config import Config
        if Config.USE_AI_RANKING:
            from app.ranking_ai import get_ranked_candidates
        else:
            from app.ranking_sql import get_ranked_candidates
        
        get_ranked_candidates(job_id)
        
    except Exception as exc:
        current_app.logger.exception("Resume processing failed: %s", exc)


@bp.route("", methods=["POST"])
def apply():
    info, err = _require_login("candidate")
    if err:
        return err
    cid = info["candidate_id"]
    if not cid:
        return jsonify({"error": "Candidate profile missing"}), 400
    job_id = request.form.get("job_id", type=int)
    file = request.files.get("resume")
    if not job_id or not file or not file.filename:
        return jsonify({"error": "job_id and resume file required"}), 400
    job = execute_query("SELECT id FROM Jobs WHERE id=:1 AND status='open'", [job_id], fetch="one", commit=False)
    if not job:
        return jsonify({"error": "Job not found or closed"}), 404
    ext = os.path.splitext(secure_filename(file.filename))[1].lower() or ".pdf"
    if ext != ".pdf":
        return jsonify({"error": "Only PDF resumes are accepted"}), 400
    fname = f"{uuid.uuid4().hex}{ext}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    dest_path = os.path.join(upload_dir, fname)
    file.save(dest_path)
    try:
        app_id = execute_query(
            """
            INSERT INTO Applications (candidate_id, job_id, status, score, resume_path)
            VALUES (:1,:2,'submitted',0,:3) RETURNING id INTO :out_bind
            """,
            [cid, job_id, dest_path],
            fetch="none",
            returning_id=True,
        )
    except Exception as exc:
        if "Duplicate" in str(exc) or "1062" in str(exc) or "ORA-00001" in str(exc):
            if os.path.isfile(dest_path):
                os.remove(dest_path)
            return jsonify({"error": "Already applied to this job"}), 409
        if os.path.isfile(dest_path):
            os.remove(dest_path)
        raise
    thread = threading.Thread(
        target=_process_resume_async,
        args=(int(cid), dest_path, int(job_id)),
        daemon=True,
    )
    thread.start()
    return jsonify({"application_id": app_id, "message": "Application submitted; resume processing started"}), 201


@bp.route("/<int:application_id>/status", methods=["PATCH"])
def update_status(application_id: int):
    info, err = _require_login("recruiter", "admin")
    if err:
        return err
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400
    new_status = (data.get("status") or "").strip().lower()
    if new_status not in ("submitted", "shortlisted", "rejected", "reviewed"):
        return jsonify({"error": "Invalid status"}), 400
    row = execute_query(
        """
        SELECT a.id, a.status, j.recruiter_user_id
        FROM Applications a
        INNER JOIN Jobs j ON j.id = a.job_id
        WHERE a.id=:1
        """,
        [application_id],
        fetch="one",
        commit=False,
    )
    if not row:
        return jsonify({"error": "Application not found"}), 404
    if info["role"] == "recruiter" and int(row["recruiter_user_id"]) != int(info["user_id"]):
        return jsonify({"error": "Forbidden"}), 403
    execute_query(
        "UPDATE Applications SET status=:1 WHERE id=:2",
        [new_status, application_id],
    )
    return jsonify({"message": "Status updated", "application_id": application_id, "status": new_status})


@bp.route("/mine", methods=["GET"])
def my_applications():
    info, err = _require_login("candidate")
    if err:
        return err
    cid = info["candidate_id"]
    rows = execute_query(
        """
        SELECT a.id AS application_id, a.job_id, a.status, a.score, a.applied_at, j.title AS job_title
        FROM Applications a
        INNER JOIN Jobs j ON j.id = a.job_id
        WHERE a.candidate_id=:1
        ORDER BY a.applied_at DESC
        """,
        [cid],
        fetch="all",
        commit=False,
    )
    return jsonify(rows or [])


@bp.route("/skills", methods=["GET"])
def my_skills():
    """Return the skills currently extracted from the logged-in candidate's resume."""
    info, err = _require_login("candidate")
    if err:
        return err
    cid = info["candidate_id"]
    rows = execute_query(
        """
        SELECT s.id, s.name
        FROM CandidateSkills cs
        INNER JOIN Skills s ON s.id = cs.skill_id
        WHERE cs.candidate_id=:1
        ORDER BY s.name
        """,
        [cid],
        fetch="all",
        commit=False,
    )
    return jsonify(rows or [])

