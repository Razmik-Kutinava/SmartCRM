"""Тесты RAG_AUTO_STRUCTURE_LLM."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from rag.qa_structure import (
    auto_structure_llm_enabled,
    build_hit_rag_text,
    hit_to_rag_text_heuristic,
)


def test_heuristic_qa_format():
    text = hit_to_rag_text_heuristic("CRM", {"title": "T", "snippet": "Факт", "url": "https://x.ru"})
    assert "Вопрос: CRM" in text
    assert "Факт" in text


@pytest.mark.asyncio
async def test_build_hit_rag_text_heuristic_by_default(monkeypatch):
    monkeypatch.delenv("RAG_AUTO_STRUCTURE_LLM", raising=False)
    text = await build_hit_rag_text("запрос", {"title": "A", "snippet": "B", "url": "https://a.ru"})
    assert "Вопрос: запрос" in text


@pytest.mark.asyncio
async def test_build_hit_rag_text_llm_when_enabled(monkeypatch):
    monkeypatch.setenv("RAG_AUTO_STRUCTURE_LLM", "1")

    async def fake_chat(*_a, **_k):
        return '{"question":"Как работает CRM?","answer":"SaaS для продаж"}'

    monkeypatch.setattr("core.llm.chat", fake_chat)
    text = await build_hit_rag_text("CRM", {"title": "x", "snippet": "y", "url": "https://z.ru"})
    assert "Как работает CRM?" in text
    assert "SaaS для продаж" in text


def test_auto_structure_llm_enabled_flag(monkeypatch):
    monkeypatch.setenv("RAG_AUTO_STRUCTURE_LLM", "1")
    assert auto_structure_llm_enabled() is True
    monkeypatch.setenv("RAG_AUTO_STRUCTURE_LLM", "0")
    assert auto_structure_llm_enabled() is False
