"""A/B промптов Hermes на кейсах из плохих трейсов."""
from __future__ import annotations

from typing import Any

from core import traces
from core.eval_runner import run_eval_pipeline
from core.hermes import get_system_prompt
from core.qa.stats import z_test_proportions


def collect_bad_trace_cases(max_traces: int = 15) -> list[dict[str, Any]]:
    """Кейсы из 👎 / error трейсов (дедуп по фразе)."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for t in traces.get_traces(limit=500):
        if t.get("feedback") != "bad" and not t.get("error"):
            continue
        text = (t.get("text") or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "text": text,
            "expected": None,
            "trace_id": t.get("id"),
            "baseline_intent": t.get("intent"),
            "source": "bad_trace",
        })
        if len(out) >= max(1, max_traces):
            break
    return out


async def enrich_expected_from_eval_db(cases: list[dict[str, Any]]) -> None:
    """Подставляет expected из eval-сценариев с той же фразой."""
    if not cases:
        return
    from sqlalchemy import select

    from db.models.eval_scenario import EvalScenario
    from db.session import SessionLocal

    phrases = {c["text"].strip().lower() for c in cases}
    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(EvalScenario).where(EvalScenario.status.in_(("approved", "pending_review")))
            )
        ).scalars().all()
    by_phrase = {
        (s.phrase or "").strip().lower(): s.expected_intent
        for s in rows
        if (s.phrase or "").strip().lower() in phrases
    }
    for c in cases:
        exp = by_phrase.get(c["text"].strip().lower())
        if exp:
            c["expected"] = exp


def _summary_row(out: dict[str, Any], model: str) -> dict[str, Any]:
    s = out.get("summary", {}).get(model, {})
    total = int(s.get("total") or 0)
    correct = int(s.get("correct") or 0)
    return {
        "model": model,
        "cases_total": out.get("cases_count", 0),
        "cases_with_expected": total,
        "cases_correct": correct,
        "accuracy_pct": s.get("accuracy_pct", 0),
        "avg_ms": s.get("avg_ms", 0),
    }


def _per_case_compare(
    base_out: dict[str, Any],
    var_out: dict[str, Any],
    model: str,
    cases: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    base_by_text = {r["text"]: r for r in base_out.get("results", [])}
    var_by_text = {r["text"]: r for r in var_out.get("results", [])}
    rows: list[dict[str, Any]] = []
    for c in cases:
        text = c["text"]
        br = (base_by_text.get(text) or {}).get("models", {}).get(model, {})
        vr = (var_by_text.get(text) or {}).get("models", {}).get(model, {})
        rows.append({
            "text": text,
            "trace_id": c.get("trace_id"),
            "expected": c.get("expected"),
            "baseline_intent": br.get("intent"),
            "variant_intent": vr.get("intent"),
            "baseline_correct": br.get("correct"),
            "variant_correct": vr.get("correct"),
            "intent_changed": br.get("intent") != vr.get("intent"),
        })
    return rows


async def run_prompt_ab_on_traces(
    variant_prompt: str,
    *,
    max_bad_traces: int = 15,
    models: list[str] | None = None,
    baseline_prompt: str | None = None,
) -> dict[str, Any]:
    """Сравнить baseline и variant на плохих трейсах."""
    variant_prompt = (variant_prompt or "").strip()
    if len(variant_prompt) < 80:
        return {"ok": False, "error": "variant_prompt_too_short", "message": "Промпт варианта < 80 символов"}

    models = models or ["hermes3"]
    baseline = (baseline_prompt or get_system_prompt()).strip()
    cases = collect_bad_trace_cases(max_bad_traces)
    if not cases:
        return {
            "ok": False,
            "error": "no_bad_traces",
            "message": "Нет 👎 трейсов. Поставь минус на проблемных командах.",
        }

    await enrich_expected_from_eval_db(cases)
    with_expected = sum(1 for c in cases if c.get("expected"))

    base_out = await run_eval_pipeline(cases, models, system_prompt=baseline)
    var_out = await run_eval_pipeline(cases, models, system_prompt=variant_prompt)

    model = models[0]
    bk = _summary_row(base_out, model)
    vk = _summary_row(var_out, model)
    acc_delta = float(vk.get("accuracy_pct", 0)) - float(bk.get("accuracy_pct", 0))

    stats: dict[str, Any] = {}
    n = int(bk.get("cases_with_expected") or 0)
    if n >= 10:
        stats = z_test_proportions(
            p1=float(bk.get("accuracy_pct", 0)) / 100,
            p2=float(vk.get("accuracy_pct", 0)) / 100,
            n1=n,
            n2=n,
        )

    per_case = _per_case_compare(base_out, var_out, model, cases)
    fixes = sum(
        1 for r in per_case
        if r.get("expected") and r.get("baseline_correct") is False and r.get("variant_correct") is True
    )
    regressions = sum(
        1 for r in per_case
        if r.get("expected") and r.get("baseline_correct") is True and r.get("variant_correct") is False
    )

    return {
        "ok": True,
        "cases_count": len(cases),
        "cases_with_expected": with_expected,
        "model": model,
        "baseline": bk,
        "variant": vk,
        "delta": {
            "accuracy_pp": round(acc_delta, 2),
            "fixes": fixes,
            "regressions": regressions,
            "intent_changes": sum(1 for r in per_case if r.get("intent_changed")),
        },
        "stats": stats,
        "per_case": per_case,
    }
