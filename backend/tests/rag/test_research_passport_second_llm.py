"""allow_llm=False не вызывает второй LLM."""
from __future__ import annotations

import pytest

from rag.search.research_passport import extract_passport_from_research_sources


@pytest.mark.asyncio
async def test_passport_extract_allow_llm_false_skips_second_call(monkeypatch):
    import rag.search.research_passport as rp

    called = False

    async def _boom(**kwargs):
        nonlocal called
        called = True
        return {"industry": "should-not"}

    monkeypatch.setattr(rp, "llm_extract_passport_fields", _boom)
    out = await extract_passport_from_research_sources(
        company="ТЕСТ",
        summary="Телефон +7 495 111-22-33 info@test.ru",
        hits=[],
        page_texts="",
        allow_llm=False,
    )
    assert called is False
    assert out.get("phones") or out.get("emails")
