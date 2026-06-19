"""Lead hunt: поиск кандидатов, очередь approve, импорт в CRM."""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import ops_store
from db.models import Lead
from services.lead_hunt_config import LeadHuntConfig, load_state, save_state
from services.lead_hunt_notifications import add_notification

logger = logging.getLogger(__name__)

_MAX_CANDIDATES = 200


def candidate_fingerprint(company: dict[str, Any]) -> str:
    inn = (company.get("inn") or "").strip()
    if inn:
        return f"inn:{inn}"
    name = (company.get("name") or company.get("name_short") or "").strip().lower()
    return f"name:{name[:80]}"


def _company_label(company: dict[str, Any]) -> str:
    return (company.get("name") or company.get("name_short") or "Компания")[:120]


def list_candidates(*, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    items = list((load_state().get("candidates") or []))
    if status:
        items = [x for x in items if x.get("status") == status]
    return items[:limit]


def _pending_fingerprints() -> set[str]:
    return {
        candidate_fingerprint(c.get("company") or {})
        for c in list_candidates(status="pending")
    }


async def search_candidates(icp: dict[str, Any], cfg: LeadHuntConfig) -> dict[str, Any]:
    portrait = (icp.get("search_portrait") or icp.get("portrait_text") or "").strip()
    if not portrait:
        return {"candidates": [], "errors": ["empty_portrait"], "total_raw": 0}

    from leadgen.pipeline import search_by_portrait
    from leadgen.pipeline.persist_autosave import portrait_fit_score

    limit = min(cfg.candidates_per_run, 5)
    result = await search_by_portrait(portrait, limit=limit, save_to_crm=False)
    review = result.get("agent_review") or {}
    picked: list[dict[str, Any]] = []
    for company in result.get("results") or []:
        score = portrait_fit_score(company, review)
        if score < cfg.min_score_threshold:
            continue
        picked.append({"company": company, "score": score})
    return {
        "candidates": picked,
        "errors": result.get("errors") or [],
        "total_raw": len(result.get("results") or []),
    }


def _push_ops_queue(entry: dict[str, Any]) -> None:
    company = entry.get("company") or {}
    fp = candidate_fingerprint(company)
    qid = f"auto-leadhunt-{fp}"[:120]
    existing = ops_store.load_queue()
    if any(x.get("id") == qid and x.get("status") == "open" for x in existing):
        return
    title = _company_label(company)
    score = entry.get("score", 0)
    inn = (company.get("inn") or "").strip()
    detail = f"Автопоиск лидов. Скор: {score}%." + (f" ИНН: {inn}" if inn else "")
    existing.insert(
        0,
        {
            "id": qid,
            "severity": "medium",
            "title": f"Кандидат: {title}",
            "detail": detail,
            "kind": "lead_hunt",
            "status": "open",
            "created_ts": time.time(),
            "trace_ids": [],
            "candidate_id": entry.get("id"),
            "lead_hunt": {"company": title, "inn": inn, "score": score},
        },
    )
    ops_store.save_queue(existing)


def _notify_new(entry: dict[str, Any]) -> None:
    company = entry.get("company") or {}
    title = _company_label(company)
    fp = candidate_fingerprint(company)
    add_notification(
        kind="lead_hunt_new",
        title=f"Новый кандидат: {title}",
        detail=f"Скор {entry.get('score', 0)}%. Одобрите в Lead Hunt.",
        dedupe_key=f"new:{fp}",
        candidate={
            "id": entry.get("id"),
            "company": title,
            "inn": company.get("inn"),
            "score": entry.get("score"),
        },
    )


async def _create_lead_from_company(
    company: dict[str, Any], score: int, db: AsyncSession
) -> int | None:
    from leadgen.pipeline.persist import _find_lead_by_inn
    from leadgen.pipeline.persist_autosave import minimal_card_from_company
    from leadgen.pipeline.persist_card import lead_payload_from_card

    card = minimal_card_from_company(company, final_score=score)
    payload = lead_payload_from_card(card)
    payload["source"] = "lead_hunt"
    inn = (payload.get("inn") or "").strip() or None
    if inn:
        existing = await _find_lead_by_inn(db, inn)
        if existing:
            return existing.id
    name = (payload.get("company") or "").strip()
    if not name:
        return None
    dup = await db.execute(select(Lead.id).where(Lead.company == name).limit(1))
    if dup.scalar_one_or_none():
        return None
    lead = Lead(**payload, stage="Новый")
    db.add(lead)
    await db.flush()
    await db.refresh(lead)
    return lead.id


async def process_search_results(
    db: AsyncSession,
    candidates: list[dict[str, Any]],
    *,
    icp_version: int,
    cfg: LeadHuntConfig,
) -> dict[str, int]:
    items = list((load_state().get("candidates") or []))
    pending_fps = _pending_fingerprints()
    queued = approved = skipped = 0
    now = datetime.now(timezone.utc).isoformat()

    for item in candidates:
        company = item.get("company") or {}
        fp = candidate_fingerprint(company)
        if fp in pending_fps:
            skipped += 1
            continue
        entry: dict[str, Any] = {
            "id": f"lh-{uuid.uuid4().hex[:10]}",
            "status": "pending",
            "company": company,
            "score": int(item.get("score") or 0),
            "icp_version": icp_version,
            "found_at": now,
            "lead_id": None,
        }
        if cfg.autosave_above_threshold:
            lead_id = await _create_lead_from_company(company, entry["score"], db)
            if lead_id:
                entry["status"] = "approved"
                entry["lead_id"] = lead_id
                entry["approved_at"] = now
                approved += 1
                items.insert(0, entry)
                pending_fps.add(fp)
                continue
        items.insert(0, entry)
        pending_fps.add(fp)
        queued += 1
        if cfg.notify_ops_queue:
            _push_ops_queue(entry)
            _notify_new(entry)

    state = load_state()
    state["candidates"] = items[:_MAX_CANDIDATES]
    save_state(state)
    if approved:
        await db.commit()
    return {"queued": queued, "approved": approved, "skipped": skipped}


async def approve_candidate(candidate_id: str, db: AsyncSession) -> dict[str, Any]:
    items = list((load_state().get("candidates") or []))
    for cand in items:
        if cand.get("id") != candidate_id:
            continue
        if cand.get("status") != "pending":
            raise ValueError("not_pending")
        lead_id = await _create_lead_from_company(
            cand.get("company") or {}, int(cand.get("score") or 0), db
        )
        if not lead_id:
            raise ValueError("create_failed")
        cand["status"] = "approved"
        cand["lead_id"] = lead_id
        cand["approved_at"] = datetime.now(timezone.utc).isoformat()
        state = load_state()
        state["candidates"] = items
        save_state(state)
        await db.commit()
        return {"ok": True, "lead_id": lead_id, "candidate_id": candidate_id}
    raise ValueError("not_found")


def reject_candidate(candidate_id: str, *, note: str = "") -> dict[str, Any]:
    items = list((load_state().get("candidates") or []))
    for cand in items:
        if cand.get("id") != candidate_id:
            continue
        if cand.get("status") != "pending":
            raise ValueError("not_pending")
        cand["status"] = "rejected"
        cand["rejected_at"] = datetime.now(timezone.utc).isoformat()
        cand["reject_note"] = note[:500]
        state = load_state()
        state["candidates"] = items
        save_state(state)
        return {"ok": True, "candidate_id": candidate_id}
    raise ValueError("not_found")
