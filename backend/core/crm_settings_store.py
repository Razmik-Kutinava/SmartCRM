"""
Настройки CRM (воронка, пороги приоритета) — JSON в backend/data/crm_settings.json.
Не трогает строки в БД; этапы используются UI как единый источник для фильтров и смены стадии.
"""
from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_FILE = _DATA_DIR / "crm_settings.json"

DEFAULT_SETTINGS: dict[str, Any] = {
    "stages": [
        "Новый",
        "Квалифицирован",
        "КП отправлено",
        "Переговоры",
        "Выигран",
        "Проигран",
    ],
    # Пороги приоритета по score (шкала score_range). Значения вне max при отображении масштабируются в UI.
    "priority_thresholds": {"critical": 85, "high": 70, "medium": 40},
    "score_range": {"min": 0, "max": 100},
    "default_new_lead_score": 50,
    "notes": "",
    # Балльная подсказка (не перезаписывает score): менеджер владеет баллом, агенты по умолчанию не меняют CRM-score.
    "manager_sets_score": True,
    "agents_may_update_score": False,
    "scoring_advisory_enabled": True,
    # Переопределения для compute_lead_score_advisory; пустой dict = встроенные дефолты в core/lead_score_advisory.py
    "scoring_advisory": {},
    # P2: правила перехода в стадию (пустой список = без доп. гейтов). Пример элемента:
    # {"to_stage": "Выигран", "require_non_empty": ["email", "company"], "require_positive_amount_rub": true}
    "stage_transition_rules": [],
}


def _ensure_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def normalize_stage_transition_rules(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    cleaned_rules: list[dict[str, Any]] = []
    for r in raw:
        if not isinstance(r, dict):
            continue
        ts = str(r.get("to_stage", "")).strip()
        if not ts:
            continue
        item: dict[str, Any] = {"to_stage": ts}
        req = r.get("require_non_empty")
        if isinstance(req, list):
            item["require_non_empty"] = [str(x).strip() for x in req if str(x).strip()]
        if r.get("require_positive_amount_rub") is True:
            item["require_positive_amount_rub"] = True
        cleaned_rules.append(item)
    return cleaned_rules


def load_settings() -> dict[str, Any]:
    _ensure_dir()
    if not _FILE.exists():
        return deepcopy(DEFAULT_SETTINGS)
    try:
        raw = _FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return deepcopy(DEFAULT_SETTINGS)
        merged = deepcopy(DEFAULT_SETTINGS)
        merged.update(data)
        if "stages" in data and isinstance(data["stages"], list):
            merged["stages"] = [str(s).strip() for s in data["stages"] if str(s).strip()]
        if not merged["stages"]:
            merged["stages"] = list(DEFAULT_SETTINGS["stages"])
        if "stage_transition_rules" in data:
            merged["stage_transition_rules"] = normalize_stage_transition_rules(
                data["stage_transition_rules"]
            )
        return merged
    except Exception as e:
        logger.warning("crm_settings: не удалось прочитать %s: %s", _FILE, e)
        return deepcopy(DEFAULT_SETTINGS)


def save_settings(new_data: dict[str, Any]) -> dict[str, Any]:
    _ensure_dir()
    current = load_settings()
    for k, v in new_data.items():
        if k == "stages" and isinstance(v, list):
            cleaned = [str(s).strip() for s in v if str(s).strip()]
            if len(cleaned) != len(set(cleaned)):
                raise ValueError("Этапы воронки должны быть уникальными")
            if not cleaned:
                raise ValueError("Список этапов не может быть пустым")
            current["stages"] = cleaned
        elif k == "stage_transition_rules":
            current["stage_transition_rules"] = normalize_stage_transition_rules(v)
        elif k in DEFAULT_SETTINGS:
            current[k] = v
    _FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("crm_settings сохранён: %s", _FILE)
    return current
