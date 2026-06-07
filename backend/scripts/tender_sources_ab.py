"""
A/B runner for tender providers (Gosplan + TenderGuru).

Compares two benchmark configurations and prints delta summary.

Example (из каталога backend/):
  python scripts/tender_sources_ab.py --runs 2 --save data/tender_sources_ab.json

Артефакты только в backend/data/ — не запускать из корня репо (иначе появится backend/backend/data/).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from tender_sources_benchmark import run_benchmark  # type: ignore  # noqa: E402
import asyncio  # noqa: E402


BASELINE_QUERIES = ["битрикс24", "crm система", "внедрение crm"]
VARIANT_QUERIES = ["ремонт", "поставка", "строительство"]


def _pct(a: float, b: float) -> float | None:
    if a == 0:
        return None
    return round(((b - a) / a) * 100.0, 2)


def _pick(summary: dict[str, Any], provider: str, key: str, default: float = 0.0) -> float:
    try:
        return float(summary.get(provider, {}).get(key, default))
    except Exception:
        return float(default)


def _delta(base: dict[str, Any], var: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for provider in sorted(set(base.keys()) | set(var.keys())):
        b = base.get(provider, {}) or {}
        v = var.get(provider, {}) or {}

        out[provider] = {
            "calls_with_data": {
                "baseline": int(b.get("calls_with_data", 0)),
                "variant": int(v.get("calls_with_data", 0)),
            },
            "avg_items": {
                "baseline": float(b.get("avg_items", 0.0)),
                "variant": float(v.get("avg_items", 0.0)),
                "delta_abs": round(float(v.get("avg_items", 0.0)) - float(b.get("avg_items", 0.0)), 2),
            },
            "p95_latency_ms": {
                "baseline": float(b.get("p95_latency_ms", 0.0)),
                "variant": float(v.get("p95_latency_ms", 0.0)),
                "delta_pct": _pct(float(b.get("p95_latency_ms", 0.0)), float(v.get("p95_latency_ms", 0.0))) ,
            },
        }
    return out


async def run_ab(
    runs: int,
    baseline_queries: list[str],
    baseline_law: str,
    variant_queries: list[str],
    variant_law: str,
) -> dict[str, Any]:
    baseline = await run_benchmark(queries=baseline_queries, law=baseline_law, runs=runs)
    variant = await run_benchmark(queries=variant_queries, law=variant_law, runs=runs)
    return {
        "baseline": {
            "law": baseline_law,
            "queries": baseline_queries,
            "summary": baseline.get("summary", {}),
        },
        "variant": {
            "law": variant_law,
            "queries": variant_queries,
            "summary": variant.get("summary", {}),
        },
        "delta": _delta(baseline.get("summary", {}), variant.get("summary", {})),
    }


def _parse_list(raw: str, fallback: list[str]) -> list[str]:
    raw = (raw or "").strip()
    if not raw:
        return fallback
    return [x.strip() for x in raw.split(",") if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="A/B compare tender providers benchmarks.")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--baseline-queries", default=",".join(BASELINE_QUERIES))
    ap.add_argument("--baseline-law", default="44")
    ap.add_argument("--variant-queries", default=",".join(VARIANT_QUERIES))
    ap.add_argument("--variant-law", default="all")
    ap.add_argument("--save", default=str(ROOT / "data" / "tender_sources_ab.json"))
    args = ap.parse_args()

    payload = asyncio.run(
        run_ab(
            runs=max(args.runs, 1),
            baseline_queries=_parse_list(args.baseline_queries, BASELINE_QUERIES),
            baseline_law=str(args.baseline_law),
            variant_queries=_parse_list(args.variant_queries, VARIANT_QUERIES),
            variant_law=str(args.variant_law),
        )
    )

    save_path = Path(args.save)
    if not save_path.is_absolute():
        save_path = ROOT / save_path
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"ok": True, "save": str(save_path), "delta": payload["delta"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

