"""
Feature rollout benchmark through the real Hermes runtime path (parse_intent).
Runs isolated A/B stages for optimization features.

Usage:
  cd backend
  python scripts/run_hermes_parse_rollout.py --status all --repeat 3
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from typing import Any

import httpx
from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models.eval_scenario import EvalScenario
from db.session import SessionLocal
from core.hermes import parse_intent
from core.hermes import config as hermes_module


def _read_groq_tokens() -> tuple[int, int]:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "api_stats.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        groq = data.get("groq", {})
        return int(groq.get("tokens_prompt_today", 0)), int(groq.get("tokens_completion_today", 0))
    except Exception:
        return (0, 0)


async def _load_cases(status: str) -> list[dict[str, Any]]:
    async with SessionLocal() as db:
        q = select(EvalScenario).order_by(EvalScenario.id)
        if status != "all":
            q = q.where(EvalScenario.status == status)
        rows = (await db.execute(q)).scalars().all()
    return [{"text": r.phrase, "expected": r.expected_intent} for r in rows]


def _configure_stage(stage: str) -> None:
    # baseline defaults
    hermes_module.HERMES_ENABLE_FASTPATH = False
    hermes_module.HERMES_ENABLE_POST_VERIFY = False
    hermes_module.HERMES_ENABLE_CACHE = False
    hermes_module.HERMES_ENABLE_MEMORY = False
    hermes_module.HERMES_ENABLE_CONTEXT_COMPRESS = False
    hermes_module.HERMES_ENABLE_CONTEXT_HYGIENE = False
    hermes_module.HERMES_ENABLE_CONTEXT_PROFILE = False
    hermes_module.HERMES_ENABLE_QUANT_MODEL = False
    hermes_module.HERMES_ENABLE_OLLAMA_PRELOAD = False
    hermes_module.HERMES_ENABLE_GPU_OFFLOAD = False
    hermes_module.HERMES_ROUTING_POLICY = "default"
    hermes_module.HERMES_PROMPT_PROFILE = ""
    hermes_module._preloaded_models.clear()

    if stage == "f1_context_profile":
        hermes_module.HERMES_ENABLE_CONTEXT_PROFILE = True
    elif stage == "f2_quant_model":
        hermes_module.HERMES_ENABLE_QUANT_MODEL = True
    elif stage == "f3_keepalive_preload":
        hermes_module.HERMES_ENABLE_OLLAMA_PRELOAD = True
    elif stage == "f4_gpu_offload":
        hermes_module.HERMES_ENABLE_GPU_OFFLOAD = True
    elif stage == "f5_parallelism":
        # tested in runner (parallel request pattern)
        pass
    elif stage == "f6_context_hygiene":
        hermes_module.HERMES_ENABLE_CONTEXT_HYGIENE = True
        hermes_module.HERMES_ENABLE_CONTEXT_COMPRESS = True
    elif stage == "f7_routing_policy":
        hermes_module.HERMES_ROUTING_POLICY = "local_first"
    elif stage == "f8_full_stack":
        hermes_module.HERMES_ENABLE_CONTEXT_PROFILE = True
        hermes_module.HERMES_ENABLE_QUANT_MODEL = True
        hermes_module.HERMES_ENABLE_OLLAMA_PRELOAD = True
        hermes_module.HERMES_ENABLE_GPU_OFFLOAD = True
        hermes_module.HERMES_ENABLE_CONTEXT_HYGIENE = True
        hermes_module.HERMES_ENABLE_CONTEXT_COMPRESS = True
        hermes_module.HERMES_ROUTING_POLICY = "local_first"
    elif stage == "f9_recommended_profile":
        # Proven-safe stack from per-feature gate:
        # context profile + gpu offload + context hygiene + routing policy.
        hermes_module.HERMES_ENABLE_CONTEXT_PROFILE = True
        hermes_module.HERMES_ENABLE_GPU_OFFLOAD = True
        hermes_module.HERMES_ENABLE_CONTEXT_HYGIENE = True
        hermes_module.HERMES_ENABLE_CONTEXT_COMPRESS = True
        hermes_module.HERMES_ROUTING_POLICY = "local_first"

    hermes_module._intent_cache.clear()


def _ollama_available() -> bool:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        r = httpx.get(f"{host}/api/tags", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


async def _run_stage(stage: str, cases: list[dict[str, Any]]) -> dict[str, Any]:
    _configure_stage(stage)
    ollama_related = stage in {
        "f1_context_profile",
        "f2_quant_model",
        "f3_keepalive_preload",
        "f4_gpu_offload",
        "f7_routing_policy",
        "f8_full_stack",
        "f9_recommended_profile",
    }
    ollama_unavailable = ollama_related and not _ollama_available()
    if ollama_unavailable:
        hermes_module.HERMES_ROUTING_POLICY = "default"
        hermes_module.HERMES_ENABLE_CONTEXT_PROFILE = False
        hermes_module.HERMES_ENABLE_QUANT_MODEL = False
        hermes_module.HERMES_ENABLE_OLLAMA_PRELOAD = False
        hermes_module.HERMES_ENABLE_GPU_OFFLOAD = False

    before_p, before_c = _read_groq_tokens()
    total = len(cases)
    correct = 0
    errors = 0
    times: list[int] = []
    t_stage_start = time.monotonic()

    async def run_one(row: dict[str, Any]) -> tuple[bool, int, bool]:
        t0 = time.monotonic()
        try:
            parsed = await parse_intent(row["text"])
            elapsed = round((time.monotonic() - t0) * 1000)
            return True, elapsed, parsed.get("intent") == row["expected"]
        except Exception:
            return False, 0, False

    if stage == "f5_parallelism":
        sem = asyncio.Semaphore(4)

        async def run_with_sem(row: dict[str, Any]) -> tuple[bool, int, bool]:
            async with sem:
                return await run_one(row)

        results = await asyncio.gather(*(run_with_sem(r) for r in cases))
    else:
        results = [await run_one(r) for r in cases]

    for ok, elapsed, is_correct in results:
        if ok:
            times.append(elapsed)
            if is_correct:
                correct += 1
        else:
            errors += 1

    after_p, after_c = _read_groq_tokens()
    usage = {
        "prompt_tokens": max(0, after_p - before_p),
        "completion_tokens": max(0, after_c - before_c),
    }
    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
    sorted_times = sorted(times)
    if sorted_times:
        idx = max(0, min(len(sorted_times) - 1, int(len(sorted_times) * 0.95) - 1))
        p95 = sorted_times[idx]
    else:
        p95 = 0
    elapsed_s = max(0.001, time.monotonic() - t_stage_start)
    throughput_rps = round(total / elapsed_s, 3)

    return {
        "stage": stage,
        "ollama_unavailable_fallback": ollama_unavailable,
        "kpi": {
            "cases_total": total,
            "cases_success": total - errors,
            "error_rate_pct": round((errors / total) * 100, 2) if total else 0.0,
            "accuracy_pct": round((correct / total) * 100, 2) if total else 0.0,
            "avg_ms": round(sum(times) / len(times)) if times else 0,
            "p95_ms": p95,
            "throughput_rps": throughput_rps,
        },
        "usage": usage,
    }


def _pct(old: float, new: float) -> float:
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100.0


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", default="all", help="approved|draft|pending_review|archived|all")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    base_cases = await _load_cases(args.status)
    if not base_cases:
        print(json.dumps({"error": f"No scenarios found for status={args.status}"}))
        return
    cases = base_cases * max(1, args.repeat)

    stages = [
        "baseline",
        "f1_context_profile",
        "f2_quant_model",
        "f3_keepalive_preload",
        "f4_gpu_offload",
        "f5_parallelism",
        "f6_context_hygiene",
        "f7_routing_policy",
        "f8_full_stack",
        "f9_recommended_profile",
    ]
    rows = []
    for s in stages:
        rows.append(await _run_stage(s, cases))

    baseline = rows[0]
    for row in rows:
        row["delta_vs_baseline"] = {
            "accuracy_pct_points": round(row["kpi"]["accuracy_pct"] - baseline["kpi"]["accuracy_pct"], 2),
            "avg_ms_pct": round(_pct(baseline["kpi"]["avg_ms"], row["kpi"]["avg_ms"]), 2),
            "error_rate_pct_points": round(row["kpi"]["error_rate_pct"] - baseline["kpi"]["error_rate_pct"], 2),
            "p95_ms_pct": round(_pct(baseline["kpi"]["p95_ms"], row["kpi"]["p95_ms"]), 2),
            "throughput_rps_pct": round(_pct(baseline["kpi"]["throughput_rps"], row["kpi"]["throughput_rps"]), 2),
            "prompt_tokens_pct": round(_pct(baseline["usage"]["prompt_tokens"], row["usage"]["prompt_tokens"]), 2),
            "total_tokens_pct": round(_pct(baseline["usage"]["total_tokens"], row["usage"]["total_tokens"]), 2),
        }

    payload = {
        "status_filter": args.status,
        "repeat": args.repeat,
        "cases_count": len(cases),
        "stages": rows,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
