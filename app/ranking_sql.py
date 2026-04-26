"""DBS mode: scores via stored procedure; ordering from vw_RankedCandidates."""

from typing import Any

from db import get_connection, make_dict_factory


def get_ranked_candidates(job_id: int) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Fetch application IDs
            cur.execute("SELECT id FROM Applications WHERE job_id=:1", [job_id])
            cur.rowfactory = make_dict_factory(cur)
            app_rows = cur.fetchall() or []

            # Call stored procedure per application to calculate score
            for row in app_rows:
                cur.callproc("sp_CalculateCandidateScore", [int(row["id"])])

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
