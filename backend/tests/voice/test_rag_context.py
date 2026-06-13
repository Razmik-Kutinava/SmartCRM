"""Тесты voice/rag_context.py."""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from voice.rag_context import fetch_rag_answer


@pytest.mark.asyncio
async def test_fetch_rag_answer_empty_question():
    out = await fetch_rag_answer({}, "")
    assert "уточни" in out["final_reply"].lower()


@pytest.mark.asyncio
async def test_fetch_rag_answer_with_context():
    with patch("rag.retrieve.retrieve_context_sync", return_value="Документ про CRM."):
        out = await fetch_rag_answer({"question": "CRM"}, "CRM")
    assert out["rag_hits"] >= 1
    assert "CRM" in out["rag_answer"]


@pytest.mark.asyncio
async def test_fetch_rag_answer_no_hits():
    with patch("rag.retrieve.retrieve_context_sync", return_value=""):
        out = await fetch_rag_answer({"question": "xyznone"}, "xyznone")
    assert out["rag_hits"] == 0
