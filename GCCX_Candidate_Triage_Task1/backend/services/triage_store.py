from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("TRIAGE_DB_PATH", str(BASE_DIR / "data" / "triage.sqlite3")))
DATA_PATH = Path(os.getenv("TRIAGE_DATA_PATH", str(BASE_DIR / "data" / "candidates.json")))


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                target_role TEXT NOT NULL,
                years_experience REAL NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT '',
                skills_json TEXT NOT NULL DEFAULT '[]',
                notes TEXT NOT NULL DEFAULT '',
                applied_date TEXT NOT NULL DEFAULT '',
                is_shortlisted INTEGER NOT NULL DEFAULT 0,
                tags_json TEXT NOT NULL DEFAULT '[]'
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_role ON candidates(target_role)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_source ON candidates(source)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_shortlisted ON candidates(is_shortlisted)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_experience ON candidates(years_experience)")
        count = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        if count == 0:
            records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
            for item in records:
                conn.execute("""
                    INSERT INTO candidates
                    (id, name, target_role, years_experience, source, skills_json, notes, applied_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item["id"], item["name"], item.get("target_role", ""),
                    item.get("years_experience", 0), item.get("source", ""),
                    json.dumps(item.get("skills", [])), item.get("notes", ""),
                    item.get("applied_date", "")
                ))


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["skills"] = json.loads(item.pop("skills_json"))
    item["tags"] = json.loads(item.pop("tags_json"))
    item["is_shortlisted"] = bool(item["is_shortlisted"])
    return item


def list_candidates(search: str = "", role: str = "", source: str = "",
                    min_experience: float | None = None, max_experience: float | None = None,
                    skill: str = "", shortlisted_only: bool = False) -> list[dict[str, Any]]:
    sql = "SELECT * FROM candidates WHERE 1=1"
    params: list[Any] = []
    if search.strip():
        term = f"%{search.strip()}%"
        sql += " AND (name LIKE ? OR target_role LIKE ? OR notes LIKE ? OR id LIKE ?)"
        params.extend([term, term, term, term])
    if role:
        sql += " AND target_role = ?"
        params.append(role)
    if source:
        sql += " AND source = ?"
        params.append(source)
    if min_experience is not None:
        sql += " AND years_experience >= ?"
        params.append(min_experience)
    if max_experience is not None:
        sql += " AND years_experience <= ?"
        params.append(max_experience)
    if shortlisted_only:
        sql += " AND is_shortlisted = 1"
    sql += " ORDER BY applied_date DESC, name COLLATE NOCASE"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    results = [row_to_dict(row) for row in rows]
    if skill.strip():
        needle = skill.strip().casefold()
        # Exact normalized skill matching avoids false positives (e.g. "java" matching "javascript").
        results = [r for r in results if any(needle == s.strip().casefold() for s in r["skills"])]
    return results


def update_candidate(candidate_id: str, is_shortlisted: bool | None = None,
                     tags: list[str] | None = None) -> dict[str, Any] | None:
    with connect() as conn:
        existing = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if existing is None:
            return None
        if is_shortlisted is not None:
            conn.execute("UPDATE candidates SET is_shortlisted = ? WHERE id = ?",
                         (1 if is_shortlisted else 0, candidate_id))
        if tags is not None:
            clean_tags = list(dict.fromkeys(t.strip() for t in tags if t.strip()))[:20]
            conn.execute("UPDATE candidates SET tags_json = ? WHERE id = ?",
                         (json.dumps(clean_tags), candidate_id))
        row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    return row_to_dict(row)


def candidate_summary(candidate_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    return row_to_dict(row) if row else None
