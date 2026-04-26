"""Extract PDF text and map known Skills using spaCy PhraseMatcher (lexicon from DB)."""

from __future__ import annotations

import re
from typing import Iterable

import pdfplumber

from db import execute_query, get_connection

try:
    import spacy
    from spacy.matcher import PhraseMatcher

    _NLP = spacy.blank("en")
except ImportError:  # pragma: no cover
    spacy = None  # type: ignore
    PhraseMatcher = None  # type: ignore
    _NLP = None


def extract_pdf_text(path: str) -> str:
    parts: list[str] = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
    except Exception:
        return ""
    return "\n".join(parts)


def _match_skill_ids_regex(text: str, skills: Iterable[dict]) -> set[int]:
    if not text:
        return set()
    matched: set[int] = set()
    lower_full = text.lower()
    for row in skills:
        name = str(row["name"])
        pattern = r"(?<!\w)" + re.escape(name) + r"(?!\w)"
        if re.search(pattern, lower_full, flags=re.IGNORECASE):
            matched.add(int(row["id"]))
    return matched


def _match_skill_ids_spacy(text: str, skills: list[dict]) -> set[int]:
    if not text or _NLP is None or PhraseMatcher is None:
        return set()
    matcher = PhraseMatcher(_NLP.vocab, attr="LOWER")
    for row in skills:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        matcher.add(str(int(row["id"])), [_NLP.make_doc(name)])
    doc = _NLP(text)
    out: set[int] = set()
    for match_id, _start, _end in matcher(doc):
        key = _NLP.vocab.strings[match_id]
        try:
            out.add(int(key))
        except ValueError:
            continue
    return out


def sync_skills_from_resume(candidate_id: int, resume_path: str) -> None:
    text = extract_pdf_text(resume_path)
    skills = execute_query("SELECT id, name FROM Skills", fetch="all", commit=False) or []
    if spacy and skills:
        ids = _match_skill_ids_spacy(text, skills)
        if not ids:
            ids = _match_skill_ids_regex(text, skills)
    else:
        ids = _match_skill_ids_regex(text, skills)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM CandidateSkills WHERE candidate_id=:1", [candidate_id])
            for sid in ids:
                cur.execute(
                    "INSERT INTO CandidateSkills (candidate_id, skill_id) VALUES (:1,:2)",
                    [candidate_id, sid],
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
