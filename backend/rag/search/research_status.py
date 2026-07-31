"""Фазы исследования лида — единые подписи для UI и логов."""
from __future__ import annotations

RESEARCH_STATUS_LABELS: dict[str, str] = {
    "searching": "Ищу в интернете (Serper / Brave / Tavily)…",
    "reading_pages": "Читаю страницы источников…",
    "synthesizing": "Синтез выжимки (Groq → Ollama)…",
    "saving": "Сохраняю в карточку…",
    "done_llm": "Готово · выжимка от LLM",
    "done_fallback": "Готово без LLM · выжимка из поиска",
    "error": "Исследование не удалось",
}

_DEFAULT = "Исследование…"


def research_status_label(status: str) -> str:
    return RESEARCH_STATUS_LABELS.get((status or "").strip(), _DEFAULT)


def done_status(llm_used: bool) -> str:
    return "done_llm" if llm_used else "done_fallback"
