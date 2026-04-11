"""
Ops API — дашборд качества голосового пайплайна:
  GET  /api/ops/improvement, /hermes/prompt, /eval/preview, …
  POST /api/ops/hermes/prompt — сохранить системный промпт Hermes (файл override)
  DELETE /api/ops/hermes/prompt — сброс на встроенный промпт
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from api.routes.eval_scenarios import fetch_approved_eval_cases
from core import traces
from core import ops_store
from core.eval_runner import run_eval_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ops", tags=["ops"])



# ── Схемы ──────────────────────────────────────────────────────────

class FeedbackBody(BaseModel):
    trace_id: str
    feedback: str  # "good" | "bad"


class EvalCase(BaseModel):
    text: str
    expected_intent: Optional[str] = None


class EvalBody(BaseModel):
    cases: Optional[list[EvalCase]] = None  # если None — смотрим scenario_source
    models: list[str] = ["groq", "hermes3"]
    scenario_source: Literal["builtin", "db_approved", "builtin_and_db"] = "builtin"


class SnapshotBody(BaseModel):
    label: str = ""


class BaselineBody(BaseModel):
    snapshot_id: str


class ResolveQueueBody(BaseModel):
    status: str  # done | dismissed
    note: str = ""


class HermesPromptBody(BaseModel):
    prompt: str


# ── Встроенный eval-набор ──────────────────────────────────────────

BUILTIN_EVAL_CASES = [
    {"text": "создай лид компания АКМЕ контакт Иван", "expected": "create_lead"},
    {"text": "добавь лид ООО Ромашка телефон 79161234567", "expected": "create_lead"},
    {"text": "покажи горячих лидов", "expected": "list_leads"},
    {"text": "покажи все лиды", "expected": "list_leads"},
    {"text": "удали лид АКМЕ", "expected": "delete_lead"},
    {"text": "в лиде ромашка исправь почту на ivan@mail.ru", "expected": "update_lead"},
    {"text": "у ООО Вектор поменяй этап на В работе", "expected": "update_lead"},
    {"text": "напоминалку на завтра — позвонить в ООО Вектор", "expected": "create_task"},
    {"text": "какие задачи на сегодня", "expected": "list_tasks"},
    {"text": "напиши письмо клиенту АКМЕ про обновление продукта", "expected": "write_email"},
    {"text": "найди в интернете CRM системы для малого бизнеса", "expected": "search_web"},
    {"text": "привет как дела", "expected": "noop"},
    {"text": "создай два лида", "expected": "noop"},
    {"text": "что ты умеешь", "expected": "noop"},
]


def _builtin_cases_normalized() -> list[dict]:
    return [
        {"text": c["text"], "expected": c.get("expected"), "scenario_id": None, "scenario_title": None}
        for c in BUILTIN_EVAL_CASES
    ]


async def _build_eval_cases(body: EvalBody, db: AsyncSession) -> list[dict]:
    """Собирает список кейсов без вызова LLM."""
    if body.cases:
        return [
            {"text": c.text, "expected": c.expected_intent, "scenario_id": None, "scenario_title": None}
            for c in body.cases
        ]
    if body.scenario_source == "builtin":
        return _builtin_cases_normalized()
    if body.scenario_source == "db_approved":
        cases = await fetch_approved_eval_cases(db)
        if not cases:
            raise HTTPException(
                400,
                detail="Нет одобренных сценариев в БД. Создайте записи на странице «Сценарии eval» и нажмите «Утвердить».",
            )
        return cases
    if body.scenario_source == "builtin_and_db":
        return _builtin_cases_normalized() + await fetch_approved_eval_cases(db)
    return _builtin_cases_normalized()


# ── Эндпоинты ──────────────────────────────────────────────────────

@router.get("/traces")
async def get_traces(limit: int = 50, intent: Optional[str] = None):
    return traces.get_traces(limit=limit, intent_filter=intent)


@router.get("/stats")
async def get_stats():
    return traces.get_stats()


@router.get("/overview")
async def get_overview():
    """
    Сводка для дашборда: этапы пайплайна, здоровье LLM, очередь решений (кратко).
    """
    from core.llm import health_check

    ops_store.recompute_queue_and_suggestions(update_queue=False)
    q = ops_store.load_queue()
    open_items = [x for x in q if x.get("status") == "open"]
    by_sev = {"critical": 0, "medium": 0, "low": 0}
    for x in open_items:
        s = x.get("severity", "low")
        if s in by_sev:
            by_sev[s] += 1

    try:
        llm_h = await health_check()
    except Exception as e:
        llm_h = {"groq": False, "ollama": False, "active": "none", "error": str(e)[:200]}

    llm_ok = bool(llm_h.get("groq") or llm_h.get("ollama"))

    stats = traces.get_stats()

    pipeline = [
        {"id": "stt", "name": "Whisper (STT)", "status": "ok", "hint": "Аудио → текст"},
        {"id": "hermes", "name": "Hermes (интенты)", "status": "ok", "hint": "Текст → JSON интента"},
        {"id": "graph", "name": "LangGraph", "status": "ok", "hint": "Агенты и инструменты"},
        {"id": "db", "name": "PostgreSQL / Redis", "status": "ok", "hint": "Данные и кэш"},
    ]
    if stats.get("errors", 0) > 0:
        pipeline[1]["status"] = "warn"
        pipeline[1]["hint"] = f"Есть ошибки в трейсах: {stats['errors']}"
    if not llm_ok:
        pipeline[1]["status"] = "error"
        pipeline[1]["hint"] = "Нет доступного LLM (Groq и Ollama недоступны)"

    return {
        "pipeline": pipeline,
        "llm": llm_h,
        "stats": stats,
        "queue": {
            "open_total": len(open_items),
            "by_severity": by_sev,
            "preview": sorted(open_items, key=lambda x: {"critical": 0, "medium": 1, "low": 2}.get(x.get("severity"), 3))[:5],
        },
    }


@router.get("/queue")
async def get_queue():
    """Очередь задач для оператора (критичность + статус)."""
    items = ops_store.load_queue()
    open_items = [x for x in items if x.get("status") == "open"]
    open_items.sort(
        key=lambda x: (
            {"critical": 0, "medium": 1, "low": 2}.get(x.get("severity"), 3),
            -x.get("created_ts", 0),
        ),
    )
    return {"items": items, "open": open_items}


@router.post("/queue/{item_id}/resolve")
async def resolve_queue_item(item_id: str, body: ResolveQueueBody):
    if body.status not in ("done", "dismissed"):
        raise HTTPException(400, detail="status должен быть 'done' или 'dismissed'")
    ok = ops_store.resolve_queue_item(item_id, body.status, body.note)
    if not ok:
        raise HTTPException(404, detail="Запись не найдена")
    return {"ok": True, "id": item_id}


@router.post("/recompute")
async def post_recompute():
    """Пересчитать авто-очередь и сигналы по текущим трейсам."""
    data = ops_store.recompute_queue_and_suggestions(update_queue=True)
    return data


@router.get("/insights")
async def get_insights():
    """Предложения системы (эвристики) без перезаписи очереди."""
    return ops_store.generate_insights_only()


@router.get("/history")
async def get_history():
    """Снимки метрик и сравнение с базовой линией."""
    return ops_store.history_comparison()


@router.get("/hermes/prompt")
async def get_hermes_prompt():
    """Текущий системный промпт Hermes (встроенный или из файла override)."""
    from core.hermes import SYSTEM_PROMPT, get_system_prompt
    from core.hermes_prompt_store import get_prompt_source, override_path

    return {
        "prompt": get_system_prompt(),
        "source": get_prompt_source(),
        "override_file": override_path(),
        "builtin_char_count": len(SYSTEM_PROMPT),
    }


@router.post("/hermes/prompt")
async def post_hermes_prompt(body: HermesPromptBody):
    """Сохранить переопределение промпта в backend/data/hermes_system_prompt.txt"""
    from core.hermes_prompt_store import save_override

    text = body.prompt.strip()
    if len(text) < 80:
        raise HTTPException(400, detail="Промпт слишком короткий (минимум 80 символов).")
    save_override(text)
    return {"ok": True, "source": "override"}


@router.delete("/hermes/prompt")
async def delete_hermes_prompt():
    """Удалить override — снова используется встроенный промпт из кода."""
    from core.hermes_prompt_store import clear_override

    cleared = clear_override()
    return {"ok": True, "cleared": cleared}


class WhisperSettingsBody(BaseModel):
    """Параметры Groq Whisper (сохраняются в backend/data/whisper_settings.json)."""

    model_config = ConfigDict(populate_by_name=True)

    whisper_model: str = Field(
        default="whisper-large-v3-turbo",
        alias="model",
        description="Модель Groq Whisper",
    )
    language: str = "ru"
    temperature: float = 0.0
    prompt: str = ""
    ffmpeg_preprocess: bool = True


@router.get("/voice/whisper")
async def get_whisper_settings():
    """Текущие настройки STT: эффективные значения и дефолты из .env."""
    from core import voice_settings

    return voice_settings.get_settings_for_api()


@router.put("/voice/whisper")
async def put_whisper_settings(body: WhisperSettingsBody):
    """Сохранить настройки Whisper; дальше transcribe и WS используют их без перезапуска."""
    from core import voice_settings

    saved = voice_settings.save_settings(body.model_dump(by_alias=True))
    return {"ok": True, "effective": saved}


@router.delete("/voice/whisper")
async def delete_whisper_settings():
    """Сброс файла настроек — снова только переменные окружения."""
    from core import voice_settings

    cleared = voice_settings.clear_settings_file()
    return {"ok": True, "cleared": cleared, "effective": voice_settings.get_resolved_whisper_params()}


class AddExampleBody(BaseModel):
    phrase: str        # фраза пользователя
    intent: str        # правильный интент
    slots: dict = {}   # правильные слоты
    reply: str = ""    # ответ (можно пустой)


@router.post("/hermes/add-example")
async def add_example_to_prompt(body: AddExampleBody):
    """
    Добавляет few-shot пример прямо в системный промпт Hermes.
    Вставляет перед закрывающими кавычками промпта.
    Если промпт ещё не override — создаёт override из встроенного + пример.
    """
    import json as _json
    from core.hermes import get_system_prompt
    from core.hermes_prompt_store import save_override

    current = get_system_prompt()

    # Формируем строку примера
    out = {
        "intent": body.intent,
        "agents": ["analyst"],
        "slots": body.slots,
        "parallel": False,
        "reply": body.reply or f"Выполняю: {body.intent}.",
    }
    example_str = f'\nInput: "{body.phrase}"\nOutput: {_json.dumps(out, ensure_ascii=False)}\n'

    # Вставляем перед последним """ если есть, иначе в конец
    marker = '"""'
    idx = current.rfind(marker)
    if idx != -1:
        new_prompt = current[:idx].rstrip() + "\n" + example_str + current[idx:]
    else:
        new_prompt = current.rstrip() + "\n" + example_str

    save_override(new_prompt)
    logger.info("Добавлен few-shot пример в промпт: '%s' → %s", body.phrase[:40], body.intent)
    return {"ok": True, "example": example_str.strip(), "prompt_chars": len(new_prompt)}


@router.post("/hermes/bulk-eval")
async def bulk_eval(body: list[AddExampleBody]):
    """
    Прогоняет список фраз через Groq и проверяет совпадение интента.
    Возвращает каждую запись с полем passed: true/false и got_intent.
    """
    import asyncio
    import os
    from groq import AsyncGroq
    import json as _json
    from core.hermes import get_system_prompt

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise HTTPException(503, detail="GROQ_API_KEY не задан")

    client = AsyncGroq(api_key=api_key)
    system = get_system_prompt()
    results = []

    for item in body:
        await asyncio.sleep(2.0)  # rate-limit guard
        try:
            resp = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": item.phrase},
                ],
                temperature=0.0,
                max_tokens=256,
            )
            raw = resp.choices[0].message.content
            parsed = {}
            try:
                parsed = _json.loads(raw)
            except Exception:
                import re
                m = re.search(r'\{.*\}', raw, re.DOTALL)
                if m:
                    parsed = _json.loads(m.group())
            got = parsed.get("intent", "?")
            results.append({
                "phrase": item.phrase,
                "expected": item.intent,
                "got": got,
                "passed": got == item.intent,
                "slots": item.slots,
                "reply": item.reply,
            })
        except Exception as e:
            results.append({
                "phrase": item.phrase,
                "expected": item.intent,
                "got": "error",
                "passed": False,
                "slots": item.slots,
                "reply": item.reply,
                "error": str(e),
            })

    passed = sum(1 for r in results if r["passed"])
    return {
        "ok": True,
        "total": len(results),
        "passed": passed,
        "accuracy_pct": round(passed / len(results) * 100) if results else 0,
        "results": results,
    }


@router.post("/hermes/bulk-add")
async def bulk_add_to_prompt(body: list[AddExampleBody]):
    """Добавляет список few-shot примеров в промпт одним блоком."""
    import json as _json
    from core.hermes import get_system_prompt
    from core.hermes_prompt_store import save_override

    current = get_system_prompt()
    block = ""
    for item in body:
        out = {
            "intent": item.intent,
            "agents": ["analyst"],
            "slots": item.slots,
            "parallel": False,
            "reply": item.reply or f"Выполняю: {item.intent}.",
        }
        block += f'\nInput: "{item.phrase}"\nOutput: {_json.dumps(out, ensure_ascii=False)}\n'

    marker = '"""'
    idx = current.rfind(marker)
    if idx != -1:
        new_prompt = current[:idx].rstrip() + "\n" + block + current[idx:]
    else:
        new_prompt = current.rstrip() + "\n" + block

    save_override(new_prompt)
    logger.info("Bulk-добавлено %d few-shot примеров в промпт", len(body))
    return {"ok": True, "added": len(body), "prompt_chars": len(new_prompt)}


@router.get("/improvement")
async def get_improvement_workspace():
    """
    Единая сводка для страницы «Улучшение»: промпт, инсайты, подсказки процесса.
    """
    from core.hermes import get_system_prompt
    from core.hermes_prompt_store import get_prompt_source, override_path

    ins = ops_store.generate_insights_only()
    tips = [
        "Цикл качества: голос/трейсы → сценарии eval → правка системного промпта → прогон Eval (Hermes3 без токенов Groq).",
        "Сценарии в БД — эталоны регрессии: модель сама по себе от записей в таблице не учится, улучшается от текста промпта и примеров.",
        "Добавляйте few-shot (примеры «фраза → JSON») в промпт для спорных формулировок.",
        "После смены промпта сделайте снимок метрик на странице «Обзор» и сравните в «Истории».",
    ]
    return {
        "prompt": {
            "text": get_system_prompt(),
            "source": get_prompt_source(),
            "file": override_path(),
        },
        "suggestions": ins.get("suggestions", []),
        "signals": ins.get("signals", {}),
        "tips": tips,
    }


@router.post("/snapshot")
async def post_snapshot(body: SnapshotBody = SnapshotBody()):
    """Зафиксировать текущую статистику трейсов как снимок + текущий промпт."""
    from core.hermes import get_system_prompt
    from core.hermes_prompt_store import get_prompt_source
    stats = traces.get_stats()
    prompt_text = get_system_prompt()
    entry = ops_store.append_snapshot(
        stats,
        source="manual",
        label=body.label,
        prompt_text=prompt_text,
        prompt_source=get_prompt_source(),
    )
    return {"ok": True, "snapshot": entry}


@router.post("/traces/{trace_id}/to-scenario")
async def trace_to_scenario(trace_id: str, db: AsyncSession = Depends(get_db)):
    """
    Создаёт сценарий eval из трейса по trace_id.
    Трейс с 👎 превращается в draft-сценарий — сразу видно на странице Сценарии.
    """
    from db.models.eval_scenario import EvalScenario

    # Ищем трейс в памяти
    trace = next((t for t in traces.get_traces(limit=500) if t["id"] == trace_id), None)
    if not trace:
        raise HTTPException(404, detail=f"Трейс {trace_id} не найден (буфер 500 записей)")

    text = trace.get("text", "").strip()
    intent = trace.get("intent") or "noop"
    slots = trace.get("slots") or {}

    if not text:
        raise HTTPException(400, detail="Трейс пустой — нет текста команды")

    # Создаём сценарий
    scenario = EvalScenario(
        title=f"из трейса #{trace_id}: {text[:60]}",
        phrase=text,
        expected_intent=intent,
        expected_slots=slots,
        success_criteria=f"Hermes должен вернуть intent='{intent}'",
        desired_outcome="Исправить распознавание этой фразы",
        notes=f"Создан автоматически из трейса #{trace_id}. feedback={trace.get('feedback')}",
        status="draft",
    )
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)

    logger.info("Трейс %s → сценарий eval #%s '%s'", trace_id, scenario.id, text[:40])
    return {"ok": True, "scenario": scenario.to_dict()}


class SuggestPromptBody(BaseModel):
    max_bad_traces: int = 10  # сколько плохих трейсов брать для анализа


@router.post("/suggest-prompt")
async def suggest_prompt(body: SuggestPromptBody = SuggestPromptBody()):
    """
    Читает плохие трейсы (👎 + ошибки) + текущий промпт → просит Groq предложить улучшения.
    Возвращает: suggestion (текст предложений) + few_shot_examples (готовые строки для вставки в промпт).
    НЕ применяет изменения — только предлагает. Пользователь сам апрувит.
    """
    from groq import AsyncGroq
    import os
    from core.hermes import get_system_prompt

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise HTTPException(503, detail="GROQ_API_KEY не задан — не могу вызвать Groq")

    # Собираем плохие трейсы
    all_traces = traces.get_traces(limit=200)
    bad = [t for t in all_traces if t.get("feedback") == "bad" or t.get("error")][:body.max_bad_traces]

    if not bad:
        return {
            "ok": True,
            "has_suggestion": False,
            "message": "Нет плохих трейсов (👎) для анализа. Поставь минус на проблемных командах.",
            "suggestion": "",
            "few_shot_examples": [],
        }

    current_prompt = get_system_prompt()

    # Формируем запрос к Groq
    bad_list = "\n".join(
        f'- "{t["text"]}" → got: {t.get("intent", "?")} | feedback: {t.get("feedback", "")} | err: {t.get("error", "")[:80] if t.get("error") else "-"}'
        for t in bad
    )

    analysis_prompt = f"""You are a prompt engineering expert. Analyze these FAILED CRM voice command recognitions and suggest improvements to the system prompt.

CURRENT SYSTEM PROMPT (first 800 chars):
{current_prompt[:800]}

FAILED/BAD TRACES ({len(bad)} cases):
{bad_list}

Your task:
1. Identify patterns in the failures (what kinds of phrases fail?)
2. Write 2-4 new few-shot EXAMPLES to add to the prompt (format: Input: "phrase" → Output: {{...json...}})
3. Write a SHORT explanation (2-3 sentences in Russian) of what to fix

Respond in JSON:
{{
  "patterns": "краткое описание проблем (по-русски)",
  "explanation": "что именно стоит исправить в промпте (по-русски)",
  "few_shot_examples": [
    {{"input": "фраза пользователя", "output": {{"intent":"...", "agents":["analyst"], "slots":{{}}, "parallel":false, "reply":"..."}}}},
    ...
  ]
}}"""

    client = AsyncGroq(api_key=api_key)
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": analysis_prompt}],
        temperature=0.3,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    import json as _json
    try:
        result = _json.loads(raw)
    except Exception:
        result = {"patterns": raw, "explanation": raw, "few_shot_examples": []}

    # Форматируем few-shot примеры как строки для вставки в промпт
    formatted_examples = []
    for ex in result.get("few_shot_examples", []):
        try:
            inp = ex.get("input", "")
            out = _json.dumps(ex.get("output", {}), ensure_ascii=False)
            formatted_examples.append(f'Input: "{inp}"\nOutput: {out}')
        except Exception:
            pass

    return {
        "ok": True,
        "has_suggestion": True,
        "bad_traces_analyzed": len(bad),
        "patterns": result.get("patterns", ""),
        "explanation": result.get("explanation", ""),
        "few_shot_examples": formatted_examples,
        "raw_few_shot": result.get("few_shot_examples", []),
    }


@router.post("/baseline")
async def post_baseline(body: BaselineBody):
    """Установить линию «было» по id снимка."""
    ok = ops_store.set_baseline_snapshot_id(body.snapshot_id)
    if not ok:
        raise HTTPException(404, detail="Снимок с таким id не найден")
    return {"ok": True, "baseline": ops_store.get_baseline()}


@router.post("/feedback")
async def post_feedback(body: FeedbackBody):
    if body.feedback not in ("good", "bad"):
        raise HTTPException(400, detail="feedback должен быть 'good' или 'bad'")
    found = traces.set_feedback(body.trace_id, body.feedback)
    if not found:
        raise HTTPException(404, detail=f"Трейс {body.trace_id} не найден")
    return {"ok": True, "trace_id": body.trace_id, "feedback": body.feedback}


@router.get("/eval/preview")
async def eval_preview(
    scenario_source: Literal["builtin", "db_approved", "builtin_and_db"] = "builtin",
    db: AsyncSession = Depends(get_db),
):
    """Список фраз, которые уйдут в eval при таком источнике — без вызова LLM (экономия токенов)."""
    body = EvalBody(scenario_source=scenario_source, models=["hermes3"])
    try:
        cases = await _build_eval_cases(body, db)
    except HTTPException as e:
        return {
            "count": 0,
            "scenario_source": scenario_source,
            "cases": [],
            "warning": e.detail if isinstance(e.detail, str) else str(e.detail),
        }
    return {
        "count": len(cases),
        "scenario_source": scenario_source,
        "cases": [
            {
                "text": c["text"],
                "expected": c.get("expected"),
                "scenario_id": c.get("scenario_id"),
                "scenario_title": c.get("scenario_title"),
            }
            for c in cases
        ],
    }


@router.post("/eval")
async def run_eval(body: EvalBody, db: AsyncSession = Depends(get_db)):
    """
    Прогоняет eval-набор через выбранные модели.
    Источник кейсов: тело запроса, встроенный набор, БД (approved) или объединение.
    """
    cases = await _build_eval_cases(body, db)
    out = await run_eval_pipeline(cases, body.models)
    out["scenario_source"] = body.scenario_source if not body.cases else "custom"
    return out


# ── Агенты ─────────────────────────────────────────────────────────

AGENT_IDS = ["analyst", "strategist", "economist", "marketer", "tech_specialist"]

_AGENT_PROMPTS = {
    "analyst": "agents.analyst:ANALYST_SYSTEM_PROMPT",
    "strategist": "agents.strategist:STRATEGIST_SYSTEM_PROMPT",
}


def _agent_prompt_path(agent_id: str) -> "Path":
    from pathlib import Path
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / f"agent_prompt_{agent_id}.txt"


def _get_builtin_prompt(agent_id: str) -> str:
    if agent_id == "analyst":
        from agents.analyst import ANALYST_SYSTEM_PROMPT
        return ANALYST_SYSTEM_PROMPT
    if agent_id == "strategist":
        from agents.strategist import STRATEGIST_SYSTEM_PROMPT
        return STRATEGIST_SYSTEM_PROMPT
    if agent_id == "economist":
        from agents.economist import ECONOMIST_SYSTEM_PROMPT
        return ECONOMIST_SYSTEM_PROMPT
    if agent_id == "marketer":
        from agents.marketer import MARKETER_SYSTEM_PROMPT
        return MARKETER_SYSTEM_PROMPT
    if agent_id == "tech_specialist":
        from agents.tech_specialist import TECH_SPECIALIST_SYSTEM_PROMPT
        return TECH_SPECIALIST_SYSTEM_PROMPT
    return ""


def _get_effective_prompt(agent_id: str) -> tuple[str, str]:
    """Возвращает (промпт, source: 'builtin'|'override')."""
    path = _agent_prompt_path(agent_id)
    if path.exists():
        try:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text, "override"
        except OSError:
            pass
    builtin = _get_builtin_prompt(agent_id)
    return builtin, "builtin"


class AgentPromptBody(BaseModel):
    prompt: str


class AgentRunBody(BaseModel):
    intent: str = "create_lead"
    slots: dict = {}
    transcript: str = ""
    # Режим «лид из CRM»: бэкенд подставляет полный профиль и intent=analyze_lead
    lead_id: Optional[int] = None
    instruction: str = ""


@router.get("/agents")
async def get_agents_list():
    """Список агентов с кратким статусом."""
    result = []
    for agent_id in AGENT_IDS:
        prompt, source = _get_effective_prompt(agent_id)
        implemented = bool(prompt)
        result.append({
            "id": agent_id,
            "source": source,
            "implemented": implemented,
            "prompt_chars": len(prompt),
            "prompt_preview": prompt[:120] if prompt else "",
        })
    return {"agents": result}


@router.get("/agents/{agent_id}/prompt")
async def get_agent_prompt(agent_id: str):
    """Текущий промпт агента (встроенный или override)."""
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    prompt, source = _get_effective_prompt(agent_id)
    return {
        "agent_id": agent_id,
        "prompt": prompt,
        "source": source,
        "chars": len(prompt),
    }


@router.put("/agents/{agent_id}/prompt")
async def put_agent_prompt(agent_id: str, body: AgentPromptBody):
    """Сохранить override промпта агента в backend/data/agent_prompt_{id}.txt"""
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    text = body.prompt.strip()
    if len(text) < 50:
        raise HTTPException(400, detail="Промпт слишком короткий (минимум 50 символов)")
    path = _agent_prompt_path(agent_id)
    path.write_text(text, encoding="utf-8")
    logger.info("Промпт агента %s сохранён (%s симв.)", agent_id, len(text))
    return {"ok": True, "agent_id": agent_id, "chars": len(text), "source": "override"}


@router.delete("/agents/{agent_id}/prompt")
async def delete_agent_prompt(agent_id: str):
    """Удалить override → возврат к встроенному промпту."""
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    path = _agent_prompt_path(agent_id)
    cleared = False
    if path.exists():
        path.unlink()
        cleared = True
    prompt, source = _get_effective_prompt(agent_id)
    return {"ok": True, "cleared": cleared, "source": source, "chars": len(prompt)}


@router.post("/agents/{agent_id}/run")
async def run_agent(agent_id: str, body: AgentRunBody):
    """
    Тест-запуск одного агента вручную.
    При lead_id подгружает лид из БД и выставляет intent=analyze_lead.
    Скор лида аналитиком может обновиться в БД (как при update_lead).
    """
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    if not _get_builtin_prompt(agent_id) and not _agent_prompt_path(agent_id).exists():
        raise HTTPException(501, detail=f"Агент '{agent_id}' ещё не реализован")

    from agents.base import make_initial_state
    from agents.tools import read_lead_by_id
    import time

    slots = dict(body.slots or {})
    intent = body.intent
    transcript = (body.transcript or "").strip()

    if body.lead_id is not None:
        lead = await read_lead_by_id(body.lead_id)
        if not lead:
            raise HTTPException(404, detail="Лид не найден")
        intent = "analyze_lead"
        slots = {**slots, **lead}
        if body.instruction.strip():
            slots["instruction"] = body.instruction.strip()
        if not transcript and body.instruction.strip():
            transcript = body.instruction.strip()

    from rag.retrieve import attach_rag_to_slots

    slots = await attach_rag_to_slots(slots, transcript)
    state = make_initial_state(
        intent=intent,
        slots=slots,
        transcript=transcript,
    )
    state["slots"] = {**slots, "reply": ""}

    t0 = time.monotonic()
    try:
        if agent_id == "analyst":
            from agents import analyst
            result_state = await analyst.run(state)
            output = result_state.get("analyst_output")
        elif agent_id == "strategist":
            from agents import strategist
            result_state = await strategist.run(state)
            output = result_state.get("strategist_output")
        elif agent_id == "economist":
            from agents import economist
            result_state = await economist.run(state)
            output = result_state.get("economist_output")
        elif agent_id == "marketer":
            from agents import marketer
            result_state = await marketer.run(state)
            output = result_state.get("marketer_output")
        elif agent_id == "tech_specialist":
            from agents import tech_specialist
            result_state = await tech_specialist.run(state)
            output = result_state.get("tech_output")
        else:
            raise HTTPException(501, detail=f"Агент '{agent_id}' ещё не реализован")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Тест-запуск агента %s ошибка: %s", agent_id, e)
        raise HTTPException(500, detail=str(e))

    elapsed_ms = round((time.monotonic() - t0) * 1000)
    return {
        "ok": True,
        "agent_id": agent_id,
        "intent": intent,
        "output": output,
        "elapsed_ms": elapsed_ms,
    }
