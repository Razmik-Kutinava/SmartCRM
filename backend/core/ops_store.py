"""
Локальное хранилище для Ops: снимки метрик, очередь решений, базовая линия.
Файлы в backend/data/ — работает без PostgreSQL.
"""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SNAPSHOTS = _DATA_DIR / "ops_snapshots.json"
_QUEUE = _DATA_DIR / "ops_queue.json"
_BASELINE = _DATA_DIR / "ops_baseline.json"


def _ensure_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: Any) -> Any:
    _ensure_dir()
    if not path.exists():
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("ops_store: не удалось прочитать %s: %s", path, e)
        return default


def _write_json(path: Path, data: Any) -> None:
    _ensure_dir()
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def get_snapshots(limit: int = 30) -> list[dict[str, Any]]:
    data = _read_json(_SNAPSHOTS, {"snapshots": []})
    snaps = data.get("snapshots", [])
    return snaps[-limit:]


def append_snapshot(
    stats: dict[str, Any],
    source: str = "auto",
    label: str = "",
    prompt_text: str = "",
    prompt_source: str = "",
) -> dict[str, Any]:
    """Добавляет снимок статистики трейсов + текущий промпт (версия)."""
    data = _read_json(_SNAPSHOTS, {"snapshots": []})
    snaps: list = data.setdefault("snapshots", [])
    entry = {
        "id": str(uuid.uuid4())[:12],
        "ts": __import__("time").time(),
        "source": source,
        "label": label or None,
        "stats": stats,
        # версия промпта на момент снимка
        "prompt_chars": len(prompt_text) if prompt_text else None,
        "prompt_source": prompt_source or None,
        "prompt_preview": prompt_text[:120] if prompt_text else None,
    }
    snaps.append(entry)
    data["snapshots"] = snaps[-200:]
    _write_json(_SNAPSHOTS, data)
    return entry


def get_baseline() -> Optional[dict[str, Any]]:
    return _read_json(_BASELINE, {})


def set_baseline_snapshot_id(snapshot_id: str) -> bool:
    """Устанавливает линию «было» по id снимка."""
    data = _read_json(_SNAPSHOTS, {"snapshots": []})
    for s in data.get("snapshots", []):
        if s.get("id") == snapshot_id:
            _write_json(_BASELINE, {"snapshot_id": snapshot_id, "stats": s.get("stats"), "ts": s.get("ts")})
            return True
    return False


def load_queue() -> list[dict[str, Any]]:
    data = _read_json(_QUEUE, {"items": []})
    return data.get("items", [])


def save_queue(items: list[dict[str, Any]]) -> None:
    _write_json(_QUEUE, {"items": items})


def resolve_queue_item(item_id: str, status: str, note: str = "") -> bool:
    """status: done | dismissed"""
    items = load_queue()
    for it in items:
        if it.get("id") == item_id:
            it["status"] = status
            it["resolve_note"] = note
            save_queue(items)
            return True
    return False


def _feedback_ratio(traces_list: list[dict]) -> tuple[int, int, float]:
    good = sum(1 for t in traces_list if t.get("feedback") == "good")
    bad = sum(1 for t in traces_list if t.get("feedback") == "bad")
    denom = good + bad
    ratio = (bad / denom) if denom else 0.0
    return good, bad, ratio


def _build_proposals(
    stats: dict[str, Any],
    good: int,
    bad: int,
    bad_ratio: float,
    err_pct: int,
    errors: int,
) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    by_intent = stats.get("by_intent") or {}
    top_intents = sorted(by_intent.items(), key=lambda x: -x[1])[:5]
    if top_intents:
        proposals.append({
            "id": "prop-intents",
            "title": "Распределение интентов",
            "body": "Чаще всего распознаётся: "
            + ", ".join(f"{i} ({c})" for i, c in top_intents)
            + ". При смещении в noop стоит добавить few-shot примеры.",
            "confidence": 0.75,
        })
    if bad_ratio > 0.2 and good + bad > 0:
        proposals.append({
            "id": "prop-feedback",
            "title": "Уточнить промпт Hermes",
            "body": "Доля негативного фидбека заметна. Соберите 3–5 реальных фраз с 👎 и добавьте их в eval.",
            "confidence": 0.82,
        })
    if err_pct > 0:
        proposals.append({
            "id": "prop-errors",
            "title": "Проверить цепочку STT → Hermes",
            "body": f"Зафиксировано {errors} ошибок. Откройте трейсы с ошибкой и проверьте формат JSON от модели.",
            "confidence": 0.7,
        })
    proposals.append({
        "id": "prop-eval",
        "title": "Запустить eval на этой неделе",
        "body": "Сравните Groq и Hermes3 на странице «Eval»: стабильность интентов лучше всего видна по проценту совпадений.",
        "confidence": 0.6,
    })
    return proposals


def recompute_queue_and_suggestions(update_queue: bool = True) -> dict[str, Any]:
    """
    Анализирует in-memory трейсы и обновляет очередь + текстовые предложения.
    Не вызывает LLM — только эвристики (быстро и предсказуемо).
    """
    from core import traces

    all_t = list(traces._traces)  # noqa: SLF001 — внутренний буфер
    recent = list(reversed(all_t))[:100]
    stats = traces.get_stats()

    good, bad, bad_ratio = _feedback_ratio(recent)
    errors = sum(1 for t in recent if t.get("error"))
    err_pct = round(errors / len(recent) * 100) if recent else 0

    new_items: list[dict[str, Any]] = []
    now = __import__("time").time()

    def add_item(severity: str, title: str, detail: str, kind: str, key: str) -> None:
        new_items.append({
            "id": f"auto-{key}",
            "severity": severity,
            "title": title,
            "detail": detail,
            "kind": kind,
            "status": "open",
            "created_ts": now,
            "trace_ids": [],
        })

    if err_pct >= 15 and len(recent) >= 5:
        add_item(
            "critical",
            "Много ошибок в голосовом пайплайне",
            f"За последние записи: {errors} ошибок (~{err_pct}%). Проверьте Groq, Ollama и логи Hermes.",
            "action",
            "errors",
        )
    elif err_pct >= 5 and len(recent) >= 10:
        add_item(
            "medium",
            "Повышенная доля ошибок",
            f"Ошибок: {errors} из {len(recent)}. Имеет смысл посмотреть трейсы с пометкой «Ошибка».",
            "review",
            "errors-soft",
        )

    if good + bad >= 5 and bad_ratio >= 0.35:
        add_item(
            "medium",
            "Низкая доля положительной обратной связи",
            f"👎 {bad} против 👍 {good}. Разберите плохие трейсы и обновите промпт Hermes.",
            "review",
            "feedback",
        )

    groq_pct = stats.get("groq_pct", 0)
    if groq_pct < 40 and stats.get("total", 0) >= 8:
        add_item(
            "low",
            "Частый fallback на Ollama",
            f"Только {groq_pct}% запросов через Groq. Проверьте ключ GROQ_API_KEY и лимиты.",
            "review",
            "groq",
        )

    # Сравнение с предыдущим снимком
    snaps = get_snapshots(5)
    if len(snaps) >= 2:
        prev, cur = snaps[-2], snaps[-1]
        p_good = prev.get("stats", {}).get("good", 0)
        c_good = cur.get("stats", {}).get("good", 0)
        if c_good < p_good and p_good > 0:
            add_item(
                "medium",
                "Метрика «хороших» оценок снизилась относительно снимка",
                f"Было 👍 {p_good}, в последнем снимке 👍 {c_good}. Сравните раздел «История».",
                "review",
                "snapshot-good",
            )

    if update_queue:
        existing = load_queue()
        manual_open = [
            x for x in existing
            if not str(x.get("id", "")).startswith("auto-") and x.get("status") == "open"
        ]
        resolved = [x for x in existing if x.get("status") in ("done", "dismissed")]
        save_queue(manual_open + new_items + resolved)

    proposals = _build_proposals(stats, good, bad, bad_ratio, err_pct, errors)

    return {
        "stats": stats,
        "queue_generated": len(new_items),
        "suggestions": proposals,
        "signals": {
            "errors_recent": errors,
            "error_pct": err_pct,
            "feedback_good": good,
            "feedback_bad": bad,
            "bad_feedback_ratio": round(bad_ratio, 2),
        },
    }


def generate_insights_only() -> dict[str, Any]:
    """Инсайты без перезаписи очереди (для частого опроса UI)."""
    return recompute_queue_and_suggestions(update_queue=False)


def history_comparison() -> dict[str, Any]:
    """
    Сравнение «базовая линия / прошлый снимок / текущие live-статы» с процентами изменения.
    """
    from core import traces

    baseline = get_baseline()
    snaps = get_snapshots(30)
    live = traces.get_stats()

    def pick(d: Optional[dict], key: str, default: float = 0) -> float:
        if not d:
            return default
        v = d.get(key)
        return float(v) if v is not None else default

    def pct_change(old_val: float, new_val: float) -> Optional[float]:
        if old_val == 0:
            return None if new_val == 0 else 100.0
        return round((new_val - old_val) / old_val * 100, 1)

    prev_snap = snaps[-2] if len(snaps) >= 2 else None
    last_snap = snaps[-1] if snaps else None

    base_stats = baseline.get("stats") if baseline else None
    prev_stats = prev_snap.get("stats") if prev_snap else None
    last_stats = last_snap.get("stats") if last_snap else None

    metrics = [
        {
            "key": "total",
            "label": "Команд в буфере трейсов",
            "live": pick(live, "total"),
            "baseline": pick(base_stats, "total") if base_stats else None,
            "last_snapshot": pick(last_stats, "total") if last_stats else None,
        },
        {
            "key": "good",
            "label": "Оценок 👍 (накоплено)",
            "live": pick(live, "good"),
            "baseline": pick(base_stats, "good") if base_stats else None,
            "last_snapshot": pick(last_stats, "good") if last_stats else None,
        },
        {
            "key": "bad",
            "label": "Оценок 👎 (накоплено)",
            "live": pick(live, "bad"),
            "baseline": pick(base_stats, "bad") if base_stats else None,
            "last_snapshot": pick(last_stats, "bad") if last_stats else None,
        },
        {
            "key": "errors",
            "label": "Ошибок в трейсах",
            "live": pick(live, "errors"),
            "baseline": pick(base_stats, "errors") if base_stats else None,
            "last_snapshot": pick(last_stats, "errors") if last_stats else None,
        },
        {
            "key": "avg_ms",
            "label": "Среднее время ответа, мс",
            "live": pick(live, "avg_ms"),
            "baseline": pick(base_stats, "avg_ms") if base_stats else None,
            "last_snapshot": pick(last_stats, "avg_ms") if last_stats else None,
        },
    ]

    for m in metrics:
        live_v = m["live"]
        base_v = m.get("baseline")
        prev_v = None
        if prev_stats:
            prev_v = pick(prev_stats, m["key"])
        m["vs_baseline_pct"] = pct_change(base_v, live_v) if base_v is not None else None
        m["vs_previous_snapshot_pct"] = pct_change(prev_v, live_v) if prev_v is not None else None

    return {
        "baseline_set": bool(baseline and baseline.get("snapshot_id")),
        "baseline_ts": baseline.get("ts") if baseline else None,
        "snapshots_count": len(snaps),
        "metrics": metrics,
        "snapshots": snaps[-10:],
    }
