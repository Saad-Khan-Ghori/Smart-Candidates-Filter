"""AI mode: TF-IDF skill similarity + same exp/edu weighting as SQL; scores persisted then read from view."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import Config
from db import get_connection, make_dict_factory


def _exp_score(cand_years: int, job_min: int) -> float:
    if job_min is None or job_min <= 0:
        return 100.0
    return float(min(100.0, (cand_years * 100.0) / job_min))


def _skill_tfidf_score(job_skill_names: list[str], cand_skill_names: list[str]) -> float:
    if not job_skill_names:
        return 100.0
    if not cand_skill_names:
        return 0.0
    job_text = " ".join(job_skill_names)
    cand_text = " ".join(cand_skill_names)
    vec = TfidfVectorizer(analyzer="word", token_pattern=r"(?u)\b\w+\b")
    try:
        m = vec.fit_transform([job_text, cand_text])
        sim = cosine_similarity(m[0:1], m[1:2])[0][0]
    except ValueError:
        return 0.0
    return float(max(0.0, min(1.0, sim)) * 100.0)


def _semantic_score(job_skill_names: list[str], cand_skill_names: list[str]) -> float | None:
    if not job_skill_names or not cand_skill_names:
        return None
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None
    model = getattr(_semantic_score, "_model", None)
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        _semantic_score._model = model  # type: ignore[attr-defined]
    j_emb = model.encode(" ".join(job_skill_names), convert_to_numpy=True)
    c_emb = model.encode(" ".join(cand_skill_names), convert_to_numpy=True)
    j_norm = j_emb / (np.linalg.norm(j_emb) + 1e-9)
    c_norm = c_emb / (np.linalg.norm(c_emb) + 1e-9)
    sim = float(np.dot(j_norm, c_norm))
    return max(0.0, min(1.0, sim)) * 100.0


def _combined_skill_score(job_skill_names: list[str], cand_skill_names: list[str]) -> float:
    tf = _skill_tfidf_score(job_skill_names, cand_skill_names)
    if not Config.USE_SEMANTIC_RANKING:
        return tf
    sem = _semantic_score(job_skill_names, cand_skill_names)
    if sem is None:
        return tf
    return 0.7 * tf + 0.3 * sem


def get_ranked_candidates(job_id: int) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT js.skill_id, s.name
                FROM JobSkills js
                INNER JOIN Skills s ON s.id = js.skill_id
                WHERE js.job_id=:1
                ORDER BY s.name
                """,
                [job_id],
            )
            cur.rowfactory = make_dict_factory(cur)
            job_skills = cur.fetchall() or []
            job_skill_names = [r["name"] for r in job_skills]

            cur.execute(
                """
                SELECT a.id AS application_id, a.candidate_id, a.job_id,
                       c.years_experience, j.min_years_experience, el.score_weight AS edu_weight
                FROM Applications a
                INNER JOIN Candidates c ON c.id = a.candidate_id
                INNER JOIN Jobs j ON j.id = a.job_id
                INNER JOIN EducationLevels el ON el.id = c.education_level_id
                WHERE a.job_id=:1
                """,
                [job_id],
            )
            cur.rowfactory = make_dict_factory(cur)
            apps = cur.fetchall() or []

            for app in apps:
                cid = int(app["candidate_id"])
                cur.execute(
                    """
                    SELECT s.name FROM CandidateSkills cs
                    INNER JOIN Skills s ON s.id = cs.skill_id
                    WHERE cs.candidate_id=:1 ORDER BY s.name
                    """,
                    [cid],
                )
                cur.rowfactory = make_dict_factory(cur)
                cskills = cur.fetchall() or []
                cand_names = [r["name"] for r in cskills]
                skill_pct = _combined_skill_score(job_skill_names, cand_names)
                exp_pct = _exp_score(int(app["years_experience"]), int(app["min_years_experience"]))
                edu_pct = float(app["edu_weight"] or 0)
                final = 0.50 * skill_pct + 0.30 * exp_pct + 0.20 * edu_pct
                cur.execute(
                    "UPDATE Applications SET score=:1 WHERE id=:2",
                    [round(final, 2), int(app["application_id"])],
                )
        conn.commit()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT application_id, job_id, candidate_id, score, application_status,
                       candidate_name, rank_position
                FROM vw_RankedCandidates
                WHERE job_id=:1
                ORDER BY rank_position ASC, application_id ASC
                """,
                [job_id],
            )
            cur.rowfactory = make_dict_factory(cur)
            return list(cur.fetchall() or [])
    finally:
        conn.close()
