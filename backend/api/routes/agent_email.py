"""
API агентов на почте:
  CRUD email-интентов, запуск агента с контекстом лида,
  сохранение истории, 👍/👎 обратная связь, few-shot управление.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.agent_email_context import (
    EMAIL_DIGEST_MAX_MESSAGES,
    EMAIL_DIGEST_MAX_THREADS,
    build_agent_slots,
    build_email_digest,
)
from core.agent_gaps import merge_missing
from db.session import get_db
from db.models.agent_email_intent import AgentEmailIntent
from db.models.agent_run_log import AgentRunLog
from db.models.email import EmailThread, EmailMessage
from db.models.lead import Lead
from db.models.training_dataset import TrainingDataset, TrainingRecord

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agents", tags=["agents"])


# ── Схемы ─────────────────────────────────────────────────────────

class IntentCreate(BaseModel):
    agent_name: str
    intent_name: str
    trigger_keywords: str = ""
    action_template: str
    priority: int = 0
    auto_send: bool = False
    reply_subject: str = ""
    is_active: bool = True


class IntentUpdate(BaseModel):
    agent_name: Optional[str] = None
    intent_name: Optional[str] = None
    trigger_keywords: Optional[str] = None
    action_template: Optional[str] = None
    priority: Optional[int] = None
    auto_send: Optional[bool] = None
    reply_subject: Optional[str] = None
    is_active: Optional[bool] = None


class RunAgentBody(BaseModel):
    lead_id: int
    agent: str = "marketer"
    task: str = ""


class FeedbackBody(BaseModel):
    run_id: int
    feedback: str           # "good" | "bad"
    note: str = ""          # комментарий к плохому ответу


class FewShotBody(BaseModel):
    run_id: int             # какой запуск добавить как пример
    dataset_name: str = "marketer_email_examples"


# ── CRUD интентов ─────────────────────────────────────────────────

@router.get("/email-intents")
async def list_intents(agent_name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    q = select(AgentEmailIntent).order_by(AgentEmailIntent.priority.desc(), AgentEmailIntent.id)
    if agent_name:
        q = q.where(AgentEmailIntent.agent_name.in_([agent_name, "all"]))
    result = await db.execute(q)
    return [i.to_dict() for i in result.scalars().all()]


@router.post("/email-intents", status_code=201)
async def create_intent(body: IntentCreate, db: AsyncSession = Depends(get_db)):
    intent = AgentEmailIntent(**body.model_dump())
    db.add(intent)
    await db.commit()
    await db.refresh(intent)
    return intent.to_dict()


@router.put("/email-intents/{intent_id}")
async def update_intent(intent_id: int, body: IntentUpdate, db: AsyncSession = Depends(get_db)):
    intent = await db.get(AgentEmailIntent, intent_id)
    if not intent:
        raise HTTPException(404, "Интент не найден")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(intent, k, v)
    intent.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(intent)
    return intent.to_dict()


@router.delete("/email-intents/{intent_id}", status_code=204)
async def delete_intent(intent_id: int, db: AsyncSession = Depends(get_db)):
    intent = await db.get(AgentEmailIntent, intent_id)
    if not intent:
        raise HTTPException(404, "Интент не найден")
    await db.delete(intent)
    await db.commit()


# ── Статистика feedback ───────────────────────────────────────────

@router.get("/email/stats")
async def feedback_stats(db: AsyncSession = Depends(get_db)):
    """Сколько хороших/плохих ответов по каждому агенту."""
    result = await db.execute(
        select(AgentRunLog.agent_name, AgentRunLog.feedback, func.count().label("cnt"))
        .group_by(AgentRunLog.agent_name, AgentRunLog.feedback)
    )
    rows = result.all()
    stats: dict = {}
    for agent_name, feedback, cnt in rows:
        if agent_name not in stats:
            stats[agent_name] = {"good": 0, "bad": 0, "total": 0}
        if feedback == "good":
            stats[agent_name]["good"] += cnt
        elif feedback == "bad":
            stats[agent_name]["bad"] += cnt
        stats[agent_name]["total"] += cnt
    return stats


# ── История запусков для лида ─────────────────────────────────────

@router.get("/email/history/{lead_id}")
async def agent_history(lead_id: int, limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentRunLog)
        .where(AgentRunLog.lead_id == lead_id)
        .order_by(AgentRunLog.created_at.desc())
        .limit(limit)
    )
    return [r.to_dict() for r in result.scalars().all()]


# ── Few-shot примеры ──────────────────────────────────────────────

@router.get("/email/few-shots")
async def list_few_shots(db: AsyncSession = Depends(get_db)):
    """Все запуски помеченные как хорошие примеры."""
    result = await db.execute(
        select(AgentRunLog)
        .where(AgentRunLog.is_few_shot == True)
        .order_by(AgentRunLog.created_at.desc())
        .limit(50)
    )
    return [r.to_dict() for r in result.scalars().all()]


@router.post("/email/few-shots")
async def add_few_shot(body: FewShotBody, db: AsyncSession = Depends(get_db)):
    """Пометить запуск как few-shot пример и сохранить в TrainingDataset."""
    run = await db.get(AgentRunLog, body.run_id)
    if not run:
        raise HTTPException(404, "Запуск не найден")

    run.is_few_shot = True
    run.feedback = "good"

    # Найти или создать датасет
    ds_result = await db.execute(
        select(TrainingDataset).where(TrainingDataset.name == body.dataset_name)
    )
    ds = ds_result.scalars().first()
    if not ds:
        ds = TrainingDataset(name=body.dataset_name, description="Few-shot примеры для агента маркетолога", status="ready")
        db.add(ds)
        await db.flush()

    # Собираем пример
    result_dict = run.result_json or {}
    first_email = result_dict.get("first_email", {})
    input_text = f"Задача: {run.task or 'Написать письмо клиенту'}"

    record = TrainingRecord(
        dataset_id=ds.id,
        record_type="pair",
        input_text=input_text,
        output_json=result_dict,
        notes=f"Из запуска #{run.id}, агент {run.agent_name}, лид #{run.lead_id}",
    )
    db.add(record)
    await db.commit()
    return {"status": "added", "dataset": ds.name, "run_id": run.id}


@router.delete("/email/few-shots/{run_id}", status_code=204)
async def remove_few_shot(run_id: int, db: AsyncSession = Depends(get_db)):
    run = await db.get(AgentRunLog, run_id)
    if not run:
        raise HTTPException(404)
    run.is_few_shot = False
    await db.commit()


# ── Feedback ─────────────────────────────────────────────────────

@router.post("/email/feedback")
async def save_feedback(body: FeedbackBody, db: AsyncSession = Depends(get_db)):
    run = await db.get(AgentRunLog, body.run_id)
    if not run:
        raise HTTPException(404, "Запуск не найден")
    run.feedback      = body.feedback
    run.feedback_note = body.note
    # Если хорошо — автоматом помечаем как потенциальный few-shot
    if body.feedback == "good" and not run.is_few_shot:
        run.is_few_shot = True
    await db.commit()
    return {"status": "saved", "feedback": body.feedback}


# ── Запуск агента ────────────────────────────────────────────────

async def _load_few_shots(agent_name: str, db: AsyncSession) -> str:
    """Загружает few-shot примеры из БД для инъекции в промпт."""
    result = await db.execute(
        select(AgentRunLog)
        .where(AgentRunLog.is_few_shot == True, AgentRunLog.agent_name == agent_name)
        .order_by(AgentRunLog.created_at.desc())
        .limit(3)
    )
    logs = result.scalars().all()
    if not logs:
        return ""

    lines = ["\n\n### ПРИМЕРЫ ХОРОШИХ ОТВЕТОВ (few-shot, одобрены оператором):"]
    for i, log in enumerate(logs, 1):
        r = log.result_json or {}
        email = r.get("first_email", {})
        if email:
            lines.append(
                f"\nПример {i}:"
                f"\n  Задача: {log.task or 'Написать письмо'}"
                f"\n  Тема: {email.get('subject', '')}"
                f"\n  Письмо: {email.get('body', '')[:300]}"
            )
    return "\n".join(lines)


async def _last_agent_output(lead_id: int, agent_name: str, db: AsyncSession) -> dict:
    """Последний результат агента по лиду — только ключевые поля, чтобы не раздувать промпт."""
    result = await db.execute(
        select(AgentRunLog)
        .where(AgentRunLog.lead_id == lead_id, AgentRunLog.agent_name == agent_name)
        .order_by(AgentRunLog.created_at.desc())
        .limit(1)
    )
    log = result.scalars().first()
    payload = (log.result_json or {}) if log else {}
    if not isinstance(payload, dict) or not payload:
        return {}

    if agent_name == "analyst":
        keys = {
            "score": payload.get("score"),
            "summary": str(payload.get("summary") or "")[:400],
            "stage_view": str(payload.get("stage_view") or "")[:200],
            "bant": payload.get("bant"),
            "next_steps": (payload.get("next_steps") or [])[:2],
            "missing_data": (payload.get("missing_data") or [])[:5],
        }
    elif agent_name == "economist":
        keys = {
            "summary": str(payload.get("summary") or "")[:300],
            "deal_segment": payload.get("deal_segment"),
            "ltv_estimate": str(payload.get("ltv_estimate") or "")[:200],
            "deal_probability_pct": payload.get("deal_probability_pct"),
            "missing_data": (payload.get("missing_data") or [])[:5],
        }
    elif agent_name == "marketer":
        keys = {
            "summary": str(payload.get("summary") or "")[:300],
            "value_hook": str(payload.get("value_hook") or "")[:200],
            "product_to_offer": str(payload.get("product_to_offer") or "")[:120],
            "missing_data": (payload.get("missing_data") or [])[:5],
        }
    elif agent_name == "tech_specialist":
        keys = {
            "summary": str(payload.get("summary") or "")[:300],
            "likely_stack": (payload.get("likely_stack") or [])[:4],
            "portfolio_fit": (payload.get("portfolio_fit") or [])[:3],
            "missing_data": (payload.get("missing_data") or [])[:5],
        }
    else:
        keys = {"summary": str(payload.get("summary") or payload.get("decision") or "")[:300]}

    return {k: v for k, v in keys.items() if v}


async def _attach_card_rag(slots: dict, agent: str, task: str) -> dict:
    """RAG только для одного агента, без live web (🔍 уже в слотах). Cap ~800 символов."""
    import os
    from rag.retrieve import build_rag_query, retrieve_context_sync

    if os.getenv("RAG_ENABLED", "1").lower() in ("0", "false", "no"):
        return slots
    q = build_rag_query(task or slots.get("company", ""), slots)
    if not q:
        return slots
    try:
        import asyncio
        ctx = await asyncio.to_thread(retrieve_context_sync, q, 3, agent)
        if ctx and ctx.strip():
            slots = {**slots, f"_rag_{agent}": ctx.strip()[:800]}
    except Exception as e:
        logger.warning("RAG на карточке (%s): %s", agent, e)
    return slots


@router.post("/email/run")
async def run_agent_on_lead(body: RunAgentBody, db: AsyncSession = Depends(get_db)):
    # 1. Лид
    lead = await db.get(Lead, body.lead_id)
    if not lead:
        raise HTTPException(404, "Лид не найден")

    # 2. Треды лида (свежие первыми)
    threads_result = await db.execute(
        select(EmailThread)
        .where(EmailThread.lead_id == body.lead_id)
        .order_by(EmailThread.last_message_at.desc().nulls_last())
        .limit(EMAIL_DIGEST_MAX_THREADS)
    )
    threads = threads_result.scalars().all()

    # 3. Последние сообщения из тредов → дайджест с лимитами (экономия токенов)
    digest_threads = []
    for thread in threads:
        msgs_result = await db.execute(
            select(EmailMessage)
            .where(EmailMessage.thread_id == thread.id)
            .order_by(EmailMessage.sent_at.desc().nulls_last())
            .limit(EMAIL_DIGEST_MAX_MESSAGES)
        )
        msgs = list(reversed(msgs_result.scalars().all()))
        if not msgs:
            continue
        digest_threads.append({
            "subject": thread.subject,
            "messages": [
                {
                    "direction": m.direction,
                    "sent_at": m.sent_at.strftime("%d.%m.%Y %H:%M") if m.sent_at else "—",
                    "text": m.body or m.snippet or "",
                }
                for m in msgs
            ],
        })

    # 4. Активные email-интенты из БД
    intents_result = await db.execute(
        select(AgentEmailIntent)
        .where(AgentEmailIntent.is_active == True, AgentEmailIntent.agent_name.in_([body.agent, "all"]))
        .order_by(AgentEmailIntent.priority.desc())
    )
    intents = intents_result.scalars().all()

    intents_block = ""
    if intents:
        intents_block = "\n\nПРАВИЛА ПОВЕДЕНИЯ ПО ПОЧТЕ:\n"
        for intent in intents:
            intents_block += f"• [{intent.intent_name}]: {intent.action_template}\n"

    # 5. Few-shot примеры (одобренные оператором)
    few_shots_block = await _load_few_shots(body.agent, db)

    # Предварительные выводы других агентов (для стратега и флага prior_agents)
    peer_names = ("analyst", "economist", "marketer", "tech_specialist")
    peer_outputs = {}
    for name in peer_names:
        out = await _last_agent_output(body.lead_id, name, db)
        if out:
            peer_outputs[name] = out

    # 6. Сборка слотов (checko/brief/gaps)
    slots = build_agent_slots(
        lead,
        email_block=build_email_digest(digest_threads),
        intents_block=intents_block,
        few_shots_block=few_shots_block,
        task=body.task,
        agent=body.agent,
        prior_agents=bool(peer_outputs),
    )
    context_gaps = list(slots.get("context_gaps") or [])

    if body.agent == "strategist":
        if peer_outputs.get("analyst"):
            slots["analyst_output"] = peer_outputs["analyst"]
        if peer_outputs.get("economist"):
            slots["economist_output"] = peer_outputs["economist"]
        if peer_outputs.get("marketer"):
            slots["marketer_output"] = peer_outputs["marketer"]
        if peer_outputs.get("tech_specialist"):
            slots["tech_output"] = peer_outputs["tech_specialist"]

    slots = await _attach_card_rag(slots, body.agent, body.task)

    # 7. Запуск агента
    try:
        if body.agent == "marketer":
            from agents.marketer import _analyze
            result = await _analyze("write_email", slots)
        elif body.agent == "analyst":
            from agents.analyst import _analyze as fn
            result = await fn("analyze_lead", slots)
        elif body.agent == "strategist":
            from agents.strategist import _analyze as fn
            result = await fn("analyze_lead", slots)
        elif body.agent == "economist":
            from agents.economist import _analyze as fn
            result = await fn("analyze_lead", slots)
        elif body.agent == "tech_specialist":
            from agents.tech_specialist import _analyze as fn
            result = await fn("analyze_lead", slots)
        else:
            raise HTTPException(400, f"Агент {body.agent!r} не поддерживается")
    except ImportError as e:
        logger.exception("Agent import error: %s", e)
        raise HTTPException(500, "Ошибка загрузки агента. Подробности в логах.")
    except Exception as e:
        logger.exception("Agent run error: %s", e)
        raise HTTPException(500, "Внутренняя ошибка агента. Подробности в логах.")

    if not isinstance(result, dict):
        result = {"summary": str(result)}

    result["missing_data"] = merge_missing(result.get("missing_data"), context_gaps)
    if body.agent == "strategist" and not peer_outputs:
        result["missing_from_agents"] = merge_missing(
            result.get("missing_from_agents"),
            ["запустите аналитика (и по возможности экономиста/маркетолога/теха) до стратега"],
        )
    result["context_gaps"] = context_gaps

    # Apply: задача из next_action стратега (если ещё нет такой открытой)
    task_created = None
    next_action = (result.get("next_action") or "").strip()
    if body.agent == "strategist" and next_action:
        from db.models.task import Task

        existing = await db.execute(
            select(Task).where(
                Task.lead_id == body.lead_id,
                Task.title == next_action[:200],
                Task.status != "done",
            ).limit(1)
        )
        if not existing.scalars().first():
            t = Task(
                title=next_action[:200],
                lead_id=body.lead_id,
                status="open",
                related_lead=getattr(lead, "company", "") or "",
            )
            db.add(t)
            await db.flush()
            task_created = {"id": t.id, "title": t.title}

    # 8. Сохранить в лог
    log = AgentRunLog(
        lead_id=body.lead_id,
        agent_name=body.agent,
        task=body.task,
        result_json=result,
        threads_analyzed=len(threads),
        intents_applied=len(intents),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    return {
        "run_id":           log.id,
        "agent":            body.agent,
        "lead_id":          body.lead_id,
        "result":           result,
        "context_gaps":     context_gaps,
        "task_created":     task_created,
        "threads_analyzed": len(threads),
        "intents_applied":  len(intents),
        "few_shots_used":   1 if few_shots_block else 0,
        "score_updated":    bool(result.get("_score_applied_to_db")),
    }
