"""
Sequential feature rollout benchmark for Hermes.

Runs a stable baseline and feature stages on the same real DB scenarios,
measuring:
- accuracy
- avg latency
- error rate
- Groq prompt/completion token deltas

Usage:
  cd backend
  python scripts/run_hermes_feature_rollout.py --status all --models groq
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
EVAL_COMPARE = ROOT / "scripts" / "eval_compare_modes.py"


def read_groq_counters() -> tuple[int, int]:
    if not API_STATS_PATH.exists():
        return (0, 0)
    try:
        data = json.loads(API_STATS_PATH.read_text(encoding="utf-8"))
        groq = data.get("groq", {})
        return int(groq.get("tokens_prompt_today", 0)), int(groq.get("tokens_completion_today", 0))
    except Exception:
        return (0, 0)


def extract_json_block(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("JSON payload not found in output")
    return json.loads(text[start : end + 1])


def run_stage(
    stage_name: str,
    status: str,
    models: list[str],
    repeat: int,
    stage_env: dict[str, str],
) -> dict[str, Any]:
    env = os.environ.copy()
    env.update(stage_env)
    before_p, before_c = read_groq_counters()
    cmd = [
        sys.executable,
        str(EVAL_COMPARE),
        "--status",
        status,
        "--models",
        *models,
        "--repeat",
        str(repeat),
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
        raise RuntimeError(f"Stage {stage_name} failed.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    payload = extract_json_block(proc.stdout)
    after_p, after_c = read_groq_counters()

    model = "groq" if "groq" in models else models[0]
    kpi = next((r for r in payload.get("kpis", []) if r.get("model") == model), {})
    usage = {
        "prompt_tokens": max(0, after_p - before_p),
        "completion_tokens": max(0, after_c - before_c),
    }
    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

    return {
        "stage": stage_name,
        "env": stage_env,
        "kpi": kpi,
        "usage": usage,
    }


def pct(old: float, new: float) -> float:
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run staged Hermes feature benchmark")
    parser.add_argument("--status", default="all")
    parser.add_argument("--models", nargs="+", default=["groq"])
    parser.add_argument("--repeat", type=int, default=1, help="Repeat scenarios to expose cache wins")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    stages = [
        (
            "baseline",
            {
                "HERMES_PROMPT_MODE": "compact",
                "HERMES_MAX_TOKENS": "120",
                "HERMES_ENABLE_FASTPATH": "0",
                "HERMES_ENABLE_POST_VERIFY": "0",
                "HERMES_ENABLE_CACHE": "0",
            },
        ),
        (
            "fastpath",
            {
                "HERMES_PROMPT_MODE": "compact",
                "HERMES_MAX_TOKENS": "120",
                "HERMES_ENABLE_FASTPATH": "1",
                "HERMES_ENABLE_POST_VERIFY": "0",
                "HERMES_ENABLE_CACHE": "0",
            },
        ),
        (
            "fastpath_plus_verify",
            {
                "HERMES_PROMPT_MODE": "compact",
                "HERMES_MAX_TOKENS": "120",
                "HERMES_ENABLE_FASTPATH": "1",
                "HERMES_ENABLE_POST_VERIFY": "1",
                "HERMES_ENABLE_CACHE": "0",
            },
        ),
        (
            "all_features",
            {
                "HERMES_PROMPT_MODE": "compact",
                "HERMES_MAX_TOKENS": "120",
                "HERMES_ENABLE_FASTPATH": "1",
                "HERMES_ENABLE_POST_VERIFY": "1",
                "HERMES_ENABLE_CACHE": "1",
            },
        ),
    ]

    rows = [run_stage(name, args.status, args.models, args.repeat, env) for name, env in stages]
    baseline = rows[0]
    report_rows = []
    for row in rows:
        rb = {
            "stage": row["stage"],
            "kpi": row["kpi"],
            "usage": row["usage"],
            "delta_vs_baseline": {
                "accuracy_pct_points": round(
                    float(row["kpi"].get("accuracy_pct", 0)) - float(baseline["kpi"].get("accuracy_pct", 0)),
                    2,
                ),
                "avg_ms_pct": round(
                    pct(float(baseline["kpi"].get("avg_ms", 0)), float(row["kpi"].get("avg_ms", 0))),
                    2,
                ),
                "error_rate_pct_points": round(
                    float(row["kpi"].get("error_rate_pct", 0)) - float(baseline["kpi"].get("error_rate_pct", 0)),
                    2,
                ),
                "prompt_tokens_pct": round(
                    pct(float(baseline["usage"]["prompt_tokens"]), float(row["usage"]["prompt_tokens"])),
                    2,
                ),
                "total_tokens_pct": round(
                    pct(float(baseline["usage"]["total_tokens"]), float(row["usage"]["total_tokens"])),
                    2,
                ),
            },
        }
        report_rows.append(rb)

    final = {
        "status_filter": args.status,
        "models": args.models,
        "repeat": args.repeat,
        "stages": report_rows,
    }
    print(json.dumps(final, ensure_ascii=False, indent=2))

    if args.output:
        out = Path(args.output)
        if not out.is_absolute():
            out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
