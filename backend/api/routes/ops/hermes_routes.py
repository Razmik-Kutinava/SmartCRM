"""Ops API — промпт Hermes, few-shot, suggest-prompt, improvement."""
import json as _json
import logging
import os

from fastapi import APIRouter, HTTPException

from core import ops_store, traces

from .schemas import AddExampleBody, HermesPromptBody, SuggestPromptBody

logger = logging.getLogger(__name__)
router = APIRouter()


def _append_examples_to_prompt(current: str, block: str) -> str:
    marker = '"""'
    idx = current.rfind(marker)
    if idx != -1:
        return current[:idx].rstrip() + "\n" + block + current[idx:]
    return current.rstrip() + "\n" + block


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


@router.post("/hermes/add-example")
async def add_example_to_prompt(body: AddExampleBody):
    """Добавляет few-shot пример в системный промпт Hermes."""
    from core.hermes import get_system_prompt
    from core.hermes_prompt_store import save_override

    current = get_system_prompt()
    out = {
        "intent": body.intent,
        "agents": ["analyst"],
        "slots": body.slots,
        "parallel": False,
        "reply": body.reply or f"Выполняю: {body.intent}.",
    }
    example_str = f'\nInput: "{body.phrase}"\nOutput: {_json.dumps(out, ensure_ascii=False)}\n'
    new_prompt = _append_examples_to_prompt(current, example_str)
    save_override(new_prompt)
    logger.info("Добавлен few-shot пример в промпт: '%s' → %s", body.phrase[:40], body.intent)
    return {"ok": True, "example": example_str.strip(), "prompt_chars": len(new_prompt)}


@router.post("/hermes/bulk-eval")
async def bulk_eval(body: list[AddExampleBody]):
    """Прогоняет список фраз через Groq и проверяет совпадение интента."""
    import asyncio
    import re

    from groq import AsyncGroq

    from core.hermes import get_system_prompt

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise HTTPException(503, detail="GROQ_API_KEY не задан")

    if len(body) > 200:
        raise HTTPException(413, detail="bulk-eval: максимум 200 фраз за раз")

    client = AsyncGroq(api_key=api_key)
    system = get_system_prompt()
    results = []

    try:
        for item in body:
            await asyncio.sleep(2.0)
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
                raw = resp.choices[0].message.content or ""
                parsed = {}
                try:
                    parsed = _json.loads(raw)
                except Exception:
                    m = re.search(r"\{.*\}", raw, re.DOTALL)
                    if m:
                        try:
                            parsed = _json.loads(m.group())
                        except Exception:
                            parsed = {}
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
                    "error": type(e).__name__,
                })
    finally:
        try:
            await client.close()
        except Exception:
            pass

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

    new_prompt = _append_examples_to_prompt(current, block)
    save_override(new_prompt)
    logger.info("Bulk-добавлено %d few-shot примеров в промпт", len(body))
    return {"ok": True, "added": len(body), "prompt_chars": len(new_prompt)}


@router.get("/improvement")
async def get_improvement_workspace():
    """Единая сводка для страницы «Улучшение»: промпт, инсайты, подсказки процесса."""
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


@router.post("/suggest-prompt")
async def suggest_prompt(body: SuggestPromptBody = SuggestPromptBody()):
    """Предлагает улучшения промпта по плохим трейсам (не применяет автоматически)."""
    from groq import AsyncGroq

    from core.hermes import get_system_prompt

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise HTTPException(503, detail="GROQ_API_KEY не задан — не могу вызвать Groq")

    all_traces = traces.get_traces(limit=200)
    bad = [t for t in all_traces if t.get("feedback") == "bad" or t.get("error")][: body.max_bad_traces]

    if not bad:
        return {
            "ok": True,
            "has_suggestion": False,
            "message": "Нет плохих трейсов (👎) для анализа. Поставь минус на проблемных командах.",
            "suggestion": "",
            "few_shot_examples": [],
        }

    current_prompt = get_system_prompt()
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
    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.3,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
    finally:
        try:
            await client.close()
        except Exception:
            pass

    raw = response.choices[0].message.content or ""
    try:
        result = _json.loads(raw)
    except Exception:
        result = {"patterns": raw, "explanation": raw, "few_shot_examples": []}

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
