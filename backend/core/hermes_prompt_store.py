"""
Переопределение системного промпта Hermes без правки кода: файл backend/data/hermes_system_prompt.txt
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_OVERRIDE = _DATA_DIR / "hermes_system_prompt.txt"


def get_active_system_prompt(builtin: str) -> str:
    """Возвращает текст из override-файла, если он есть и не пустой, иначе встроенный."""
    if not _OVERRIDE.exists():
        return builtin
    try:
        text = _OVERRIDE.read_text(encoding="utf-8")
        if text.strip():
            return text
    except OSError as e:
        logger.warning("Не удалось прочитать override промпта: %s", e)
    return builtin


def get_prompt_source() -> str:
    """builtin | override"""
    if _OVERRIDE.exists():
        try:
            if _OVERRIDE.read_text(encoding="utf-8").strip():
                return "override"
        except OSError:
            pass
    return "builtin"


def save_override(text: str) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _OVERRIDE.write_text(text, encoding="utf-8")
    logger.info("Сохранён override системного промпта Hermes (%s символов)", len(text))


def clear_override() -> bool:
    if not _OVERRIDE.exists():
        return False
    try:
        _OVERRIDE.unlink()
        logger.info("Удалён override системного промпта, используется встроенный")
        return True
    except OSError as e:
        logger.warning("Не удалось удалить override: %s", e)
        return False


def override_path() -> str:
    return str(_OVERRIDE)
