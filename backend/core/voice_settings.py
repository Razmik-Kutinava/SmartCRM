"""
Настройки Groq Whisper: сохранение в backend/data/whisper_settings.json.
Если файла нет — используются значения из переменных окружения (как в voice.whisper).
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SETTINGS_PATH = _DATA_DIR / "whisper_settings.json"

_ALLOWED_MODELS = frozenset({"whisper-large-v3-turbo", "whisper-large-v3"})


def _env_defaults() -> dict[str, Any]:
    """Те же значения по умолчанию, что в voice.whisper при старте."""
    _default_prompt = (
        "SmartCRM, голосовые команды на русском. "
        "Лид, лиды, задача, контакт, компания, этап, воронка, бюджет, сделка. "
        "ООО Ромашка, ООО Вектор, Акме, TechSoft, Техпром, Альфа. "
        "ЛПР, ИТ-директор, менеджер по продажам, ответственный. "
        "Города: Москва, Санкт-Петербург, Казань, Ереван. "
        "Имена: Иван, Мария, Петров, Сидоров. "
        "CRM, API, email, телефон."
    )
    pre = os.getenv("WHISPER_FFMPEG_PREPROCESS", "1").strip().lower()
    ffmpeg = pre in ("1", "true", "yes", "on")
    return {
        "model": os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo"),
        "language": (os.getenv("WHISPER_LANGUAGE", "ru").strip() or "ru"),
        "temperature": float(os.getenv("WHISPER_TEMPERATURE", "0")),
        "prompt": (os.getenv("WHISPER_PROMPT", _default_prompt).strip() or _default_prompt),
        "ffmpeg_preprocess": ffmpeg,
    }


def _read_file() -> dict[str, Any] | None:
    if not _SETTINGS_PATH.exists():
        return None
    try:
        with open(_SETTINGS_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            return None
        return raw
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("voice_settings: не удалось прочитать %s: %s", _SETTINGS_PATH, e)
        return None


def _ensure_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _validate_and_normalize(data: dict[str, Any]) -> dict[str, Any]:
    env = _env_defaults()
    model = str(data.get("model", env["model"])).strip()
    if model not in _ALLOWED_MODELS:
        model = env["model"]
        if model not in _ALLOWED_MODELS:
            model = "whisper-large-v3-turbo"

    lang = str(data.get("language", env["language"])).strip().lower() or "ru"
    if len(lang) > 16:
        lang = lang[:16]

    try:
        temp = float(data.get("temperature", env["temperature"]))
    except (TypeError, ValueError):
        temp = float(env["temperature"])
    temp = max(0.0, min(1.0, temp))

    prompt = str(data.get("prompt", env["prompt"]))
    if len(prompt) > 8000:
        prompt = prompt[:8000]

    ff = data.get("ffmpeg_preprocess", env["ffmpeg_preprocess"])
    if isinstance(ff, str):
        ffmpeg_preprocess = ff.strip().lower() in ("1", "true", "yes", "on")
    else:
        ffmpeg_preprocess = bool(ff)

    return {
        "model": model,
        "language": lang,
        "temperature": temp,
        "prompt": prompt,
        "ffmpeg_preprocess": ffmpeg_preprocess,
    }


def get_resolved_whisper_params() -> dict[str, Any]:
    """Параметры для вызова Whisper API (файл перекрывает env)."""
    stored = _read_file()
    env = _env_defaults()
    if not stored:
        return env
    merged = {**env, **stored}
    return _validate_and_normalize(merged)


def get_settings_for_api() -> dict[str, Any]:
    """Ответ GET: эффективные настройки + признак файла и дефолты из env."""
    env = _env_defaults()
    stored = _read_file()
    effective = get_resolved_whisper_params()
    return {
        "effective": effective,
        "defaults_from_env": env,
        "saved_to_disk": stored is not None,
        "updated_at": stored.get("updated_at") if stored else None,
    }


def save_settings(data: dict[str, Any]) -> dict[str, Any]:
    """Сохраняет валидированные настройки в JSON."""
    normalized = _validate_and_normalize(data)
    payload = {
        **normalized,
        "updated_at": time.time(),
    }
    _ensure_dir()
    tmp = _SETTINGS_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(_SETTINGS_PATH)
    logger.info("voice_settings: сохранено в %s", _SETTINGS_PATH)
    return normalized


def clear_settings_file() -> bool:
    """Удаляет файл — снова только env."""
    try:
        if _SETTINGS_PATH.exists():
            _SETTINGS_PATH.unlink()
            logger.info("voice_settings: файл удалён, используются переменные окружения")
            return True
    except OSError as e:
        logger.warning("voice_settings: не удалось удалить файл: %s", e)
    return False
