"""Понятный detail для ответа, когда Битрикс24 недоступен.

Битрикс на ошибках отдаёт HTML со стектрейсом PHP и путями своего сервера
(`/home/bitrix/www/bitrix/modules/...`). Пробрасывать это в браузер нельзя:
оператору бесполезно, а внутренняя структура чужого сервера утекает наружу.
"""
from __future__ import annotations

import re

_SERVER_PATH = re.compile(r"/home/[\w./-]+|[A-Za-z]:\\[\w\\.-]+")
_HTML_TAG = re.compile(r"<[^>]+>")
_PHP_TRACE = re.compile(r"#\d+:.*")
_SPACES = re.compile(r"\s+")

_MAX_LEN = 200

_HINTS: tuple[tuple[str, str], ...] = (
    ("connection refused", "База данных Битрикс24 не отвечает"),
    ("mysql connect error", "База данных Битрикс24 не отвечает"),
    ("connectionexception", "База данных Битрикс24 не отвечает"),
    ("timeout", "Битрикс24 не ответил вовремя"),
    ("insufficient_scope", "Вебхуку Битрикс24 не хватает прав"),
    ("invalid_token", "Токен вебхука Битрикс24 недействителен"),
    ("unauthorized", "Токен вебхука Битрикс24 недействителен"),
)


def bitrix_unavailable_detail(err: BaseException | str) -> str:
    """Короткая причина без стектрейса и путей чужого сервера."""
    raw = str(err or "").strip()
    low = raw.lower()
    for needle, hint in _HINTS:
        if needle in low:
            return f"Битрикс24 недоступен: {hint}. Подробности в логах."

    cleaned = _PHP_TRACE.sub("", _HTML_TAG.sub(" ", raw))
    cleaned = _SPACES.sub(" ", _SERVER_PATH.sub("", cleaned)).strip()
    if not cleaned:
        return "Битрикс24 недоступен. Подробности в логах."
    if len(cleaned) > _MAX_LEN:
        cleaned = cleaned[:_MAX_LEN].rstrip() + "…"
    return f"Битрикс24 недоступен: {cleaned}"
