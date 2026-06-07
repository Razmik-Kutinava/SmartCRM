"""Dr. QA — реестр гипотез (SQLite)."""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Optional

from .config import DATA_DIR, DB_PATH, VALID_METHODS, VALID_STATUSES


def _conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS hypotheses (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            description   TEXT NOT NULL DEFAULT '',
            method        TEXT NOT NULL DEFAULT 'ab',
            status        TEXT NOT NULL DEFAULT 'draft',
            created_at    REAL NOT NULL,
            updated_at    REAL NOT NULL,
            result_json   TEXT,
            decision      TEXT,
            decision_reason TEXT,
            canary_pct    INTEGER NOT NULL DEFAULT 0,
            ttl_hours     INTEGER NOT NULL DEFAULT 0,
            canary_started_at REAL
        );
        CREATE TABLE IF NOT EXISTS hypothesis_events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            hypothesis_id   INTEGER NOT NULL,
            ts              REAL NOT NULL,
            event           TEXT NOT NULL,
            payload_json    TEXT NOT NULL DEFAULT '{}'
        );
    """)
    conn.commit()
    return conn


@dataclass
class Hypothesis:
    id: int
    name: str
    description: str
    method: str
    status: str
    created_at: float
    updated_at: float
    result_json: Optional[str]
    decision: Optional[str]
    decision_reason: Optional[str]
    canary_pct: int
    ttl_hours: int
    canary_started_at: Optional[float]


class HypothesisRegistry:
    """SQLite-backed registry of experiment hypotheses."""

    def add(self, name: str, description: str = "", method: str = "ab") -> Hypothesis:
        if method not in VALID_METHODS:
            raise ValueError(f"Unknown method: {method}. Valid: {VALID_METHODS}")
        now = time.time()
        conn = _conn()
        cur = conn.execute(
            "INSERT INTO hypotheses (name, description, method, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'draft', ?, ?)",
            (name, description, method, now, now),
        )
        conn.commit()
        h_id = cur.lastrowid
        self._log(h_id, "created", {"name": name, "method": method})
        return self.get(h_id)

    def get(self, h_id: int) -> Optional[Hypothesis]:
        conn = _conn()
        row = conn.execute("SELECT * FROM hypotheses WHERE id = ?", (h_id,)).fetchone()
        return self._row_to_h(row) if row else None

    def list(self, status: Optional[str] = None) -> list[Hypothesis]:
        conn = _conn()
        if status:
            rows = conn.execute(
                "SELECT * FROM hypotheses WHERE status = ? ORDER BY id DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM hypotheses ORDER BY id DESC").fetchall()
        return [self._row_to_h(r) for r in rows]

    def update_status(self, h_id: int, status: str, reason: str = "") -> None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Unknown status: {status}")
        conn = _conn()
        conn.execute(
            "UPDATE hypotheses SET status = ?, decision = ?, updated_at = ? WHERE id = ?",
            (status, status, time.time(), h_id),
        )
        conn.commit()
        self._log(h_id, f"status→{status}", {"reason": reason})

    def save_result(self, h_id: int, result: dict, decision: str, reason: str) -> None:
        conn = _conn()
        conn.execute(
            "UPDATE hypotheses SET result_json = ?, decision = ?, decision_reason = ?, "
            "status = ?, updated_at = ? WHERE id = ?",
            (json.dumps(result), decision, reason, decision.lower(), time.time(), h_id),
        )
        conn.commit()
        self._log(h_id, "result_saved", {"decision": decision})

    def set_canary(self, h_id: int, pct: int, ttl_hours: int) -> None:
        conn = _conn()
        conn.execute(
            "UPDATE hypotheses SET canary_pct = ?, ttl_hours = ?, canary_started_at = ?, "
            "status = 'canary', updated_at = ? WHERE id = ?",
            (pct, ttl_hours, time.time(), time.time(), h_id),
        )
        conn.commit()
        self._log(h_id, "canary_set", {"pct": pct, "ttl_hours": ttl_hours})
        self._write_canary_config()

    def rollback(self, h_id: int) -> None:
        conn = _conn()
        conn.execute(
            "UPDATE hypotheses SET canary_pct = 0, status = 'killed', updated_at = ? WHERE id = ?",
            (time.time(), h_id),
        )
        conn.commit()
        self._log(h_id, "rollback", {})
        self._write_canary_config()

    def check_expired_canaries(self) -> list[int]:
        conn = _conn()
        rows = conn.execute(
            "SELECT id, canary_started_at, ttl_hours FROM hypotheses "
            "WHERE status = 'canary' AND ttl_hours > 0"
        ).fetchall()
        expired = []
        now = time.time()
        for r in rows:
            if r["canary_started_at"] and r["ttl_hours"]:
                elapsed_h = (now - r["canary_started_at"]) / 3600
                if elapsed_h >= r["ttl_hours"]:
                    expired.append(r["id"])
        return expired

    def _write_canary_config(self) -> None:
        conn = _conn()
        rows = conn.execute(
            "SELECT id, name, canary_pct FROM hypotheses WHERE status = 'canary'"
        ).fetchall()
        cfg = {"active_canaries": [dict(r) for r in rows]}
        out = DATA_DIR / "canary_config.json"
        out.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    def _log(self, h_id: int, event: str, payload: dict) -> None:
        conn = _conn()
        conn.execute(
            "INSERT INTO hypothesis_events (hypothesis_id, ts, event, payload_json) VALUES (?, ?, ?, ?)",
            (h_id, time.time(), event, json.dumps(payload)),
        )
        conn.commit()

    @staticmethod
    def _row_to_h(row: sqlite3.Row) -> Hypothesis:
        return Hypothesis(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            method=row["method"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            result_json=row["result_json"],
            decision=row["decision"],
            decision_reason=row["decision_reason"],
            canary_pct=row["canary_pct"],
            ttl_hours=row["ttl_hours"],
            canary_started_at=row["canary_started_at"],
        )
