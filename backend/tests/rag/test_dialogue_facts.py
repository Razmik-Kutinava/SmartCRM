"""Тесты извлечения фактов из диалога агента."""

from rag.dialogue_facts import (
    dialogue_to_rag_text,
    extract_deal_facts,
    ingest_dialogue_facts,
    is_dialogue_eligible,
)


def test_extract_deal_facts_bant_and_summary():
    output = {
        "summary": "Клиент готов к пилоту на 2 недели, бюджет согласован.",
        "score": 78,
        "bant": {"budget": "800000 RUB approved", "authority": "директор IT отдела"},
        "next_action": "Позвонить в понедельник до 12:00",
    }
    facts = extract_deal_facts(output)
    assert len(facts) >= 3
    assert is_dialogue_eligible(facts)


def test_extract_skips_empty():
    assert extract_deal_facts(None) == []
    assert extract_deal_facts({"summary": "коротко"}) == []


def test_dialogue_to_rag_text_format():
    text = dialogue_to_rag_text(
        "проанализируй лид",
        ["summary: Длинный факт о сделке", "score: 70/100"],
        company="ООО Ромашка",
        agent_id="analyst",
    )
    assert "Вопрос:" in text
    assert "ООО Ромашка" in text
    assert "dialogue/analyst" in text


def test_ingest_dialogue_dry_run_eligible(monkeypatch):
    monkeypatch.setenv("RAG_DIALOGUE_MIN_FACTS", "2")

    def fake_ingest(*_a, **_k):
        return {"chunks": 2, "chunk_previews": [{"text": "x"}]}

    monkeypatch.setattr("rag.dialogue_facts.ingest_manual_text", fake_ingest)
    out = ingest_dialogue_facts(
        "analyst",
        {
            "summary": "Сильный интерес к интеграции CRM с 1С.",
            "decision": "Перевести на этап переговоры с ЛПР.",
        },
        transcript="анализ",
        slots={"company": "АКМЕ", "lead_id": 7},
        dry_run=True,
    )
    assert out["eligible"] is True
    assert out["facts_count"] >= 2
    assert out["chunks"] == 2


def test_ingest_not_eligible_with_one_fact(monkeypatch):
    monkeypatch.setenv("RAG_DIALOGUE_MIN_FACTS", "2")
    out = ingest_dialogue_facts(
        "analyst",
        {"summary": "Единственный длинный факт о компании и сделке."},
        dry_run=True,
    )
    assert out["eligible"] is False
    assert out["ingested"] == 0
