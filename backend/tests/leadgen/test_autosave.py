"""Автосохранение в CRM при скор ≥ порога (дефолт 30)."""
from __future__ import annotations

import asyncio
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

import pytest

from leadgen.crm_threshold import (
    DEFAULT_CRM_SCORE_THRESHOLD,
    get_crm_score_threshold,
    should_autosave_to_crm,
)
from leadgen.inn_constants import MOCK_INN_TECHNOSOFT

SAMPLE_PROFILE = {
    "company": {
        "inn": MOCK_INN_TECHNOSOFT,
        "name": "ООО ТехноСофт",
        "name_short": "ТехноСофт",
        "status": "ACTIVE",
        "director": "Иванов И.И.",
        "website": "technosoft.ru",
        "dadata_phones": ["+74950000000"],
        "dadata_emails": ["info@technosoft.ru"],
    },
    "financials": {"revenue": 120_000_000, "finance_year": 2024},
    "tech": {"maturity": "medium"},
    "news": [],
    "contact": {"email": "info@technosoft.ru"},
}


class TestCrmThreshold:
    def test_default_threshold(self):
        assert DEFAULT_CRM_SCORE_THRESHOLD == 30

    def test_should_autosave_at_threshold(self):
        assert should_autosave_to_crm(True, 30) is True
        assert should_autosave_to_crm(True, 29) is False
        assert should_autosave_to_crm(False, 99) is False

    def test_should_autosave_custom_threshold(self):
        assert should_autosave_to_crm(True, 54, threshold=55) is False
        assert should_autosave_to_crm(True, 55, threshold=55) is True

    def test_get_threshold_from_config(self, tmp_path, monkeypatch):
        import leadgen.crm_threshold as mod

        cfg = tmp_path / "leadgen_config.json"
        cfg.write_text('{"score_threshold_crm": 42}', encoding="utf-8")
        monkeypatch.setattr(mod, "_CONFIG_PATH", str(cfg))
        assert get_crm_score_threshold() == 42


class TestPersistSave:
    @pytest.mark.asyncio
    async def test_save_to_crm_writes_lead(self, db_engine):
        from contextlib import asynccontextmanager

        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from db.models import Lead
        from leadgen.pipeline.persist import _save_to_crm

        factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

        @asynccontextmanager
        async def fake_session():
            async with factory() as session:
                yield session

        card = {
            "company_name": "ООО Тест Автосейв",
            "inn": MOCK_INN_TECHNOSOFT,
            "final_score": 74,
            "lpr": {"name": "Директор", "phone": "+79000000000", "email": "a@b.ru"},
            "financials": {},
            "tech_stack": {},
        }
        with patch("db.session.get_db_session", fake_session):
            lead_id = await _save_to_crm(card)
        assert lead_id is not None

        async with factory() as session:
            lead = await session.get(Lead, lead_id)
            assert lead is not None
            assert lead.company == "ООО Тест Автосейв"
            assert lead.score == 74
            assert lead.source == "Лидогенератор"


def _pipeline_patches(score: int):
    mock_company = SAMPLE_PROFILE["company"].copy()
    mock_fin = SAMPLE_PROFILE["financials"].copy()
    return (
        patch("leadgen.modules.checko.fetch_company", new=AsyncMock(return_value=mock_company)),
        patch("leadgen.modules.checko.fetch_full_profile", new=AsyncMock(return_value=mock_fin)),
        patch("leadgen.modules.checko._available", return_value=True),
        patch("leadgen.modules.builtwith.fetch_tech_stack", new=AsyncMock(return_value=SAMPLE_PROFILE["tech"])),
        patch("leadgen.modules.newsapi.fetch_news", new=AsyncMock(return_value=SAMPLE_PROFILE["news"])),
        patch("leadgen.modules.buster.find_email", new=AsyncMock(return_value=SAMPLE_PROFILE["contact"])),
        patch("rag.search.free_search", new=AsyncMock(return_value={"formatted_block": ""})),
        patch(
            "core.llm.chat",
            new=AsyncMock(
                return_value='{"score":75,"summary":"ok","hook":"test","script_outline":["Hello"],"triggers":[]}'
            ),
        ),
        patch("leadgen.pipeline.run_pipeline._compute_final_score", return_value=score),
    )


class TestPipelineAutosave:
    def test_autosave_skipped_below_threshold(self):
        save_mock = AsyncMock(return_value=101)

        async def run():
            with ExitStack() as stack:
                for p in _pipeline_patches(29):
                    stack.enter_context(p)
                stack.enter_context(
                    patch("leadgen.pipeline.run_pipeline._save_to_crm", save_mock)
                )
                from leadgen.pipeline import run_pipeline

                return await run_pipeline(inn=MOCK_INN_TECHNOSOFT, save_to_crm=True)

        result = asyncio.run(run())
        save_mock.assert_not_awaited()
        assert "crm_lead_id" not in result

    def test_autosave_when_at_threshold(self):
        save_mock = AsyncMock(return_value=202)

        async def run():
            with ExitStack() as stack:
                for p in _pipeline_patches(30):
                    stack.enter_context(p)
                stack.enter_context(
                    patch("leadgen.pipeline.run_pipeline._save_to_crm", save_mock)
                )
                from leadgen.pipeline import run_pipeline

                return await run_pipeline(inn=MOCK_INN_TECHNOSOFT, save_to_crm=True)

        result = asyncio.run(run())
        save_mock.assert_awaited_once()
        assert result["crm_lead_id"] == 202
