"""
Тесты лидогенерации SmartCRM.

Покрытие:
  1. Модуль Checko — _parse_company, _parse_finances
  2. Модуль FNS — парсинг бухотчётности
  3. Модуль BuiltWith — оценка зрелости, clean_domain
  4. Модуль NewsAPI — фильтр по дате, extract_triggers
  5. Модуль Buster — транслитерация, генерация паттернов
  6. Анализаторы — все 5 анализов + compute_profile_analyses
  7. Pipeline — _compute_final_score, _build_lead_card, _extract_domain, _fmt_money
  8. API config — load/save/patch
  9. Пайплайн (интеграция, мок) — run_pipeline с моком Checko
 10. Hermes — новые интенты в промпте
 11. Оркестратор — leadgen интенты в _AGENT_INTENTS
"""
import asyncio
import json
import sys
import os
import pytest

# Добавляем backend в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ══════════════════════════════════════════════════════════════════════════════
# 1. Checko — идентификация и контакты
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckoIdentification:
    def test_parse_company_with_contacts(self):
        """Checko возвращает телефоны, email и сайт из поля Контакты."""
        from leadgen.modules.checko import _parse_company
        raw = {
            "ИНН": "7736207543",
            "КПП": "773601001",
            "ОГРН": "1234567890123",
            "НаимПолн": "ООО ТехноСофт",
            "НаимСокр": "ТехноСофт",
            "Статус": {"Наим": "Действует"},
            "ОКВЭД": {"Код": "62.01", "Наим": "Разработка ПО"},
            "ЮрАдрес": {"АдресРФ": "г Москва, ул Ленина 1", "НасПункт": "г Москва"},
            "Руковод": [{"ФИО": "Иванов Иван Иванович", "НаимДолжн": "Генеральный директор"}],
            "Учред": {"ФЛ": [{"ФИО": "Иванов И.И.", "ИНН": "123456789012", "Доля": {"Процент": 100}}]},
            "Контакты": {"Тел": ["+74956001234"], "Эмейл": ["info@technosoft.ru"], "Сайт": "technosoft.ru"},
        }
        result = _parse_company(raw)
        assert result is not None
        assert result["inn"] == "7736207543"
        assert result["name"] == "ООО ТехноСофт"
        assert result["status"] == "ACTIVE"
        assert result["director"] == "Иванов Иван Иванович"
        assert result["website"] == "technosoft.ru"
        assert "+74956001234" in result["dadata_phones"]
        assert "info@technosoft.ru" in result["dadata_emails"]

    def test_parse_company_website_from_email(self):
        """Если нет сайта — домен берётся из email."""
        from leadgen.modules.checko import _parse_company
        raw = {
            "ИНН": "1234567890",
            "НаимСокр": "ООО Тест",
            "Статус": "Действует",
            "Контакты": {"Эмейл": ["contact@mycompany.ru"]},
        }
        result = _parse_company(raw)
        assert result is not None
        assert result["website"] == "mycompany.ru"

    def test_search_companies_without_key_uses_egrul_rows(self, monkeypatch):
        """Без CHECKO_API_KEY поиск должен возвращать минимальные карточки из ЕГРЮЛ rows."""
        import asyncio
        from leadgen.modules import checko as checko_mod

        async def fake_rows(query: str, count: int = 5):
            return [{
                "i": "7700000000",
                "p": "770001001",
                "o": "1027700000000",
                "n": "ООО Тест Компания",
                "c": "ООО Тест",
                "g": "г. Москва",
                "r": "01.01.2020",
            }]

        monkeypatch.setattr(checko_mod, "_available", lambda: False)
        monkeypatch.setattr(checko_mod, "_search_egrul_rows", fake_rows)
        res = asyncio.get_event_loop().run_until_complete(checko_mod.search_companies("тест", count=3))
        assert len(res) == 1
        assert res[0]["inn"] == "7700000000"
        assert "Тест" in res[0]["name"]


# ══════════════════════════════════════════════════════════════════════════════
# 2. FNS
# ══════════════════════════════════════════════════════════════════════════════

class TestFNS:
    def test_parse_bo_charts_growing(self):
        from leadgen.modules.fns import _parse_bo_charts
        charts = [
            {"code": "2110", "values": [
                {"year": 2022, "value": 100_000_000},
                {"year": 2023, "value": 120_000_000},
            ]},
            {"code": "2400", "values": [
                {"year": 2022, "value": 10_000_000},
                {"year": 2023, "value": 15_000_000},
            ]},
        ]
        result = _parse_bo_charts(charts)
        assert result["revenue"] == 120_000_000
        assert result["revenue_trend"] == "growing"

    def test_parse_bo_charts_declining(self):
        from leadgen.modules.fns import _parse_bo_charts
        charts = [
            {"code": "2110", "values": [
                {"year": 2022, "value": 200_000_000},
                {"year": 2023, "value": 150_000_000},
            ]},
        ]
        result = _parse_bo_charts(charts)
        assert result["revenue_trend"] == "declining"

    def test_parse_bo_charts_stable(self):
        from leadgen.modules.fns import _parse_bo_charts
        charts = [
            {"code": "2110", "values": [
                {"year": 2022, "value": 100_000_000},
                {"year": 2023, "value": 103_000_000},
            ]},
        ]
        result = _parse_bo_charts(charts)
        assert result["revenue_trend"] == "stable"

    def test_parse_bo_charts_empty(self):
        from leadgen.modules.fns import _parse_bo_charts
        result = _parse_bo_charts([])
        assert result["revenue"] is None
        assert result["revenue_trend"] == "unknown"


# ══════════════════════════════════════════════════════════════════════════════
# 3. BuiltWith
# ══════════════════════════════════════════════════════════════════════════════

class TestBuiltWith:
    def test_clean_domain(self):
        from leadgen.modules.builtwith import _clean_domain
        assert _clean_domain("https://www.example.com/path") == "example.com"
        assert _clean_domain("http://test.ru") == "test.ru"
        assert _clean_domain("example.com") == "example.com"

    def test_assess_maturity_low(self):
        from leadgen.modules.builtwith import _assess_maturity
        assert _assess_maturity(group_count=2, has_enterprise=False, has_crm=False, total_signals=5) == "low"

    def test_assess_maturity_medium(self):
        from leadgen.modules.builtwith import _assess_maturity
        assert _assess_maturity(group_count=6, has_enterprise=False, has_crm=False, total_signals=15) == "medium"

    def test_assess_maturity_enterprise(self):
        from leadgen.modules.builtwith import _assess_maturity
        assert _assess_maturity(group_count=3, has_enterprise=True, has_crm=True, total_signals=60) == "enterprise"

    def test_no_api_key_skips(self):
        """Без ключа fetch_tech_stack возвращает _skipped."""
        import asyncio
        from unittest.mock import patch
        from leadgen.modules.builtwith import fetch_tech_stack
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("BUILTWITH_API_KEY", None)
            result = asyncio.get_event_loop().run_until_complete(
                fetch_tech_stack("example.com")
            )
        assert result.get("_skipped") or result == {}


# ══════════════════════════════════════════════════════════════════════════════
# 4. NewsAPI
# ══════════════════════════════════════════════════════════════════════════════

class TestNewsAPI:
    def test_calc_age_days_valid(self):
        from leadgen.modules.newsapi import _calc_age_days
        from datetime import datetime, timezone, timedelta
        recent = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        age = _calc_age_days(recent)
        assert 4 <= age <= 6

    def test_calc_age_days_invalid(self):
        from leadgen.modules.newsapi import _calc_age_days
        assert _calc_age_days("not-a-date") is None

    def test_parse_article(self):
        from leadgen.modules.newsapi import _parse_article
        from datetime import datetime, timezone, timedelta
        pub = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        a = _parse_article({
            "title": "Компания привлекла инвестиции",
            "description": "100 млн рублей",
            "url": "https://example.com",
            "source": {"name": "RBC"},
            "publishedAt": pub,
        })
        assert a["is_fresh"] is True
        assert a["age_days"] <= 15

    def test_extract_triggers(self):
        from leadgen.modules.newsapi import extract_triggers
        articles = [
            {"title": "Компания привлекла инвестиции раунд А", "description": ""},
            {"title": "Активный найм сотрудников IT", "description": ""},
            {"title": "Продажи выросли", "description": ""},
        ]
        triggers = extract_triggers(articles)
        assert "Привлечение инвестиций" in triggers or "Инвестиционный раунд" in triggers
        assert "Активный найм" in triggers

    def test_no_api_key_returns_empty(self):
        import asyncio
        from leadgen.modules.newsapi import fetch_news
        os.environ.pop("NEWS_API_KEY", None)
        result = asyncio.get_event_loop().run_until_complete(fetch_news("Ромашка"))
        assert result == []


# ══════════════════════════════════════════════════════════════════════════════
# 5. Buster
# ══════════════════════════════════════════════════════════════════════════════

class TestBuster:
    def test_translit(self):
        from leadgen.modules.buster import _translit
        assert _translit("Иван") == "ivan"
        assert _translit("Петров") == "petrov"

    def test_generate_pattern_ru(self):
        from leadgen.modules.buster import _generate_pattern
        result = _generate_pattern("Иван", "Петров", "example.com")
        assert result["email"] == "ivan.petrov@example.com"
        assert result["source"] == "pattern"
        assert len(result["email_variants"]) > 1

    def test_generate_pattern_empty(self):
        from leadgen.modules.buster import _generate_pattern
        result = _generate_pattern("", "", "example.com")
        assert result == {}

    def test_no_api_key_uses_pattern(self):
        import asyncio
        from leadgen.modules.buster import find_email
        os.environ.pop("BUSTER_API_KEY", None)
        result = asyncio.get_event_loop().run_until_complete(
            find_email("Иван", "Петров", "example.com")
        )
        assert result.get("source") == "pattern"
        assert "@example.com" in result.get("email", "")


# ══════════════════════════════════════════════════════════════════════════════
# 6. Анализаторы (все 5)
# ══════════════════════════════════════════════════════════════════════════════

SAMPLE_PROFILE = {
    "company": {
        "inn": "7736207543",
        "name": "ООО ТехноСофт",
        "okved": "62.01",
        "okved_name": "Разработка ПО",
        "city": "Москва",
        "director": "Иванов Иван Иванович",
        "founders": [{"name": "Иванов И.И.", "type": "INDIVIDUAL", "inn": "", "share_percent": 100}],
        "management_type": "owner_managed",
        "branch_count": 0,
    },
    "financials": {
        "revenue": 500_000_000,
        "profit": 50_000_000,
        "revenue_trend": "growing",
        "has_bankruptcy": False,
        "arbitration_count": 0,
        "licenses": [],
    },
    "tech": {
        "tech_count": 15,
        "crm": ["amoCRM"],
        "analytics": ["Google Analytics"],
        "maturity_level": "medium",
        "all_technologies": ["WordPress", "Google Analytics", "amoCRM"],
        "has_crm": True,
        "has_analytics": True,
        "security": [],
        "by_category": {},
    },
    "news": [
        {"title": "ТехноСофт привлёк инвестиции", "description": "раунд А", "age_days": 10, "is_fresh": True},
        {"title": "Компания расширяет найм разработчиков", "description": "", "age_days": 20, "is_fresh": True},
    ],
    "contact": {"email": "ivanov@technosoft.ru", "smtp_valid": True},
}


class TestAnalyzers:
    def test_it_maturity_medium(self):
        from leadgen.analyzers import analyze_it_maturity
        result = analyze_it_maturity(SAMPLE_PROFILE)
        assert result["level"] in ("optimization", "basic", "enterprise")
        assert "recommendation" in result
        assert isinstance(result["score_impact"], int)

    def test_it_maturity_enterprise(self):
        from leadgen.analyzers import analyze_it_maturity
        profile = {**SAMPLE_PROFILE, "tech": {**SAMPLE_PROFILE["tech"], "maturity_level": "enterprise", "tech_count": 35}}
        result = analyze_it_maturity(profile)
        assert result["level"] == "enterprise"

    def test_decision_structure_owner(self):
        from leadgen.analyzers import analyze_decision_structure
        result = analyze_decision_structure(SAMPLE_PROFILE)
        assert result["decision_level"] == "owner"
        assert result["lpr_name"] == "Иванов Иван Иванович"

    def test_decision_structure_board(self):
        from leadgen.analyzers import analyze_decision_structure
        profile = {**SAMPLE_PROFILE, "company": {
            **SAMPLE_PROFILE["company"],
            "management_type": "board",
            "founders": [{"name": f"F{i}"} for i in range(5)],
        }}
        result = analyze_decision_structure(profile)
        assert result["decision_level"] == "board"

    def test_vendor_landscape_complement(self):
        from leadgen.analyzers import analyze_vendor_landscape
        result = analyze_vendor_landscape(SAMPLE_PROFILE)
        assert result["strategy"] in ("replace", "integrate", "complement")

    def test_vendor_landscape_replace(self):
        from leadgen.analyzers import analyze_vendor_landscape
        profile = {**SAMPLE_PROFILE, "tech": {
            **SAMPLE_PROFILE["tech"],
            "all_technologies": ["ServiceNow", "Jira Service Management"],
        }}
        result = analyze_vendor_landscape(profile)
        assert result["strategy"] == "replace"

    def test_growth_trajectory_growing(self):
        from leadgen.analyzers import analyze_growth_trajectory
        result = analyze_growth_trajectory(SAMPLE_PROFILE)
        assert result["trajectory"] == "growing"
        assert "sales_argument" in result

    def test_growth_trajectory_declining(self):
        from leadgen.analyzers import analyze_growth_trajectory
        profile = {
            **SAMPLE_PROFILE,
            "financials": {**SAMPLE_PROFILE["financials"], "revenue_trend": "declining"},
            "news": [  # нет роста-сигналов, зато есть сигнал упадка
                {"title": "Компания сокращает сотрудников из-за убытков", "description": "сокращение", "age_days": 5, "is_fresh": True},
            ],
        }
        result = analyze_growth_trajectory(profile)
        assert result["trajectory"] == "declining"

    def test_security_compliance_basic(self):
        from leadgen.analyzers import analyze_security_compliance
        result = analyze_security_compliance(SAMPLE_PROFILE)
        assert result["compliance_level"] in ("basic", "certified", "incident_driven")
        assert "product_recommendation" in result

    def test_security_compliance_regulated(self):
        from leadgen.analyzers import analyze_security_compliance
        profile = {**SAMPLE_PROFILE, "company": {**SAMPLE_PROFILE["company"], "okved": "64.19"}}
        result = analyze_security_compliance(profile)
        assert result["is_regulated_industry"] is True
        assert result["compliance_level"] == "certified"

    def test_compute_profile_analyses_structure(self):
        from leadgen.analyzers import compute_profile_analyses
        result = compute_profile_analyses(SAMPLE_PROFILE)
        assert "it_maturity" in result
        assert "decision_structure" in result
        assert "vendor_landscape" in result
        assert "growth_trajectory" in result
        assert "security_compliance" in result
        assert isinstance(result["profile_score_impact"], int)
        assert 0 <= result["profile_score_impact"] <= 40

    def test_compute_profile_analyses_score_bounded(self):
        from leadgen.analyzers import compute_profile_analyses
        result = compute_profile_analyses(SAMPLE_PROFILE)
        assert result["profile_score_impact"] <= 40


# ══════════════════════════════════════════════════════════════════════════════
# 7. Pipeline helpers
# ══════════════════════════════════════════════════════════════════════════════

class TestPipelineHelpers:
    def test_extract_domain(self):
        from leadgen.pipeline import _extract_domain
        assert _extract_domain("https://www.example.com/path") == "example.com"
        assert _extract_domain("http://test.ru") == "test.ru"
        assert _extract_domain("") == ""

    def test_fmt_money(self):
        from leadgen.pipeline import _fmt_money
        assert "млрд" in _fmt_money(1_500_000_000)
        assert "млн" in _fmt_money(50_000_000)
        assert "₽" in _fmt_money(500_000)
        assert _fmt_money(None) == "—"

    def test_parse_json_safe_valid(self):
        from leadgen.pipeline import _parse_json_safe
        result = _parse_json_safe('{"score": 75, "verdict": "safe"}')
        assert result["score"] == 75

    def test_parse_json_safe_with_wrapping(self):
        from leadgen.pipeline import _parse_json_safe
        result = _parse_json_safe('Some text {"score": 42} more text')
        assert result["score"] == 42

    def test_parse_json_safe_invalid(self):
        from leadgen.pipeline import _parse_json_safe
        result = _parse_json_safe("not json at all")
        assert result.get("_parse_error") is True

    def test_compute_final_score_bounds(self):
        from leadgen.pipeline import _compute_final_score
        from leadgen.analyzers import compute_profile_analyses
        analyses = compute_profile_analyses(SAMPLE_PROFILE)
        agents = {
            "analyst": {"score": 80},
            "tech_specialist": {"score": 70},
            "marketer": {"score": 75},
            "strategist": {"score": 85},
        }
        score = _compute_final_score(analyses, agents)
        assert 5 <= score <= 99

    def test_compute_final_score_high(self):
        from leadgen.pipeline import _compute_final_score
        analyses = {"profile_score_impact": 40}
        agents = {k: {"score": 95} for k in ["analyst", "tech_specialist", "marketer", "strategist"]}
        score = _compute_final_score(analyses, agents)
        assert score >= 70

    def test_build_lead_card_structure(self):
        from leadgen.pipeline import _build_lead_card, _compute_final_score
        from leadgen.analyzers import compute_profile_analyses
        analyses = compute_profile_analyses(SAMPLE_PROFILE)
        agents = {
            "analyst": {"score": 75, "summary": "ok", "risks": []},
            "tech_specialist": {"score": 70, "recommended_products": ["OpManager"]},
            "marketer": {"score": 80, "hook": "Тест крючок", "urgency": "week", "triggers": []},
            "strategist": {"score": 85, "script_outline": ["Привет", "Предложение"]},
        }
        score = _compute_final_score(analyses, agents)
        card = _build_lead_card(SAMPLE_PROFILE["company"], SAMPLE_PROFILE, analyses, agents, score)
        # Обязательные поля
        assert card["inn"] == "7736207543"
        assert card["company_name"] == "ООО ТехноСофт"
        assert "lpr" in card
        assert card["lpr"]["name"] == "Иванов Иван Иванович"
        assert "financials" in card
        assert "tech_stack" in card
        assert "analyses" in card
        assert "agent_scores" in card
        assert 5 <= card["final_score"] <= 99
        assert card["priority"] in ("critical", "high", "medium", "low")
        assert card["action"] in ("call_now", "schedule_call", "research_more", "monitor")

    def test_lead_card_lpr_email(self):
        from leadgen.pipeline import _build_lead_card, _compute_final_score
        from leadgen.analyzers import compute_profile_analyses
        analyses = compute_profile_analyses(SAMPLE_PROFILE)
        agents = {"analyst": {"score": 70}, "tech_specialist": {"score": 70},
                  "marketer": {"score": 70}, "strategist": {"score": 70}}
        score = _compute_final_score(analyses, agents)
        card = _build_lead_card(SAMPLE_PROFILE["company"], SAMPLE_PROFILE, analyses, agents, score)
        assert card["lpr"]["email"] == "ivanov@technosoft.ru"
        assert card["lpr"]["email_valid"] is True


class TestPortraitMatching:
    def test_match_portrait_with_core_fields(self):
        from leadgen.pipeline import _match_portrait
        company = {
            "status": "ACTIVE",
            "city": "Москва",
            "okved": "62.01",
            "revenue": 200_000_000,
            "_contracts_count": 3,
        }
        criteria = {
            "city": "Москва",
            "okved": "62",
            "revenue_min": 100_000_000,
            "must_have_gov_contracts": True,
        }
        score, matched, missed = _match_portrait(company, criteria)
        assert score > 0.6
        assert "active" in matched
        assert "city" in matched
        assert "okved" in matched
        assert "revenue" in matched
        assert "gov_contracts" in matched
        assert "bankruptcy_risk" not in missed

    def test_match_portrait_employees_unknown_is_neutral(self):
        from leadgen.pipeline import _match_portrait
        company = {
            "status": "ACTIVE",
            "city": "Москва",
            "okved": "62.01",
            "employees_count": None,
        }
        criteria = {
            "city": "Москва",
            "okved": "62",
            "employees_min": 50,
            "employees_max": 500,
        }
        score, matched, missed = _match_portrait(company, criteria)
        assert score > 0.4
        assert "employees_unknown" in missed


class TestPortraitWebFill:
    def test_extract_employees_from_text(self):
        from leadgen.pipeline import _extract_employees_from_text
        text = "По данным за год, численность сотрудников: 125 человек."
        assert _extract_employees_from_text(text) == 125

    def test_extract_revenue_from_text(self):
        from leadgen.pipeline import _extract_revenue_from_text
        text = "Revenue 1.5 billion in 2024."
        val = _extract_revenue_from_text(text)
        assert val is not None
        assert val >= 1_500_000_000


class TestPortraitReference:
    def test_merge_criteria_with_reference(self):
        from leadgen.pipeline import _merge_criteria_with_reference
        criteria = {"query": "", "okved": "", "city": "", "revenue_min": None}
        ref = {"name_short": "ООО Тест", "okved": "62.01", "city": "Москва", "revenue": 400_000_000}
        merged = _merge_criteria_with_reference(criteria, ref)
        assert merged["okved"] == "62"
        assert merged["city"] == "Москва"
        assert merged["revenue_min"] == 200_000_000
        assert "Тест" in merged["query"]

    def test_score_reference_similarity(self):
        from leadgen.pipeline import _score_reference_similarity
        company = {"okved": "62.02", "city": "Москва", "revenue": 420_000_000, "_contracts_count": 5}
        ref = {"okved": "62.01", "city": "Москва", "revenue": 400_000_000, "_contracts_count": 2}
        bonus, matched = _score_reference_similarity(company, ref)
        assert bonus > 0.3
        assert "similar_okved" in matched
        assert "similar_city" in matched
        assert "similar_revenue" in matched


# ══════════════════════════════════════════════════════════════════════════════
# 8. API config helpers
# ══════════════════════════════════════════════════════════════════════════════

class TestAPIConfig:
    def test_load_config_defaults(self, tmp_path, monkeypatch):
        import leadgen.pipeline as pl_mod
        import api.routes.leadgen as lg_mod
        monkeypatch.setattr(lg_mod, "CONFIG_PATH", str(tmp_path / "cfg.json"))
        cfg = lg_mod._load_config()
        assert "score_threshold_crm" in cfg
        assert "news_max_age_days" in cfg
        assert isinstance(cfg["portrait_intents"], list)

    def test_save_and_reload_config(self, tmp_path, monkeypatch):
        import api.routes.leadgen as lg_mod
        path = str(tmp_path / "cfg.json")
        monkeypatch.setattr(lg_mod, "CONFIG_PATH", path)
        cfg = lg_mod._load_config()
        cfg["score_threshold_crm"] = 55
        lg_mod._save_config(cfg)
        reloaded = lg_mod._load_config()
        assert reloaded["score_threshold_crm"] == 55


# ══════════════════════════════════════════════════════════════════════════════
# 9. Pipeline интеграция (мок)
# ══════════════════════════════════════════════════════════════════════════════

class TestPipelineIntegration:
    def test_run_pipeline_with_mock(self):
        """Полный прогон pipeline с заглушками всех модулей."""
        import asyncio
        from unittest.mock import AsyncMock, patch, MagicMock

        mock_company = SAMPLE_PROFILE["company"].copy()
        mock_fin = SAMPLE_PROFILE["financials"].copy()

        async def run():
            with patch("leadgen.modules.checko.fetch_company", new=AsyncMock(return_value=mock_company)), \
                 patch("leadgen.modules.checko.fetch_full_profile", new=AsyncMock(return_value=mock_fin)), \
                 patch("leadgen.modules.checko._available", return_value=True), \
                 patch("leadgen.modules.builtwith.fetch_tech_stack", new=AsyncMock(return_value=SAMPLE_PROFILE["tech"])), \
                 patch("leadgen.modules.newsapi.fetch_news", new=AsyncMock(return_value=SAMPLE_PROFILE["news"])), \
                 patch("leadgen.modules.buster.find_email", new=AsyncMock(return_value=SAMPLE_PROFILE["contact"])), \
                 patch("rag.search.free_search", new=AsyncMock(return_value={"formatted_block": ""})), \
                 patch("core.llm.chat", new=AsyncMock(return_value='{"score":75,"summary":"ok","hook":"test","script_outline":["Hello"],"triggers":[]}')):
                from leadgen.pipeline import run_pipeline
                return await run_pipeline(inn="7736207543")

        result = asyncio.get_event_loop().run_until_complete(run())
        assert result["status"] == "ok"
        assert result["inn"] == "7736207543"
        assert "final_score" in result
        assert 5 <= result["final_score"] <= 99
        assert "lpr" in result
        assert "analyses" in result

    def test_run_pipeline_no_inn_no_name(self):
        """Pipeline без ИНН и имени — возвращает минимальный профиль."""
        import asyncio
        from unittest.mock import AsyncMock, patch

        async def run():
            with patch("rag.search.free_search", new=AsyncMock(return_value={})), \
                 patch("core.llm.chat", new=AsyncMock(return_value='{"score":50,"summary":"ok"}')):
                from leadgen.pipeline import run_pipeline
                return await run_pipeline()

        result = asyncio.get_event_loop().run_until_complete(run())
        assert result["status"] == "ok"


# ══════════════════════════════════════════════════════════════════════════════
# 10. Hermes — новые интенты
# ══════════════════════════════════════════════════════════════════════════════

class TestHermesLeadgenIntents:
    def test_generate_lead_in_prompt(self):
        from core.hermes import SYSTEM_PROMPT
        assert "generate_lead" in SYSTEM_PROMPT

    def test_find_leads_portrait_in_prompt(self):
        from core.hermes import SYSTEM_PROMPT
        assert "find_leads_portrait" in SYSTEM_PROMPT

    def test_cluster_company_in_prompt(self):
        from core.hermes import SYSTEM_PROMPT
        assert "cluster_company" in SYSTEM_PROMPT

    def test_leadgen_examples_in_prompt(self):
        from core.hermes import SYSTEM_PROMPT
        assert "ИНН" in SYSTEM_PROMPT or "ЛИДОГЕНЕРАЦИЯ" in SYSTEM_PROMPT


# ══════════════════════════════════════════════════════════════════════════════
# 11. Оркестратор — leadgen интенты
# ══════════════════════════════════════════════════════════════════════════════

class TestOrchestratorLeadgen:
    def test_generate_lead_in_agent_intents(self):
        from agents.orchestrator import _AGENT_INTENTS
        assert "generate_lead" in _AGENT_INTENTS

    def test_find_leads_portrait_in_agent_intents(self):
        from agents.orchestrator import _AGENT_INTENTS
        assert "find_leads_portrait" in _AGENT_INTENTS

    def test_cluster_company_in_agent_intents(self):
        from agents.orchestrator import _AGENT_INTENTS
        assert "cluster_company" in _AGENT_INTENTS

    def test_intent_to_agents_mapping(self):
        from agents.orchestrator import _INTENT_TO_AGENTS
        assert "generate_lead" in _INTENT_TO_AGENTS
        assert "analyst" in _INTENT_TO_AGENTS["generate_lead"]

    def test_run_agents_noop_for_unknown(self):
        import asyncio
        from agents.orchestrator import run_agents
        result = asyncio.get_event_loop().run_until_complete(
            run_agents("unknown_intent", {}, "test")
        )
        assert result["agents_ran"] is False


# ══════════════════════════════════════════════════════════════════════════════
# 12. Checko — парсинг данных
# ══════════════════════════════════════════════════════════════════════════════

class TestChecko:
    def test_map_status_int(self):
        from leadgen.modules.checko import _parse_status
        # Словарь-формат: {"Наим": "Действует"}
        assert _parse_status({"Наим": "Действует"}) == "ACTIVE"
        assert _parse_status({"Код": "001"}) == "ACTIVE"

    def test_map_status_string(self):
        from leadgen.modules.checko import _parse_status
        assert _parse_status("ACTIVE") == "ACTIVE"
        assert _parse_status("BANKRUPT") == "BANKRUPT"
        assert _parse_status("REORGANIZING") == "REORGANIZING"
        assert _parse_status("") == "ACTIVE"
        assert _parse_status(None) == "ACTIVE"
        # Реальные значения из API
        assert _parse_status({"Наим": "Действует"}) == "ACTIVE"

    def test_parse_finances_dict_format(self):
        from leadgen.modules.checko import _parse_finances
        # Реальный формат Checko: код строки РСБУ как ключ
        data = {
            "2022": {"2110": 100_000_000, "2400": 5_000_000},
            "2023": {"2110": 130_000_000, "2400": 8_000_000},
        }
        result = _parse_finances(data)
        assert result["revenue"] == 130_000_000
        assert result["profit"] == 8_000_000
        assert result["revenue_trend"] == "growing"
        assert result["finance_year"] == 2023

    def test_parse_finances_list_format(self):
        from leadgen.modules.checko import _parse_finances
        data = [
            {"year": 2022, "revenue": 200_000_000},
            {"year": 2023, "revenue": 160_000_000},
        ]
        result = _parse_finances(data)
        assert result["revenue"] == 160_000_000
        assert result["revenue_trend"] == "declining"

    def test_parse_finances_stable(self):
        from leadgen.modules.checko import _parse_finances
        data = {"2022": {"2110": 100_000_000}, "2023": {"2110": 103_000_000}}
        result = _parse_finances(data)
        assert result["revenue_trend"] == "stable"

    def test_parse_finances_empty(self):
        from leadgen.modules.checko import _parse_finances
        result = _parse_finances({})
        assert result["revenue"] is None
        assert result["revenue_trend"] == "unknown"

    def test_parse_company_minimal(self):
        from leadgen.modules.checko import _parse_company
        # Реальная структура Checko API
        d = {
            "ИНН": "7736207543",
            "ОГРН": "1027700132380",
            "НаимПолн": "ООО МангоТелеком",
            "Статус": {"Наим": "Действует"},
            "ЮрАдрес": {"АдресРФ": "119021, г. Москва, ул. Льва Толстого, д. 16", "НасПункт": "г. Москва"},
            "Руковод": [{"ФИО": "Иванов Иван Иванович", "НаимДолжн": "Генеральный директор", "ОгрДоступ": False}],
            "ОКВЭД": {"Код": "61.10", "Наим": "Деятельность в области связи"},
        }
        result = _parse_company(d)
        assert result is not None
        assert result["inn"] == "7736207543"
        assert result["status"] == "ACTIVE"
        assert result["director"] == "Иванов Иван Иванович"
        assert result["city"] == "Москва"
        assert result["_source"] == "checko"

    def test_parse_company_nested_director(self):
        from leadgen.modules.checko import _parse_company
        # Checko возвращает Руковод[].ФИО как строку
        d = {
            "ИНН": "1234567890",
            "НаимПолн": "ООО Тест",
            "Руковод": [
                {
                    "ФИО": "Петров Пётр Петрович",
                    "НаимДолжн": "Директор",
                    "ОгрДоступ": False,
                }
            ]
        }
        result = _parse_company(d)
        assert result["director"] == "Петров Пётр Петрович"
        assert result["director_post"] == "Директор"

    def test_parse_company_empty(self):
        from leadgen.modules.checko import _parse_company
        result = _parse_company({})
        assert result is None or result.get("inn") == ""

    def test_extract_contacts_list(self):
        # Контакты теперь разбираются внутри _parse_company через Тел/Эмейл
        from leadgen.modules.checko import _parse_company
        d = {
            "ИНН": "9999999999",
            "Контакты": {
                "Тел": ["+7 495 123-45-67", "+7 495 987-65-43"],
                "Эмейл": [],
            }
        }
        result = _parse_company(d)
        assert result is not None
        assert "+7 495 123-45-67" in result["dadata_phones"]

    def test_extract_contacts_string(self):
        from leadgen.modules.checko import _parse_company
        d = {
            "ИНН": "9999999998",
            "Контакты": {"Тел": [], "Эмейл": ["test@example.com"]},
        }
        result = _parse_company(d)
        assert result is not None
        assert "test@example.com" in result["dadata_emails"]

    def test_num_helper(self):
        from leadgen.modules.checko import _num
        assert _num("1 234 567") == 1_234_567.0
        assert _num(None) is None
        assert _num("abc") is None
        assert _num(100_000) == 100_000.0

    def test_parse_founders(self):
        # Учредители ФЛ разбираются внутри _parse_company через Учред.ФЛ
        from leadgen.modules.checko import _parse_company
        d = {
            "ИНН": "8888888888",
            "Учред": {
                "ФЛ": [
                    {
                        "ФИО": "Сидоров Сидор Сидорович",
                        "ИНН": "123456789012",
                        "Доля": {"Процент": 50},
                    }
                ],
                "РосОрг": [],
                "ИнОрг": [],
            }
        }
        result = _parse_company(d)
        assert result is not None
        founders = result["founders"]
        assert len(founders) == 1
        assert founders[0]["inn"] == "123456789012"
        assert founders[0]["type"] == "INDIVIDUAL"

    def test_not_available_without_key(self):
        import os
        from leadgen.modules.checko import _available
        old = os.environ.pop("CHECKO_API_KEY", None)
        try:
            assert not _available()
        finally:
            if old:
                os.environ["CHECKO_API_KEY"] = old
