"""
KPI gate for Hermes rollout results.

Usage:
  python scripts/hermes_kpi_gate.py --input data/parse_rollout_latest.json
"""
from __future__ import annotations

import argparse
import json
from typing import Any


def _ok(
    stage: dict[str, Any],
    baseline: dict[str, Any],
    min_accuracy_delta: float,
    max_error_rate_delta: float,
    min_throughput_delta_pct: float,
    max_p95_delta_pct: float,
) -> bool:
    k = stage["kpi"]
    b = baseline["kpi"]
    acc_delta = k["accuracy_pct"] - b["accuracy_pct"]
    err_delta = k["error_rate_pct"] - b["error_rate_pct"]
    throughput_old = float(b.get("throughput_rps") or 0)
    throughput_new = float(k.get("throughput_rps") or 0)
    if throughput_old > 0:
        throughput_delta_pct = (throughput_new - throughput_old) / throughput_old * 100
    else:
        throughput_delta_pct = 0.0
    p95_old = float(b.get("p95_ms") or 0)
    p95_new = float(k.get("p95_ms") or 0)
    if p95_old > 0:
        p95_delta_pct = (p95_new - p95_old) / p95_old * 100
    else:
        p95_delta_pct = 0.0
    return (
        acc_delta >= min_accuracy_delta
        and err_delta <= max_error_rate_delta
        and throughput_delta_pct >= min_throughput_delta_pct
        and p95_delta_pct <= max_p95_delta_pct
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--min-accuracy-delta", type=float, default=-0.5)
    parser.add_argument("--max-error-rate-delta", type=float, default=1.0)
    parser.add_argument("--min-throughput-delta-pct", type=float, default=-5.0)
    parser.add_argument("--max-p95-delta-pct", type=float, default=10.0)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        payload = json.load(f)

    stages = payload.get("stages", [])
    if not stages:
        print(json.dumps({"error": "no stages"}, ensure_ascii=False))
        return

    baseline = stages[0]
    decisions = []
    for st in stages[1:]:
        decisions.append(
            {
                "stage": st["stage"],
                "accept": _ok(
                    st,
                    baseline,
                    args.min_accuracy_delta,
                    args.max_error_rate_delta,
                    args.min_throughput_delta_pct,
                    args.max_p95_delta_pct,
                ),
                "delta_vs_baseline": st.get("delta_vs_baseline", {}),
                "kpi": st.get("kpi", {}),
                "usage": st.get("usage", {}),
            }
        )

    print(
        json.dumps(
            {
                "gate": {
                    "min_accuracy_delta": args.min_accuracy_delta,
                    "max_error_rate_delta": args.max_error_rate_delta,
                    "min_throughput_delta_pct": args.min_throughput_delta_pct,
                    "max_p95_delta_pct": args.max_p95_delta_pct,
                },
                "decisions": decisions,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

