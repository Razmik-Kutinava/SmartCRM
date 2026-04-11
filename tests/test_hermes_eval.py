"""
Eval-тесты Hermes: проверяем, что роутер правильно распознаёт intent и slots
из текстовых команд (cases.jsonl).

Запуск: pytest tests/test_hermes_eval.py -v
Для быстрого smoke без реального API: pytest tests/test_hermes_eval.py -v -k "create or update or delete"
"""
import json
import re
import os
import pytest
from pathlib import Path

CASES_PATH = Path(__file__).parent.parent / "eval" / "cases.jsonl"


def load_cases():
    cases = []
    with open(CASES_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def norm(s: str) -> str:
    """Нормализация для нечёткого сравнения слотов."""
    s = str(s).lower()
    s = re.sub(r'[«»\u201c\u201d\u201e"\'\`+\-()№\s]', "", s)
    s = s.replace("ё", "е")
    return s


def slots_match(expected: dict, actual: dict) -> tuple[bool, str]:
    """
    Проверяет, что каждый ключ expected содержится в actual.
    Сравнение нечёткое: проверяем вхождение norm(expected_v) в norm(actual_v).
    """
    for key, exp_val in expected.items():
        act_val = actual.get(key, "")
        if not act_val:
            return False, f"слот '{key}' отсутствует в ответе"
        en = norm(str(exp_val))
        an = norm(str(act_val))
        if en not in an and an not in en:
            return False, f"слот '{key}': ожидалось '{exp_val}', получено '{act_val}'"
    return True, ""


# ── Юнит-тест парсера (без реального LLM) ──────────────────────────

class TestHermesParser:
    """Проверяем вспомогательные утилиты — работают без сетевых вызовов."""

    def test_cases_file_exists(self):
        assert CASES_PATH.exists(), f"Не найден файл {CASES_PATH}"

    def test_cases_have_required_fields(self):
        for case in load_cases():
            assert "id" in case, f"Нет поля id: {case}"
            assert "text" in case, f"Нет поля text: {case}"
            assert "expected_intent" in case, f"Нет expected_intent: {case}"
            assert "expected_slots" in case, f"Нет expected_slots: {case}"

    def test_norm_strips_noise(self):
        assert norm("ООО «Ромашка»") == norm("ООО Ромашка")
        assert norm("+7 916 111-22-33") == norm("79161112233")

    def test_slots_match_exact(self):
        ok, _ = slots_match({"company": "ромашка"}, {"company": "ООО Ромашка"})
        assert ok

    def test_slots_match_missing_key(self):
        ok, msg = slots_match({"email": "test@test.ru"}, {"company": "АКМЕ"})
        assert not ok
        assert "email" in msg


# ── Интеграционные тесты Hermes (требуют запущенного сервера) ───────
# Пропускаются автоматически, если GROQ_API_KEY не задан или сервер недоступен.

HERMES_AVAILABLE = bool(os.getenv("GROQ_API_KEY") or os.getenv("OLLAMA_HOST"))

@pytest.mark.skipif(not HERMES_AVAILABLE, reason="GROQ/Ollama недоступны — пропускаем интеграционные тесты Hermes")
class TestHermesIntents:

    @pytest.fixture(scope="class")
    def hermes(self):
        from core.hermes import parse_intent
        return parse_intent

    @pytest.mark.parametrize("case", [c for c in load_cases() if c.get("expected_intent") == "create_lead"])
    @pytest.mark.asyncio
    async def test_create_lead_intents(self, hermes, case):
        result = await hermes(case["text"])
        assert result["intent"] == "create_lead", (
            f"[{case['id']}] '{case['text']}' → intent='{result['intent']}', ожидалось 'create_lead'"
        )
        ok, msg = slots_match(case["expected_slots"], result.get("slots", {}))
        assert ok, f"[{case['id']}] {msg}"

    @pytest.mark.parametrize("case", [c for c in load_cases() if c.get("expected_intent") == "update_lead"])
    @pytest.mark.asyncio
    async def test_update_lead_intents(self, hermes, case):
        result = await hermes(case["text"])
        assert result["intent"] == "update_lead", (
            f"[{case['id']}] '{case['text']}' → intent='{result['intent']}', ожидалось 'update_lead'"
        )
        ok, msg = slots_match(case["expected_slots"], result.get("slots", {}))
        assert ok, f"[{case['id']}] {msg}"

    @pytest.mark.parametrize("case", [c for c in load_cases() if c.get("expected_intent") == "noop"])
    @pytest.mark.asyncio
    async def test_noop_intents(self, hermes, case):
        result = await hermes(case["text"])
        assert result["intent"] == "noop", (
            f"[{case['id']}] '{case['text']}' → intent='{result['intent']}', ожидалось 'noop'"
        )
