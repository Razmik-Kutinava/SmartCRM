"""
Baseline benchmark for tender providers (Gosplan + TenderGuru).

Usage examples:
  python scripts/tender_sources_benchmark.py --law 44 --runs 1
  python scripts/tender_sources_benchmark.py --queries "битрикс crm,1с интеграция" --save data/tender_sources_baseline.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.gosplan import GosplanAPI  # noqa: E402
from services.tenderguru import TenderGuruClient  # noqa: E402


DEFAULT_QUERIES = [
    "битрикс24",
    "crm система",
    "внедрение crm",
]


def _load_env_value(key: str) -> str:
    val = os.getenv(key, "").strip()
    if val:
        return val

    dotenv_candidates = [ROOT.parent / ".env", ROOT / ".env"]
    for path in dotenv_candidates:
        if not path.exists():
            continue
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip("\"").strip("'")
        except Exception:
            continue
    return ""


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    values = sorted(values)
    idx = round(0.95 * (len(values) - 1))
    return values[idx]


def _safe_avg(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _parse_tenderguru_count(raw: Any) -> int:
    try:
        formatted = TenderGuruClient.format_search_response(raw)
        return int(formatted.get("total", 0))
    except Exception:
        if isinstance(raw, list):
            return len(raw)
        if isinstance(raw, dict):
            return sum(1 for v in raw.values() if isinstance(v, dict))
        return 0


async def _probe_gosplan(query: str, law: str) -> dict[str, Any]:
    started = time.perf_counter()
    client = GosplanAPI(use_prod=False)
    try:
        data = await client.search_purchases(kwords=query, fz=law, limit=30, skip=0)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        error = data.get("error") if isinstance(data, dict) else "invalid_response"
        purchases = data.get("purchases", []) if isinstance(data, dict) else []
        return {
            "provider": "gosplan",
            "query": query,
            "ok": not bool(error),
            "items": len(purchases) if isinstance(purchases, list) else 0,
            "latency_ms": elapsed_ms,
            "error": error,
        }
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "provider": "gosplan",
            "query": query,
            "ok": False,
            "items": 0,
            "latency_ms": elapsed_ms,
            "error": str(e),
        }


async def _probe_tenderguru(query: str, law: str) -> dict[str, Any]:
    api_key = _load_env_value("TENDERGURU_API_KEY")
    if not api_key:
        return {
            "provider": "tenderguru",
            "query": query,
            "ok": False,
            "items": 0,
            "latency_ms": 0.0,
            "error": "TENDERGURU_API_KEY is not set",
            "skipped": True,
        }

    started = time.perf_counter()
    client = TenderGuruClient(api_key)
    try:
        data = await client.search_tenders(
            kwords=query,
            fz=None if law == "all" else law,
            page=1,
            actual=1,
            sort_by="by_date_end",
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        count = _parse_tenderguru_count(data)
        return {
            "provider": "tenderguru",
            "query": query,
            "ok": True,
            "items": count,
            "latency_ms": elapsed_ms,
            "error": None,
        }
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "provider": "tenderguru",
            "query": query,
            "ok": False,
            "items": 0,
            "latency_ms": elapsed_ms,
            "error": str(e),
        }


def _summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    by_provider: dict[str, list[dict[str, Any]]] = {}
    for row in checks:
        by_provider.setdefault(row["provider"], []).append(row)

    summary: dict[str, Any] = {}
    for provider, rows in by_provider.items():
        latencies = [float(r.get("latency_ms", 0.0)) for r in rows if float(r.get("latency_ms", 0.0)) > 0]
        items = [int(r.get("items", 0)) for r in rows]
        errors = [r for r in rows if r.get("error") and not r.get("skipped")]
        skipped = [r for r in rows if r.get("skipped")]
        ok_rows = [r for r in rows if r.get("ok")]
        with_data = [r for r in ok_rows if int(r.get("items", 0)) > 0]

        summary[provider] = {
            "calls": len(rows),
            "ok_calls": len(ok_rows),
            "calls_with_data": len(with_data),
            "error_calls": len(errors),
            "skipped_calls": len(skipped),
            "avg_latency_ms": round(_safe_avg(latencies), 2) if latencies else 0.0,
            "p95_latency_ms": round(_p95(latencies), 2) if latencies else 0.0,
            "avg_items": round(_safe_avg(items), 2) if items else 0.0,
        }

    return summary


async def run_benchmark(queries: list[str], law: str, runs: int) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for _ in range(max(runs, 1)):
        for query in queries:
            gp, tg = await asyncio.gather(
                _probe_gosplan(query, law),
                _probe_tenderguru(query, law),
            )
            checks.append(gp)
            checks.append(tg)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "law": law,
        "runs": max(runs, 1),
        "queries": queries,
        "checks": checks,
        "summary": _summarize(checks),
    }


def _parse_queries(raw: str) -> list[str]:
    if not raw.strip():
        return DEFAULT_QUERIES
    return [x.strip() for x in raw.split(",") if x.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Gosplan and TenderGuru providers.")
    parser.add_argument("--queries", default=",".join(DEFAULT_QUERIES), help="Comma-separated query list")
    parser.add_argument("--law", default="44", help="44, 223, 615 or all")
    parser.add_argument("--runs", type=int, default=1, help="How many times to repeat each query")
    parser.add_argument(
        "--save",
        default=str(ROOT / "data" / "tender_sources_baseline.json"),
        help="Path to output JSON file",
    )
    args = parser.parse_args()

    queries = _parse_queries(args.queries)
    payload = asyncio.run(run_benchmark(queries=queries, law=args.law, runs=args.runs))

    save_path = Path(args.save)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"ok": True, "save": str(save_path), "summary": payload["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
