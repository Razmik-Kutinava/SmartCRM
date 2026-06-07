"""
Tender providers test suite (not only A/B).

Includes:
  - health/smoke (basic ok + non-empty)
  - A/A drift (repeat same config and compare stability)
  - load test (concurrency, error-rate, p95 latency)
  - contract test (minimum required fields & basic format checks)

Run:
  python scripts/tender_sources_tests.py health
  python scripts/tender_sources_tests.py aa --runs 2
  python scripts/tender_sources_tests.py load --seconds 10 --concurrency 5
  python scripts/tender_sources_tests.py contract
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from tender_sources_benchmark import run_benchmark  # type: ignore  # noqa: E402


DEFAULT_QUERIES = ["ремонт", "поставка", "строительство"]
DEFAULT_LAW = "all"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = round(0.95 * (len(values) - 1))
    return float(values[idx])


def _fmean(values: list[float]) -> float:
    return float(statistics.fmean(values)) if values else 0.0


def _drift_pp(a: float, b: float) -> float:
    return round(abs(b - a), 2)


def _as_list(x: Any) -> list:
    return x if isinstance(x, list) else []


def _require(cond: bool, msg: str, failures: list[str]) -> None:
    if not cond:
        failures.append(msg)


def _extract_sample_tenders(checks: list[dict[str, Any]], provider: str) -> list[dict[str, Any]]:
    # For tenderguru we can re-run benchmark and parse checks only; we keep checks compact.
    # This test uses /api/tenders formatting indirectly, so contract checks are intentionally minimal.
    out: list[dict[str, Any]] = []
    for c in checks:
        if c.get("provider") == provider and c.get("ok") and int(c.get("items", 0)) > 0:
            out.append(c)
    return out[:3]


async def test_health(queries: list[str], law: str) -> dict[str, Any]:
    res = await run_benchmark(queries=queries, law=law, runs=1)
    summary = res.get("summary", {})

    failures: list[str] = []
    for provider in ("gosplan", "tenderguru"):
        s = summary.get(provider, {}) or {}
        _require(int(s.get("calls", 0)) > 0, f"{provider}: no calls", failures)
        _require(int(s.get("ok_calls", 0)) == int(s.get("calls", 0)), f"{provider}: has failed calls", failures)
        # For health we require at least 1 non-empty response across queries.
        _require(int(s.get("calls_with_data", 0)) >= 1, f"{provider}: no data on health queries", failures)

    return {
        "type": "health",
        "ts": _now(),
        "law": law,
        "queries": queries,
        "summary": summary,
        "pass": len(failures) == 0,
        "failures": failures,
    }


async def test_aa(queries: list[str], law: str, runs: int) -> dict[str, Any]:
    # Repeat exact same benchmark twice (A/A) and check stability.
    a = await run_benchmark(queries=queries, law=law, runs=runs)
    b = await run_benchmark(queries=queries, law=law, runs=runs)
    sa, sb = a.get("summary", {}), b.get("summary", {})

    drift: dict[str, Any] = {}
    for provider in ("gosplan", "tenderguru"):
        drift[provider] = {
            "calls_with_data_drift": abs(int((sb.get(provider, {}) or {}).get("calls_with_data", 0)) - int((sa.get(provider, {}) or {}).get("calls_with_data", 0))),
            "p95_latency_drift_ms": _drift_pp(
                float((sa.get(provider, {}) or {}).get("p95_latency_ms", 0.0)),
                float((sb.get(provider, {}) or {}).get("p95_latency_ms", 0.0)),
            ),
            "avg_items_drift": _drift_pp(
                float((sa.get(provider, {}) or {}).get("avg_items", 0.0)),
                float((sb.get(provider, {}) or {}).get("avg_items", 0.0)),
            ),
        }

    # Simple stability rule-of-thumb (not stats): data drift must be 0 and p95 drift <= 2000ms.
    failures: list[str] = []
    for provider, d in drift.items():
        if int(d["calls_with_data_drift"]) != 0:
            failures.append(f"{provider}: calls_with_data drift={d['calls_with_data_drift']}")
        if float(d["p95_latency_drift_ms"]) > 2000:
            failures.append(f"{provider}: p95 drift too high ({d['p95_latency_drift_ms']}ms)")

    return {
        "type": "aa",
        "ts": _now(),
        "law": law,
        "queries": queries,
        "runs": runs,
        "a_summary": sa,
        "b_summary": sb,
        "drift": drift,
        "stable": len(failures) == 0,
        "failures": failures,
    }


@dataclass
class _LoadRow:
    ok: bool
    latency_ms: float
    items: int
    provider: str


async def test_load(queries: list[str], law: str, seconds: int, concurrency: int) -> dict[str, Any]:
    # Synthetic load: repeat benchmarks in parallel, measure throughput and error rate from checks.
    started = time.perf_counter()
    deadline = started + max(1, seconds)
    rows: list[_LoadRow] = []

    async def _one() -> None:
        nonlocal rows
        q = queries[int(time.time() * 1000) % len(queries)]
        res = await run_benchmark(queries=[q], law=law, runs=1)
        for c in _as_list(res.get("checks")):
            rows.append(
                _LoadRow(
                    ok=bool(c.get("ok")),
                    latency_ms=float(c.get("latency_ms", 0.0) or 0.0),
                    items=int(c.get("items", 0) or 0),
                    provider=str(c.get("provider", "")),
                )
            )

    async def _worker() -> None:
        while time.perf_counter() < deadline:
            try:
                await _one()
            except Exception:
                # do not crash load test
                pass

    await asyncio.gather(*[asyncio.create_task(_worker()) for _ in range(max(1, concurrency))])

    elapsed = max(0.001, time.perf_counter() - started)
    by_provider: dict[str, list[_LoadRow]] = {}
    for r in rows:
        by_provider.setdefault(r.provider, []).append(r)

    summary: dict[str, Any] = {}
    for provider, pr in by_provider.items():
        lat = [x.latency_ms for x in pr if x.latency_ms > 0]
        ok = [x for x in pr if x.ok]
        err = [x for x in pr if not x.ok]
        with_data = [x for x in ok if x.items > 0]
        summary[provider] = {
            "calls": len(pr),
            "ok_calls": len(ok),
            "error_calls": len(err),
            "calls_with_data": len(with_data),
            "error_rate_pct": round((len(err) / max(1, len(pr))) * 100.0, 2),
            "avg_latency_ms": round(_fmean(lat), 2) if lat else 0.0,
            "p95_latency_ms": round(_p95(lat), 2) if lat else 0.0,
            "rps": round(len(pr) / elapsed, 3),
        }

    return {
        "type": "load",
        "ts": _now(),
        "law": law,
        "queries": queries,
        "seconds": seconds,
        "concurrency": concurrency,
        "elapsed_s": round(elapsed, 3),
        "summary": summary,
    }


async def test_contract(queries: list[str], law: str) -> dict[str, Any]:
    res = await run_benchmark(queries=queries, law=law, runs=1)
    checks = _as_list(res.get("checks"))
    # Contract tests are intentionally minimal and API-agnostic:
    # - ok responses must have non-negative items, positive latency
    # - when items > 0 we expect provider string and query echo
    failures: list[str] = []
    for c in checks:
        _require("provider" in c, "missing provider", failures)
        _require("query" in c, "missing query", failures)
        _require(isinstance(c.get("ok"), bool), "ok is not bool", failures)
        _require(float(c.get("latency_ms", 0.0) or 0.0) >= 0.0, "latency_ms < 0", failures)
        _require(int(c.get("items", 0) or 0) >= 0, "items < 0", failures)
        if c.get("ok") and int(c.get("items", 0) or 0) > 0:
            _require(str(c.get("provider")) in ("gosplan", "tenderguru"), "unknown provider", failures)
            _require(str(c.get("query")).strip() != "", "empty query", failures)

    # Extra: require at least one positive items per provider on contract queries.
    for provider in ("gosplan", "tenderguru"):
        has_data = any(c.get("provider") == provider and c.get("ok") and int(c.get("items", 0) or 0) > 0 for c in checks)
        _require(has_data, f"{provider}: no non-empty response on contract queries", failures)

    return {
        "type": "contract",
        "ts": _now(),
        "law": law,
        "queries": queries,
        "pass": len(failures) == 0,
        "failures": failures,
    }


def _parse_list(raw: str, fallback: list[str]) -> list[str]:
    raw = (raw or "").strip()
    if not raw:
        return fallback
    return [x.strip() for x in raw.split(",") if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Tender providers test suite.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_health = sub.add_parser("health")
    p_health.add_argument("--queries", default=",".join(DEFAULT_QUERIES))
    p_health.add_argument("--law", default=DEFAULT_LAW)
    p_health.add_argument("--save", default="", help="Optional: save JSON to this path (relative to backend/)")

    p_aa = sub.add_parser("aa")
    p_aa.add_argument("--queries", default=",".join(DEFAULT_QUERIES))
    p_aa.add_argument("--law", default=DEFAULT_LAW)
    p_aa.add_argument("--runs", type=int, default=2)
    p_aa.add_argument("--save", default="", help="Optional: save JSON to this path (relative to backend/)")

    p_load = sub.add_parser("load")
    p_load.add_argument("--queries", default=",".join(DEFAULT_QUERIES))
    p_load.add_argument("--law", default=DEFAULT_LAW)
    p_load.add_argument("--seconds", type=int, default=10)
    p_load.add_argument("--concurrency", type=int, default=5)
    p_load.add_argument("--save", default="", help="Optional: save JSON to this path (relative to backend/)")

    p_contract = sub.add_parser("contract")
    p_contract.add_argument("--queries", default=",".join(DEFAULT_QUERIES))
    p_contract.add_argument("--law", default=DEFAULT_LAW)
    p_contract.add_argument("--save", default="", help="Optional: save JSON to this path (relative to backend/)")
    args = ap.parse_args()

    queries = _parse_list(getattr(args, "queries", ""), DEFAULT_QUERIES)
    law = str(getattr(args, "law", DEFAULT_LAW))

    if args.cmd == "health":
        payload = asyncio.run(test_health(queries, law))
    elif args.cmd == "aa":
        payload = asyncio.run(test_aa(queries, law, runs=max(1, int(args.runs))))
    elif args.cmd == "load":
        payload = asyncio.run(test_load(queries, law, seconds=int(args.seconds), concurrency=int(args.concurrency)))
    else:
        payload = asyncio.run(test_contract(queries, law))

    if getattr(args, "save", ""):
        out = Path(__file__).resolve().parent.parent / str(args.save)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

