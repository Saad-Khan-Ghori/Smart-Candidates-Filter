from flask import Blueprint, jsonify, session

from config import Config
from db import execute_query

if Config.USE_AI_RANKING:
    from app.ranking_ai import get_ranked_candidates
else:
    from app.ranking_sql import get_ranked_candidates

from app.schemas import normalize_ranking_row

bp = Blueprint("ranking", __name__)


def _require_login(*roles):
    uid = session.get("user_id")
    role = session.get("role")
    if not uid:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    if roles and role not in roles:
        return None, (jsonify({"error": "Forbidden"}), 403)
    return {"user_id": uid, "role": role}, None


@bp.route("/<int:job_id>", methods=["GET"])
def ranking_for_job(job_id: int):
    info, err = _require_login("recruiter", "admin")
    if err:
        return err
    job = execute_query(
        "SELECT id, recruiter_user_id FROM Jobs WHERE id=:1",
        [job_id],
        fetch="one",
        commit=False,
    )
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if info["role"] == "recruiter" and int(job["recruiter_user_id"]) != int(info["user_id"]):
        return jsonify({"error": "Forbidden"}), 403
    rows = get_ranked_candidates(job_id)
    return jsonify(
        {
            "job_id": job_id,
            "mode": "ai" if Config.USE_AI_RANKING else "dbs",
            "candidates": [normalize_ranking_row(r) for r in rows],
        }
    )
