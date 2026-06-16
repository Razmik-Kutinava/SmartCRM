#!/usr/bin/env python3
"""
Smoke quality gate: mock LLM → пустой JSON, enrich должен дотянуть ≥85% по агентам.
Hermes: fastpath/rescue без Ollama.

  cd backend && python scripts/run_gate_enrich_smoke.py
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["GROQ_API_KEY"] = ""

from core.agent_eval.cases import AGENT_IDS, load_hermes_cases
from core.agent_eval.gate import run_single_agent_gate, _summarize
from core.agent_eval.gate_config import AGENT_THRESHOLD_PCT, HERMES_THRESHOLD_PCT
from core.hermes.cache import fastpath_route
from core.hermes.rescue import post_verify, rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent


async def _mock_chat(*_a, **_k) -> str:
    return "{}"


async def run_hermes_rescue_gate() -> dict:
    rows = []
    for case in load_hermes_cases():
        text = case["text"]
        expected = case.get("expected_intent")
        raw = fastpath_route(text) or rescue_route(text)
        if raw:
            got = normalize_parsed_intent(text, raw).get("intent")
        else:
            got = post_verify(text, {"intent": "noop", "slots": {}}).get("intent")
        rows.append({
            "id": case.get("id"),
            "expected_intent": expected,
            "actual_intent": got,
            "passed": got == expected,
        })
    summary = _summarize(rows, HERMES_THRESHOLD_PCT)
    return {"agent": "hermes", "summary": summary, "results": rows}


def _patch_llm_mock() -> None:
    import agents.analyst.analyze as analyst_analyze
    import agents.economist as economist_mod
    import agents.marketer as marketer_mod
    import agents.strategist as strategist_mod
    import agents.tech_specialist as tech_mod
    import core.llm as llm_mod

    llm_mod.chat = _mock_chat  # type: ignore[method-assign]
    llm_mod.GROQ_API_KEY = ""
    for mod in (analyst_analyze, economist_mod, marketer_mod, strategist_mod, tech_mod):
        mod.chat = _mock_chat  # type: ignore[attr-defined]


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enrich smoke quality gate (mock LLM)")
    parser.add_argument("--write-acceptance", action="store_true")
    args = parser.parse_args(argv)

    _patch_llm_mock()

    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "enrich_smoke_mock_llm",
        "ollama": {"status": "skipped", "reason": "mock LLM + rescue"},
        "agents": {},
    }
    report["agents"]["hermes"] = await run_hermes_rescue_gate()
    for aid in AGENT_IDS:
        report["agents"][aid] = await run_single_agent_gate(aid)

    gates = [v["summary"]["gate"] for v in report["agents"].values()]
    report["overall_gate"] = "fail" if "fail" in gates else ("warn" if "warn" in gates else "pass")
    from core.agent_eval.acceptance_sync import build_gaps

    report["gaps"] = build_gaps(report)

    art_dir = Path(__file__).resolve().parents[1] / "data" / "artifacts" / "eval"
    art_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    art_path = art_dir / f"agents_gate_enrich_smoke_{stamp}.json"
    art_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.write_acceptance:
        from core.agent_eval.acceptance_sync import patch_acceptance_md

        patch_acceptance_md(report, art_path.name)
        print(f"Acceptance updated (enrich smoke): {art_path.name}")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    for key, block in report["agents"].items():
        s = block["summary"]
        print(f"{key}: {s['pass_rate_pct']}% ({s['passed']}/{s['total']}) gate={s['gate']}")
    print(f"Artifact: {art_path}")
    return 0 if report["overall_gate"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
