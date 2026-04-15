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
    is_active: bool = True


class IntentUpdate(BaseModel):
    agent_name: Optional[str] = None
    intent_name: Optional[str] = None
    trigger_keywords: Optional[str] = None
    action_template: Optional[str] = None
    priority: Optional[int] = None
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


@router.post("/email/run")
async def run_agent_on_lead(body: RunAgentBody, db: AsyncSession = Depends(get_db)):
    # 1. Лид
    lead = await db.get(Lead, body.lead_id)
    if not lead:
        raise HTTPException(404, "Лид не найден")

    # 2. Треды лида (последние 5)
    threads_result = await db.execute(
        select(EmailThread)
        .where(EmailThread.lead_id == body.lead_id)
        .order_by(EmailThread.last_message_at.desc().nulls_last())
        .limit(5)
    )
    threads = threads_result.scalars().all()

    # 3. Последние сообщения из тредов
    email_lines = []
    for thread in threads:
        msgs_result = await db.execute(
            select(EmailMessage)
            .where(EmailMessage.thread_id == thread.id)
            .order_by(EmailMessage.sent_at.asc().nulls_last())
            .limit(10)
        )
        msgs = msgs_result.scalars().all()
        if msgs:
            email_lines.append(f"\n--- {thread.subject} ---")
            for m in msgs:
                who  = "Мы:" if m.direction == "outbound" else "Клиент:"
                ts   = m.sent_at.strftime("%d.%m.%Y %H:%M") if m.sent_at else "—"
                text = (m.body or m.snippet or "").strip()[:400]
                email_lines.append(f"[{ts}] {who} {text}")

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

    # 6. Сборка слотов для агента
    email_block = "\n".join(email_lines) if email_lines else "Переписки с клиентом пока нет."
    task_block  = f"\n\nЗАДАЧА ОПЕРАТОРА: {body.task}" if body.task.strip() else ""

    slots = {
        "company":     getattr(lead, "company",     ""),
        "contact":     getattr(lead, "contact",     ""),
        "industry":    getattr(lead, "industry",    ""),
        "city":        getattr(lead, "city",         ""),
        "budget":      getattr(lead, "budget",      ""),
        "stage":       getattr(lead, "stage",       ""),
        "description": getattr(lead, "description", ""),
        "instruction": (
            f"ПЕРЕПИСКА С КЛИЕНТОМ:\n{email_block}"
            f"{intents_block}"
            f"{few_shots_block}"
            f"{task_block}"
        ),
    }

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
        else:
            raise HTTPException(400, f"Агент {body.agent!r} не поддерживается")
    except ImportError as e:
        logger.exception("Agent import error: %s", e)
        raise HTTPException(500, "Ошибка загрузки агента. Подробности в логах.")
    except Exception as e:
        logger.exception("Agent run error: %s", e)
        raise HTTPException(500, "Внутренняя ошибка агента. Подробности в логах.")

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
        "threads_analyzed": len(threads),
        "intents_applied":  len(intents),
        "few_shots_used":   1 if few_shots_block else 0,
    }
