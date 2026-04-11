"""
Voice trace logger — записывает каждый проход голосового пайплайна.
Хранит в памяти + персистит в backend/data/traces.json (переживает перезапуск сервера).
"""
import json
import time
import uuid
import logging
from collections import deque
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_TRACES_FILE = _DATA_DIR / "traces.json"
_MAX = 500  # максимум трейсов в буфере

# In-memory буфер
_traces: deque = deque(maxlen=_MAX)


def _load_from_disk() -> None:
    """Загружает трейсы с диска при старте сервера."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not _TRACES_FILE.exists():
        return
    try:
        data = json.loads(_TRACES_FILE.read_text(encoding="utf-8"))
        saved = data.get("traces", [])
        for t in saved[-_MAX:]:
            _traces.append(t)
        logger.info(f"Traces: загружено {len(_traces)} трейсов с диска")
    except Exception as e:
        logger.warning(f"Traces: не удалось загрузить с диска: {e}")


def _save_to_disk() -> None:
    """Сохраняет текущий буфер трейсов на диск (атомарно)."""
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = _TRACES_FILE.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"traces": list(_traces)}, ensure_ascii=False, indent=None),
            encoding="utf-8",
        )
        tmp.replace(_TRACES_FILE)
    except Exception as e:
        logger.warning(f"Traces: не удалось сохранить на диск: {e}")


# Загружаем при импорте модуля (= при старте сервера)
_load_from_disk()


def new_trace(text: str, source: str = "text") -> dict:
    """Создаёт новый трейс, добавляет в буфер и сохраняет на диск."""
    trace = {
        "id": str(uuid.uuid4())[:8],
        "ts": time.time(),
        "source": source,
        "text": text,
        "intent": None,
        "slots": {},
        "agents": [],
        "reply": None,
        "duration_ms": None,
        "model": None,
        "feedback": None,
        "error": None,
    }
    _traces.append(trace)
    _save_to_disk()
    return trace


def finish_trace(trace: dict, result: dict, model: str, duration_ms: float):
    """Обновляет трейс после ответа LLM и сохраняет."""
    trace["intent"] = result.get("intent")
    trace["slots"] = result.get("slots", {})
    trace["agents"] = result.get("agents", [])
    trace["reply"] = result.get("reply")
    trace["duration_ms"] = round(duration_ms)
    trace["model"] = model
    _save_to_disk()
    logger.info(
        f"Trace {trace['id']}: '{trace['text'][:40]}' → {trace['intent']} "
        f"({trace['duration_ms']}ms, {model})"
    )


def error_trace(trace: dict, error: str):
    """Помечает трейс как ошибочный и сохраняет."""
    trace["error"] = error
    _save_to_disk()
    logger.warning(f"Trace {trace['id']} error: {error}")


def set_feedback(trace_id: str, feedback: str) -> bool:
    """Устанавливает фидбек и сохраняет на диск."""
    for t in _traces:
        if t["id"] == trace_id:
            t["feedback"] = feedback
            _save_to_disk()
            logger.info(f"Trace {trace_id} feedback: {feedback}")
            return True
    return False


def get_traces(limit: int = 50, intent_filter: Optional[str] = None) -> list[dict]:
    all_traces = list(reversed(list(_traces)))
    if intent_filter:
        all_traces = [t for t in all_traces if t.get("intent") == intent_filter]
    return all_traces[:limit]


def get_stats() -> dict:
    all_traces = list(_traces)
    if not all_traces:
        return {
            "total": 0, "by_intent": {}, "avg_ms": 0,
            "good": 0, "bad": 0, "errors": 0,
            "groq_pct": 0, "ollama_pct": 0,
        }

    by_intent: dict[str, int] = {}
    durations = []
    good = bad = errors = groq_cnt = ollama_cnt = 0

    for t in all_traces:
        intent = t.get("intent") or "unknown"
        by_intent[intent] = by_intent.get(intent, 0) + 1
        if t.get("duration_ms"):
            durations.append(t["duration_ms"])
        if t.get("feedback") == "good":
            good += 1
        elif t.get("feedback") == "bad":
            bad += 1
        if t.get("error"):
            errors += 1
        model = t.get("model") or ""
        if "groq" in model.lower() or "llama" in model.lower() or "instant" in model.lower():
            groq_cnt += 1
        elif model:
            ollama_cnt += 1

    total = len(all_traces)
    return {
        "total": total,
        "by_intent": dict(sorted(by_intent.items(), key=lambda x: -x[1])),
        "avg_ms": round(sum(durations) / len(durations)) if durations else 0,
        "good": good,
        "bad": bad,
        "errors": errors,
        "groq_pct": round(groq_cnt / total * 100) if total else 0,
        "ollama_pct": round(ollama_cnt / total * 100) if total else 0,
    }
