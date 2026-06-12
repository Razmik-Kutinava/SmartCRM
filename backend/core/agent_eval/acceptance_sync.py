"""Таблица acceptance и список дыр из JSON gate-отчёта."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

GATE_EMOJI = {"pass": "✅", "warn": "🟡", "fail": "🔴"}

_AGENT_LABELS = {
    "hermes": "Hermes",
    "analyst": "Analyst",
    "economist": "Economist",
    "marketer": "Marketer",
    "strategist": "Strategist",
    "tech_specialist": "Tech",
}

_REPO = Path(__file__).resolve().parents[3]
ACCEPTANCE_PATH = _REPO / "docs" / "operations" / "AGENTS_QUALITY_GATE_ACCEPTANCE.md"
MARKER_START = "<!-- GATE_STATUS_START -->"
MARKER_END = "<!-- GATE_STATUS_END -->"
GAPS_START = "<!-- GATE_GAPS_START -->"
GAPS_END = "<!-- GATE_GAPS_END -->"


def acceptance_rows(report: dict[str, Any], artifact_name: str = "") -> list[dict[str, str]]:
    date = (report.get("generated_at") or "")[:10] or datetime.now().strftime("%Y-%m-%d")
    art = artifact_name or "—"
    out: list[dict[str, str]] = []
    for key, block in (report.get("agents") or {}).items():
        s = block.get("summary") or {}
        gate = s.get("gate", "fail")
        out.append({
            "agent": _AGENT_LABELS.get(key, key),
            "pass": str(s.get("passed", 0)),
            "fail": str(s.get("failed", 0)),
            "pass_rate": f"{s.get('pass_rate_pct', 0)}%",
            "threshold": f"{s.get('threshold_pct', 0)}%",
            "gate": GATE_EMOJI.get(gate, "🔲"),
            "date": date,
            "artifact": art,
        })
    return out


def build_gaps(report: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    for key, block in (report.get("agents") or {}).items():
        s = block.get("summary") or {}
        label = _AGENT_LABELS.get(key, key)
        gate = s.get("gate", "fail")
        rate = s.get("pass_rate_pct", 0)
        thr = s.get("threshold_pct", 0)
        total = s.get("total", 0)
        min_n = s.get("min_cases", 0)
        if gate != "pass":
            gaps.append(f"**{label}**: pass rate {rate}% (порог {thr}%) — gate **{gate}**")
        if min_n and total < min_n:
            gaps.append(f"**{label}**: прогон {total}/{min_n} кейсов — недостаточно для закрытия")
        fails = [r for r in block.get("results") or [] if not r.get("passed")]
        timeouts = [r for r in fails if r.get("error") and "Timeout" in str(r["error"])]
        if timeouts:
            gaps.append(f"**{label}**: {len(timeouts)} кейсов ReadTimeout — поднять `EVAL_OLLAMA_TIMEOUT` или GPU")
    if report.get("overall_gate") != "pass":
        gaps.append("**MAP `[x]`** — не ставить, пока `overall_gate` ≠ pass")
    return gaps


def _table_md(rows: list[dict[str, str]]) -> str:
    lines = [
        "| Агент | Pass | Fail | Pass rate | Порог | Gate | Дата | Артефакт |",
        "|-------|------|------|-----------|-------|------|------|----------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['agent']} | {r['pass']} | {r['fail']} | {r['pass_rate']} | {r['threshold']} "
            f"| {r['gate']} | {r['date']} | {r['artifact']} |"
        )
    return "\n".join(lines)


def _gaps_md(gaps: list[str]) -> str:
    if not gaps:
        return "Нет открытых дыр — gate зелёный."
    return "\n".join(f"- {g}" for g in gaps)


def patch_acceptance_md(report: dict[str, Any], artifact_name: str, path: Path | None = None) -> Path:
    target = path or ACCEPTANCE_PATH
    text = target.read_text(encoding="utf-8")
    rows = acceptance_rows(report, artifact_name)
    gaps = build_gaps(report)
    report["gaps"] = gaps
    block = f"{MARKER_START}\n{_table_md(rows)}\n{MARKER_END}"
    gaps_block = f"{GAPS_START}\n{_gaps_md(gaps)}\n{GAPS_END}"
    if MARKER_START not in text:
        raise ValueError(f"markers not found in {target}")
    text = re.sub(
        rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}",
        block,
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = re.sub(
        rf"{re.escape(GAPS_START)}.*?{re.escape(GAPS_END)}",
        gaps_block,
        text,
        count=1,
        flags=re.DOTALL,
    )
    target.write_text(text, encoding="utf-8")
    return target
