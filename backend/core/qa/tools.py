"""Dr. QA — диспетчер инструментов."""
import json
from dataclasses import asdict

from .experiments import (
    get_current_kpis,
    run_aa_test,
    run_ab_test,
    run_kpi_gate,
    run_tender_sources_test,
    run_tender_suite,
)
from .registry import HypothesisRegistry

_registry = HypothesisRegistry()


def get_registry() -> HypothesisRegistry:
    return _registry


def dispatch_tool(tool: str, args: dict) -> str:
    try:
        if tool == "run_aa_test":
            return json.dumps(run_aa_test(**args), ensure_ascii=False)
        if tool == "run_ab_test":
            return json.dumps(run_ab_test(**args), ensure_ascii=False)
        if tool == "run_kpi_gate":
            return json.dumps(run_kpi_gate(**args), ensure_ascii=False)
        if tool == "run_tender_sources_test":
            return json.dumps(run_tender_sources_test(**args), ensure_ascii=False)
        if tool == "run_tender_suite":
            return json.dumps(run_tender_suite(**args), ensure_ascii=False)
        if tool == "set_canary":
            _registry.set_canary(args["hypothesis_id"], args.get("pct", 5), args.get("ttl_hours", 24))
            return json.dumps({"ok": True, "pct": args.get("pct", 5)})
        if tool == "rollback":
            _registry.rollback(args["hypothesis_id"])
            return json.dumps({"ok": True, "rolled_back": args["hypothesis_id"]})
        if tool == "list_hypotheses":
            hs = _registry.list(status=args.get("status"))
            return json.dumps([asdict(h) for h in hs], ensure_ascii=False)
        if tool == "add_hypothesis":
            h = _registry.add(**args)
            return json.dumps(asdict(h), ensure_ascii=False)
        if tool == "get_current_kpis":
            return json.dumps(get_current_kpis(), ensure_ascii=False)
        return json.dumps({"error": f"unknown tool: {tool}"})
    except Exception as e:
        return json.dumps({"error": str(e)})
