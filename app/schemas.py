"""Shared JSON shapes for API responses."""

from typing import Any, TypedDict


class RankedCandidateRow(TypedDict):
    application_id: int
    job_id: int
    candidate_id: int
    score: float
    application_status: str
    candidate_name: str
    rank_position: int


def normalize_ranking_row(row: dict[str, Any]) -> RankedCandidateRow:
    return {
        "application_id": int(row["application_id"]),
        "job_id": int(row["job_id"]),
        "candidate_id": int(row["candidate_id"]),
        "score": float(row["score"]) if row["score"] is not None else 0.0,
        "application_status": str(row["application_status"]),
        "candidate_name": str(row["candidate_name"]),
        "rank_position": int(row["rank_position"]),
    }
