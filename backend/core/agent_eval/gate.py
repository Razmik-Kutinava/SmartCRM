"""Прогон quality gate: Hermes + 5 агентов через Ollama."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.analyst.runner import run as run_analyst
from agents.base import make_initial_state
from agents.economist import run as run_economist
from agents.marketer import run as run_marketer
from agents.strategist import run as run_strategist
from agents.tech_specialist import run as run_tech
from core.agent_eval.cases import (
    AGENT_IDS,
    AGENT_MIN_CASES,
    HERMES_MIN_CASES,
    load_agent_cases,
    load_hermes_cases,
)
from core.agent_eval.gate_config import (
    AGENT_OUTPUT_KEYS,
    AGENT_THRESHOLD_PCT,
    HERMES_THRESHOLD_PCT,
    gate_label,
)
from core.agent_eval.ollama_check import HERMES_MODEL, check_ollama_ready, warmup_ollama
from core.agent_eval.score import score_case
from core.eval_runner import eval_one_case

_REPO = Path(__file__).resolve().parents[3]
ARTIFACTS_DIR = _REPO / "backend" / "data" / "artifacts" / "eval"


def _gate_log(msg: str) -> None:
    print(msg, flush=True)


_gate_logger = _gate_log


def set_gate_logger(fn) -> None:
    global _gate_logger
    _gate_logger = fn

_RUNNERS = {
    "analyst": run_analyst,
    "economist": run_economist,
    "marketer": run_marketer,
    "tech_specialist": run_tech,
    "strategist": run_strategist,
}


def force_ollama_env() -> None:
    os.environ["GROQ_API_KEY"] = ""
    os.environ["OLLAMA_MODEL"] = os.getenv("HERMES_MODEL", HERMES_MODEL)
    import core.llm as llm_mod

    llm_mod.GROQ_API_KEY = ""
    llm_mod._groq_available = False
    llm_mod._groq_client = None


def _summarize(rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    total = len(rows)
    passed = sum(1 for r in rows if r.get("passed"))
    rate = round(passed / total * 100, 1) if total else 0.0
    return {
        "passed": passed,
        "failed": total - passed,
        "total": total,
        "pass_rate_pct": rate,
        "threshold_pct": threshold,
        "gate": gate_label(rate, threshold),
    }


async def run_hermes_gate(*, limit: int = 0) -> dict[str, Any]:
    cases = load_hermes_cases()
    if limit > 0:
        cases = cases[:limit]
    rows: list[dict[str, Any]] = []
    for case in cases:
        text = case["text"]
        expected = case.get("expected_intent")
        result = await eval_one_case(text, expected, "hermes3")
        ok = result.get("correct") is True and "error" not in result
        rows.append({
            "id": case.get("id"),
            "text": text[:120],
            "expected_intent": expected,
            "actual_intent": result.get("intent"),
            "passed": ok,
            "error": result.get("error"),
            "duration_ms": result.get("duration_ms"),
        })
    summary = _summarize(rows, HERMES_THRESHOLD_PCT)
    summary["min_cases"] = HERMES_MIN_CASES
    return {"agent": "hermes", "model": HERMES_MODEL, "summary": summary, "results": rows}


async def run_single_agent_gate(agent_id: str, *, limit: int = 0) -> dict[str, Any]:
    cases = load_agent_cases(agent_id)
    if limit > 0:
        cases = cases[:limit]
    runner = _RUNNERS[agent_id]
    out_key = AGENT_OUTPUT_KEYS[agent_id]
    rows: list[dict[str, Any]] = []
    for case in cases:
        state = make_initial_state(case["intent"], dict(case.get("slots") or {}))
        for k, v in (case.get("state_overrides") or {}).items():
            state[k] = v
        t0 = time.monotonic()
        try:
            new_state = await runner(state)
            output = new_state.get(out_key) or {}
            ok, reason = score_case(output, case)
            err = None
        except Exception as e:
            ok, reason = False, f"exception:{type(e).__name__}"
            err = str(e)[:200]
        duration_ms = round((time.monotonic() - t0) * 1000)
        rows.append({
            "id": case["id"],
            "intent": case["intent"],
            "passed": ok,
            "reason": reason,
            "error": err,
            "duration_ms": duration_ms,
        })
    summary = _summarize(rows, AGENT_THRESHOLD_PCT)
    summary["min_cases"] = AGENT_MIN_CASES
    return {"agent": agent_id, "model": os.getenv("OLLAMA_MODEL", HERMES_MODEL), "summary": summary, "results": rows}


async def run_agents_quality_gate(
    *,
    hermes_limit: int = 0,
    agent_limit: int = 0,
    skip_agents: bool = False,
    skip_hermes: bool = False,
) -> dict[str, Any]:
    force_ollama_env()
    ollama = await check_ollama_ready()
    _gate_logger("[gate] warmup Ollama (first call may take minutes on CPU)...")
    await warmup_ollama()
    _gate_logger("[gate] warmup OK")
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ollama": ollama,
        "agents": {},
    }
    if not skip_hermes:
        report["agents"]["hermes"] = await run_hermes_gate(limit=hermes_limit)
    if not skip_agents:
        for aid in AGENT_IDS:
            _gate_logger(f"[gate] {aid} ...")
            report["agents"][aid] = await run_single_agent_gate(aid, limit=agent_limit)
    gates = [v["summary"]["gate"] for v in report["agents"].values()]
    report["overall_gate"] = "fail" if "fail" in gates else ("warn" if "warn" in gates else "pass")
    from core.agent_eval.acceptance_sync import build_gaps

    report["gaps"] = build_gaps(report)
    return report


def save_gate_artifact(report: dict[str, Any], path: Path | None = None) -> Path:
    from core.agent_eval.gate_artifacts import load_latest_gate
    from core.agent_eval.gate_delta import compute_delta_vs_previous

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    prev_path, prev = load_latest_gate()
    report["delta_vs_previous"] = compute_delta_vs_previous(
        report,
        prev,
        previous_artifact_name=prev_path.name if prev_path else None,
    )
    if path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = ARTIFACTS_DIR / f"agents_gate_{stamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
