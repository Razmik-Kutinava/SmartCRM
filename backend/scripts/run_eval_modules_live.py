#!/usr/bin/env python3
"""Live LLM eval модулей Hermes (Ф2) — Groq + Ollama, не rescue.

Запуск из backend:
  python scripts/run_eval_modules_live.py
  python scripts/run_eval_modules_live.py --full --log-file data/artifacts/eval/modules_live.log
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.eval_runner import eval_one_case
from core.hermes.slot_normalize import normalize_parsed_intent

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CASES = REPO / "eval" / "cases_modules.jsonl"
ALL_CASES = REPO / "eval" / "cases.jsonl"
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "data" / "artifacts" / "eval"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def score_row(case: dict, raw: dict) -> dict:
    if raw.get("error"):
        return {"ok": False, "error": raw["error"], **raw}
    parsed = normalize_parsed_intent(
        case["text"],
        {
            "intent": raw.get("intent") or "",
            "slots": raw.get("slots") or {},
            "agents": [],
            "parallel": False,
            "reply": raw.get("reply") or "",
            "_model": raw.get("model") or "eval",
        },
    )
    checks = {
        "intent": parsed.get("intent") == case.get("expected_intent"),
        "module": parsed.get("module") == case.get("expected_module"),
        "ui_action": parsed.get("ui_action") == case.get("expected_ui_action"),
    }
    slot_ok = True
    for k, v in (case.get("expected_slots") or {}).items():
        got = (parsed.get("slots") or {}).get(k)
        if isinstance(v, (int, float)):
            try:
                slot_ok = slot_ok and float(got) == float(v)
            except (TypeError, ValueError):
                slot_ok = False
        else:
            slot_ok = slot_ok and str(got or "").lower() == str(v).lower()
    checks["slots"] = slot_ok
    ok = all(checks.values())
    return {
        "ok": ok,
        "checks": checks,
        "intent": parsed.get("intent"),
        "module": parsed.get("module"),
        "ui_action": parsed.get("ui_action"),
        "slots": parsed.get("slots"),
        "duration_ms": raw.get("duration_ms"),
        "model": raw.get("model"),
    }


async def run_model(cases: list[dict], model: str, log) -> dict:
    results = []
    ok_n = 0
    for i, case in enumerate(cases, 1):
        log(f"[{model}] {i}/{len(cases)} {case['id']}: {case['text'][:50]}...")
        raw = await eval_one_case(case["text"], case.get("expected_intent"), model)
        row = {"id": case["id"], "text": case["text"], **score_row(case, raw)}
        results.append(row)
        if row.get("ok"):
            ok_n += 1
        else:
            log(f"  FAIL checks={row.get('checks')} intent={row.get('intent')}")
        if model == "groq" and i < len(cases):
            await asyncio.sleep(2.5)
    acc = round(ok_n / len(cases) * 100, 1) if cases else 0
    return {"model": model, "total": len(cases), "passed": ok_n, "accuracy_pct": acc, "results": results}


async def main_async(args: argparse.Namespace) -> dict:
    cases = load_jsonl(Path(args.cases))
    if args.full:
        extra = load_jsonl(ALL_CASES)
        seen = {c["text"] for c in cases}
        for row in extra:
            if row["text"] not in seen:
                cases.append(row)
                seen.add(row["text"])
    if args.limit:
        cases = cases[: args.limit]

    models = []
    if os.getenv("GROQ_API_KEY"):
        models.append("groq")
    models.append("hermes3")

    log_lines: list[str] = []

    def log(msg: str) -> None:
        line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
        log_lines.append(line)
        print(msg, flush=True)
        if args.log_file:
            Path(args.log_file).parent.mkdir(parents=True, exist_ok=True)
            with open(args.log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    log(f"Live eval modules: {len(cases)} cases, models={models}")
    by_model = []
    for m in models:
        by_model.append(await run_model(cases, m, log))
        log(f"--- {m}: {by_model[-1]['passed']}/{by_model[-1]['total']} ({by_model[-1]['accuracy_pct']}%) ---")

    payload = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "cases_file": str(args.cases),
        "full": args.full,
        "cases_count": len(cases),
        "models": by_model,
    }
    out = Path(args.save) if args.save else ARTIFACT_DIR / f"modules_live_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Artifact: {out}")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=str(DEFAULT_CASES))
    ap.add_argument("--full", action="store_true", help="Добавить eval/cases.jsonl")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--save", default="")
    ap.add_argument("--log-file", default="")
    args = ap.parse_args()
    asyncio.run(main_async(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
