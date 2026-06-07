"""
One-command A/B check for Hermes routing modes.

Runs eval twice on real DB scenarios:
1) full prompt mode
2) compact prompt mode

Then prints KPI deltas:
- accuracy
- avg latency
- error rate
- Groq token usage delta (from data/api_stats.json)

Usage (from backend/):
  python scripts/run_hermes_ab_check.py --status approved --models groq
  python scripts/run_hermes_ab_check.py --status all --models groq
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
API_STATS_PATH = ROOT / "data" / "api_stats.json"
EVAL_COMPARE_PATH = ROOT / "scripts" / "eval_compare_modes.py"


def _read_groq_tokens() -> tuple[int, int]:
    if not API_STATS_PATH.exists():
        return (0, 0)
    try:
        data = json.loads(API_STATS_PATH.read_text(encoding="utf-8"))
        groq = data.get("groq", {})
        prompt = int(groq.get("tokens_prompt_today", 0))
        completion = int(groq.get("tokens_completion_today", 0))
        return (prompt, completion)
    except Exception:
        return (0, 0)


def _extract_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Cannot find JSON payload in command output")
    return json.loads(text[start : end + 1])


def _run_mode(
    status: str,
    models: list[str],
    prompt_mode: str,
    max_tokens: int,
) -> tuple[dict[str, Any], dict[str, int]]:
    env = os.environ.copy()
    env["HERMES_PROMPT_MODE"] = prompt_mode
    env["HERMES_MAX_TOKENS"] = str(max_tokens)

    before_prompt, before_completion = _read_groq_tokens()
    cmd = [
        sys.executable,
        str(EVAL_COMPARE_PATH),
        "--status",
        status,
        "--models",
        *models,
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Mode '{prompt_mode}' failed.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )

    payload = _extract_json(proc.stdout)
    after_prompt, after_completion = _read_groq_tokens()
    usage = {
        "prompt_tokens": max(0, after_prompt - before_prompt),
        "completion_tokens": max(0, after_completion - before_completion),
    }
    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
    return payload, usage


def _kpi_for_model(payload: dict[str, Any], model: str) -> dict[str, Any]:
    for row in payload.get("kpis", []):
        if row.get("model") == model:
            return row
    return {
        "model": model,
        "cases_total": 0,
        "cases_success": 0,
        "error_rate_pct": 100.0,
        "accuracy_pct": 0.0,
        "avg_ms": 0,
    }


def _pct_change(old: float, new: float) -> float:
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100.0


def main() -> None:
    parser = argparse.ArgumentParser(description="A/B KPI check for Hermes routing modes")
    parser.add_argument("--status", default="approved", help="approved|draft|pending_review|archived|all")
    parser.add_argument("--models", nargs="+", default=["groq"], help="Models for eval_compare_modes")
    parser.add_argument("--full-max-tokens", type=int, default=192)
    parser.add_argument("--compact-max-tokens", type=int, default=120)
    parser.add_argument("--output", default="", help="Optional path to save report JSON")
    args = parser.parse_args()

    model_for_report = "groq" if "groq" in args.models else args.models[0]

    full_payload, full_usage = _run_mode(
        status=args.status,
        models=args.models,
        prompt_mode="full",
        max_tokens=args.full_max_tokens,
    )
    compact_payload, compact_usage = _run_mode(
        status=args.status,
        models=args.models,
        prompt_mode="compact",
        max_tokens=args.compact_max_tokens,
    )

    full_kpi = _kpi_for_model(full_payload, model_for_report)
    compact_kpi = _kpi_for_model(compact_payload, model_for_report)

    report = {
        "status_filter": args.status,
        "models": args.models,
        "full": {
            "kpi": full_kpi,
            "usage": full_usage,
        },
        "compact": {
            "kpi": compact_kpi,
            "usage": compact_usage,
        },
        "delta": {
            "accuracy_pct_points": round(
                float(compact_kpi.get("accuracy_pct", 0)) - float(full_kpi.get("accuracy_pct", 0)), 2
            ),
            "avg_ms_pct": round(
                _pct_change(float(full_kpi.get("avg_ms", 0)), float(compact_kpi.get("avg_ms", 0))), 2
            ),
            "error_rate_pct_points": round(
                float(compact_kpi.get("error_rate_pct", 0)) - float(full_kpi.get("error_rate_pct", 0)), 2
            ),
            "prompt_tokens_pct": round(
                _pct_change(float(full_usage["prompt_tokens"]), float(compact_usage["prompt_tokens"])), 2
            ),
            "total_tokens_pct": round(
                _pct_change(float(full_usage["total_tokens"]), float(compact_usage["total_tokens"])), 2
            ),
        },
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.output:
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
