"""
Lightweight long-term memory for Hermes observations.

Implements progressive disclosure:
1) search_index()   -> cheap previews + IDs
2) timeline()       -> chronological neighbors
3) get_observations -> full records by IDs
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DB_PATH = _DATA_DIR / "agent_memory.sqlite3"
_MAX_PREVIEW = 120


def _conn() -> sqlite3.Connection:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            scope TEXT NOT NULL,
            text TEXT NOT NULL,
            intent TEXT,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_observations_scope_ts ON observations(scope, ts DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_observations_scope_intent ON observations(scope, intent)")
    return conn


def _norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def add_observation(scope: str, text: str, intent: str, payload: dict[str, Any]) -> int:
    conn = _conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO observations(ts, scope, text, intent, payload_json)
            VALUES(?, ?, ?, ?, ?)
            """,
            (time.time(), scope, _norm(text), intent, json.dumps(payload, ensure_ascii=False)),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def search_index(scope: str, query: str, limit: int = 10) -> list[dict[str, Any]]:
    q = _norm(query)
    conn = _conn()
    try:
        rows = conn.execute(
            """
            SELECT id, ts, intent, text
            FROM observations
            WHERE scope = ?
              AND text LIKE ?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (scope, f"%{q}%", limit),
        ).fetchall()
        out = []
        for r in rows:
            txt = r["text"] or ""
            out.append(
                {
                    "id": int(r["id"]),
                    "ts": float(r["ts"]),
                    "intent": r["intent"],
                    "preview": (txt[:_MAX_PREVIEW] + "...") if len(txt) > _MAX_PREVIEW else txt,
                }
            )
        return out
    finally:
        conn.close()


def timeline(scope: str, around_id: int, before: int = 3, after: int = 3) -> list[dict[str, Any]]:
    conn = _conn()
    try:
        center = conn.execute("SELECT ts FROM observations WHERE id = ? AND scope = ?", (around_id, scope)).fetchone()
        if not center:
            return []
        ts = float(center["ts"])
        rows_before = conn.execute(
            """
            SELECT id, ts, intent, text FROM observations
            WHERE scope = ? AND ts < ?
            ORDER BY ts DESC LIMIT ?
            """,
            (scope, ts, before),
        ).fetchall()
        rows_after = conn.execute(
            """
            SELECT id, ts, intent, text FROM observations
            WHERE scope = ? AND ts > ?
            ORDER BY ts ASC LIMIT ?
            """,
            (scope, ts, after),
        ).fetchall()
        center_row = conn.execute(
            "SELECT id, ts, intent, text FROM observations WHERE id = ? AND scope = ?",
            (around_id, scope),
        ).fetchone()
        merged = list(reversed(rows_before)) + ([center_row] if center_row else []) + list(rows_after)
        return [
            {"id": int(r["id"]), "ts": float(r["ts"]), "intent": r["intent"], "text": r["text"]}
            for r in merged
        ]
    finally:
        conn.close()


def get_observations(ids: list[int]) -> list[dict[str, Any]]:
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    conn = _conn()
    try:
        rows = conn.execute(
            f"SELECT id, ts, scope, text, intent, payload_json FROM observations WHERE id IN ({placeholders})",
            ids,
        ).fetchall()
        out = []
        for r in rows:
            payload = {}
            try:
                payload = json.loads(r["payload_json"] or "{}")
            except json.JSONDecodeError:
                payload = {}
            out.append(
                {
                    "id": int(r["id"]),
                    "ts": float(r["ts"]),
                    "scope": r["scope"],
                    "text": r["text"],
                    "intent": r["intent"],
                    "payload": payload,
                }
            )
        return out
    finally:
        conn.close()


def lookup_recent_similar(scope: str, text: str) -> dict[str, Any] | None:
    """
    Cheap similarity: exact-normalized text hit in recent observations.
    Returns payload of latest exact match.
    """
    q = _norm(text)
    conn = _conn()
    try:
        row = conn.execute(
            """
            SELECT payload_json
            FROM observations
            WHERE scope = ? AND text = ?
            ORDER BY ts DESC
            LIMIT 1
            """,
            (scope, q),
        ).fetchone()
        if not row:
            return None
        try:
            return json.loads(row["payload_json"] or "{}")
        except json.JSONDecodeError:
            return None
    finally:
        conn.close()

