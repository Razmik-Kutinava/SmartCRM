"""Dr. QA — запуск A/A, A/B, KPI-gate и tender benchmarks."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .config import DATA_DIR, ROOT, SCRIPTS_DIR
from .stats import min_sample_size, z_test_proportions


def run_script(args: list[str], extra_env: dict | None = None) -> tuple[int, str]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        [sys.executable] + args,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(ROOT),
    )
    return result.returncode, result.stdout + result.stderr


def run_aa_test(models: str = "groq", status: str = "approved") -> dict:
    results = []
    for i in range(2):
        out_file = str(DATA_DIR / f"aa_run_{i}.json")
        rc, output = run_script([
            str(SCRIPTS_DIR / "eval_compare_modes.py"),
            "--models", models,
            "--status", status,
            "--save", out_file,
        ])
        if rc != 0:
            return {"error": output[:500], "run": i}
        try:
            results.append(json.loads(Path(out_file).read_text()))
        except Exception as e:
            return {"error": f"JSON parse failed run {i}: {e}"}

    def _acc(r: dict) -> float:
        kpis = r.get("kpis", [])
        return kpis[0]["accuracy_pct"] if kpis else 0.0

    acc0, acc1 = _acc(results[0]), _acc(results[1])
    drift = abs(acc1 - acc0)
    return {
        "type": "aa",
        "run0_accuracy": acc0,
        "run1_accuracy": acc1,
        "drift_pp": round(drift, 2),
        "stable": drift <= 2.0,
        "verdict": "STABLE" if drift <= 2.0 else "UNSTABLE — не запускай A/B пока не устранишь drift",
    }


def run_ab_test(
    variant_prompt: str,
    models: str = "groq",
    status: str = "approved",
) -> dict:
    base_file = str(DATA_DIR / "ab_baseline.json")
    rc, out = run_script([
        str(SCRIPTS_DIR / "eval_compare_modes.py"),
        "--models", models, "--status", status, "--save", base_file,
    ])
    if rc != 0:
        return {"error": f"baseline failed: {out[:400]}"}

    var_file = str(DATA_DIR / "ab_variant.json")
    rc, out = run_script([
        str(SCRIPTS_DIR / "eval_compare_modes.py"),
        "--models", models, "--status", status, "--save", var_file,
    ], extra_env={"HERMES_SYSTEM_PROMPT_OVERRIDE": variant_prompt})
    if rc != 0:
        return {"error": f"variant failed: {out[:400]}"}

    try:
        base = json.loads(Path(base_file).read_text())
        var = json.loads(Path(var_file).read_text())
    except Exception as e:
        return {"error": f"JSON parse: {e}"}

    def _kpi(r: dict) -> dict:
        kpis = r.get("kpis", [])
        return kpis[0] if kpis else {}

    bk, vk = _kpi(base), _kpi(var)
    n = bk.get("cases_total", 0)

    stats = z_test_proportions(
        p1=bk.get("accuracy_pct", 0) / 100,
        p2=vk.get("accuracy_pct", 0) / 100,
        n1=n,
        n2=n,
    ) if n >= 10 else {"error": "n<10", "note": "need more eval cases"}

    acc_delta = vk.get("accuracy_pct", 0) - bk.get("accuracy_pct", 0)
    latency_pct = ((vk.get("avg_ms", 1) - bk.get("avg_ms", 1)) / max(bk.get("avg_ms", 1), 1)) * 100

    return {
        "type": "ab",
        "n": n,
        "baseline": bk,
        "variant": vk,
        "deltas": {
            "accuracy_pp": round(acc_delta, 2),
            "latency_pct": round(latency_pct, 2),
            "error_rate_pp": round(vk.get("error_rate_pct", 0) - bk.get("error_rate_pct", 0), 2),
        },
        "stats": stats,
        "min_n_needed": min_sample_size(bk.get("accuracy_pct", 80) / 100),
    }


def run_kpi_gate(result_file: str) -> dict:
    rc, out = run_script([
        str(SCRIPTS_DIR / "hermes_kpi_gate.py"),
        "--input", result_file,
    ])
    try:
        return json.loads(out.strip().split("\n")[-1])
    except Exception:
        return {"error": out[:500], "rc": rc}


def run_tender_sources_test(
    queries: list[str] | None = None,
    law: str = "44",
    runs: int = 1,
    save_file: str = "",
) -> dict:
    target_path = Path(save_file) if save_file else (DATA_DIR / "tender_sources_baseline.json")
    if not target_path.is_absolute():
        target_path = ROOT / target_path
    target = str(target_path)
    cmd = [
        str(SCRIPTS_DIR / "tender_sources_benchmark.py"),
        "--law", str(law),
        "--runs", str(max(runs, 1)),
        "--save", target,
    ]
    if queries:
        clean = [str(q).strip() for q in queries if str(q).strip()]
        if clean:
            cmd.extend(["--queries", ",".join(clean)])

    rc, out = run_script(cmd)
    if rc != 0:
        return {"error": f"tender sources benchmark failed: {out[:500]}", "rc": rc}

    try:
        return json.loads(target_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"cannot parse benchmark file {target}: {e}", "raw": out[:500]}


def run_tender_suite(
    mode: str = "health",
    queries: list[str] | None = None,
    law: str = "all",
    runs: int = 2,
    seconds: int = 10,
    concurrency: int = 5,
    save_file: str = "",
) -> dict:
    mode = (mode or "health").strip().lower()
    if mode not in ("health", "aa", "load", "contract"):
        return {"error": f"unknown mode: {mode}. Use health|aa|load|contract"}

    cmd = [str(SCRIPTS_DIR / "tender_sources_tests.py"), mode, "--law", str(law)]
    if queries:
        clean = [str(q).strip() for q in queries if str(q).strip()]
        if clean:
            cmd.extend(["--queries", ",".join(clean)])

    if mode == "aa":
        cmd.extend(["--runs", str(max(1, int(runs)))])
    if mode == "load":
        cmd.extend(["--seconds", str(max(1, int(seconds))), "--concurrency", str(max(1, int(concurrency)))])

    if save_file:
        rel = str(save_file).replace("\\", "/").lstrip("/")
        cmd.extend(["--save", rel])

    rc, out = run_script(cmd, extra_env=os.environ.copy())
    if rc != 0:
        return {"error": f"tender suite failed: {out[:800]}", "rc": rc}
    try:
        return json.loads(out.strip().split("\n")[-1])
    except Exception:
        return {"error": "cannot parse tender suite output", "raw": out[:800]}


def get_current_kpis() -> dict:
    files = sorted(DATA_DIR.glob("hermes_kpi_gate_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        return {"error": "no KPI gate files found"}
    try:
        data = json.loads(files[0].read_text())
        return {"file": files[0].name, "data": data}
    except Exception as e:
        return {"error": str(e)}
