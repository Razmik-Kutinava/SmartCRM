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
from services.lead_hunt_queue import build_summary

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


async def search_candidates(
    icp: dict[str, Any], cfg: LeadHuntConfig, db: AsyncSession
) -> dict[str, Any]:
    from services.lead_hunt_search_cycle import run_search_cycle

    return await run_search_cycle(icp, cfg, db)


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


async def save_candidate_to_crm(cand: dict[str, Any], db: AsyncSession) -> int | None:
    """Сохранение в CRM (логика _save_to_crm) в переданной сессии."""
    from leadgen.pipeline.persist import _find_lead_by_inn
    from leadgen.pipeline.persist_autosave import minimal_card_from_company
    from leadgen.pipeline.persist_card import apply_payload_to_lead, lead_payload_from_card

    pipeline = cand.get("pipeline_card") or {}
    score = int(cand.get("score") or 0)
    company = cand.get("company") or {}
    if pipeline.get("company_name"):
        card = {**pipeline, "final_score": pipeline.get("final_score") or score}
    else:
        card = minimal_card_from_company(company, final_score=score)
    payload = lead_payload_from_card(card)
    payload["source"] = "lead_hunt"
    inn = (payload.get("inn") or "").strip() or None
    if inn:
        existing = await _find_lead_by_inn(db, inn)
        if existing:
            apply_payload_to_lead(existing, payload)
            await db.flush()
            await db.refresh(existing)
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


async def _maybe_start_nurture(
    db: AsyncSession,
    lead_id: int,
    *,
    start_nurture: bool,
    account_id: int | None,
    product: str | None,
) -> dict[str, Any] | None:
    if not start_nurture:
        return None
    from db.models import EmailAccount
    from services.email_nurture import start_nurture_chain

    acc_id = account_id
    if not acc_id:
        row = await db.execute(select(EmailAccount.id).order_by(EmailAccount.id.asc()).limit(1))
        acc_id = row.scalar_one_or_none()
    if not acc_id:
        return {"skipped": True, "reason": "no_email_account"}
    try:
        chain = await start_nurture_chain(
            db,
            lead_id=lead_id,
            account_id=int(acc_id),
            product=(product or "").strip() or None,
            chain_label="Lead hunt · nurture",
        )
        return {"chain_id": chain.id, "steps_total": chain.steps_total}
    except ValueError as e:
        return {"skipped": True, "reason": str(e)}


# alias для тестов
_create_lead_from_company = save_candidate_to_crm


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
            "portrait_score": item.get("portrait_score"),
            "pipeline_score": item.get("pipeline_score"),
            "pipeline_card": item.get("pipeline_card"),
            "search_source": item.get("search_source"),
            "agent_fanout": item.get("agent_fanout"),
            "icp_version": icp_version,
            "found_at": now,
            "lead_id": None,
        }
        entry["summary"] = build_summary(entry)
        if cfg.autosave_above_threshold:
            lead_id = await save_candidate_to_crm(entry, db)
            if lead_id:
                entry["status"] = "approved"
                entry["lead_id"] = lead_id
                entry["approved_at"] = now
                from services.lead_hunt_run_log import persist_fanout_agent_logs

                entry["agent_run_ids"] = await persist_fanout_agent_logs(
                    db, lead_id, entry.get("agent_fanout"), candidate_id=entry["id"]
                )
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


async def approve_candidate(
    candidate_id: str,
    db: AsyncSession,
    *,
    start_nurture: bool = False,
    nurture_account_id: int | None = None,
    nurture_product: str | None = None,
) -> dict[str, Any]:
    items = list((load_state().get("candidates") or []))
    for cand in items:
        if cand.get("id") != candidate_id:
            continue
        if cand.get("status") != "pending":
            raise ValueError("not_pending")
        lead_id = await save_candidate_to_crm(cand, db)
        if not lead_id:
            raise ValueError("create_failed")
        nurture = await _maybe_start_nurture(
            db,
            lead_id,
            start_nurture=start_nurture,
            account_id=nurture_account_id,
            product=nurture_product,
        )
        from services.lead_hunt_run_log import persist_fanout_agent_logs

        agent_run_ids = await persist_fanout_agent_logs(
            db, lead_id, cand.get("agent_fanout"), candidate_id=candidate_id
        )
        cand["status"] = "approved"
        cand["lead_id"] = lead_id
        cand["approved_at"] = datetime.now(timezone.utc).isoformat()
        if nurture:
            cand["nurture"] = nurture
        state = load_state()
        state["candidates"] = items
        save_state(state)
        await db.commit()
        out: dict[str, Any] = {"ok": True, "lead_id": lead_id, "candidate_id": candidate_id}
        if agent_run_ids:
            out["agent_run_ids"] = agent_run_ids
        if nurture:
            out["nurture"] = nurture
        return out
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
