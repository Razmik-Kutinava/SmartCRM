"""Генерация eval/agents/*.jsonl — ≥15 кейсов на агента."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.agent_eval.cases import AGENTS_DIR, AGENT_IDS  # noqa: E402

_NO_HALL = ["как языковая модель", "не имею доступа", "галлюцина"]

_CASES: dict[str, list[dict]] = {
    "analyst": [
        {"id": "analyst-001", "intent": "create_lead", "slots": {"company": "ООО Ромашка", "industry": "ритейл", "city": "Москва", "budget": "500000"}, "must_contain": ["score", "bant"], "must_not_contain": _NO_HALL, "notes": "Новый лид с бюджетом"},
        {"id": "analyst-002", "intent": "create_lead", "slots": {"company": "СеверСтрой", "contact": "Иван", "phone": "79161234567", "industry": "строительство"}, "must_contain": ["score", "next"], "must_not_contain": _NO_HALL, "notes": "Новый лид стройка"},
        {"id": "analyst-003", "intent": "create_lead", "slots": {"company": "ТехноПарк", "industry": "IT", "budget": "2000000", "stage": "переговоры"}, "must_contain": ["score", "risk"], "must_not_contain": _NO_HALL, "notes": "IT с крупным бюджетом"},
        {"id": "analyst-004", "intent": "list_leads", "slots": {"filter": "hot"}, "must_contain": ["лид"], "must_not_contain": _NO_HALL, "notes": "Сводка лидов"},
        {"id": "analyst-005", "intent": "create_lead", "slots": {"company": "АгроСоюз", "industry": "сельхоз", "city": "Краснодар"}, "must_contain": ["score", "industry"], "must_not_contain": _NO_HALL, "notes": "Агро без бюджета"},
        {"id": "analyst-006", "intent": "create_lead", "slots": {"company": "МедЛайн", "industry": "медицина", "email": "sales@medline.ru"}, "must_contain": ["score", "bant"], "must_not_contain": _NO_HALL, "notes": "Медицина email"},
        {"id": "analyst-007", "intent": "create_lead", "slots": {"company": "ФинГрупп", "industry": "финансы", "budget": "10000000"}, "must_contain": ["score", "budget"], "must_not_contain": _NO_HALL, "notes": "Финансы enterprise"},
        {"id": "analyst-008", "intent": "create_lead", "slots": {"company": "ЛогистикПро", "industry": "логистика", "stage": "новый"}, "must_contain": ["score", "next"], "must_not_contain": _NO_HALL, "notes": "Логистика холодный"},
        {"id": "analyst-009", "intent": "create_lead", "slots": {"company": "Кафе Уют", "industry": "общепит", "city": "СПб", "budget": "150000"}, "must_contain": ["score", "bant"], "must_not_contain": _NO_HALL, "notes": "Малый бизнес общепит"},
        {"id": "analyst-010", "intent": "create_lead", "slots": {"company": "АвтоДилер", "industry": "авто", "budget": "3000000"}, "must_contain": ["score", "risk"], "must_not_contain": _NO_HALL, "notes": "Автодилер"},
        {"id": "analyst-011", "intent": "list_leads", "slots": {"filter": "new"}, "must_contain": ["лид"], "must_not_contain": _NO_HALL, "notes": "Новые лиды"},
        {"id": "analyst-012", "intent": "create_lead", "slots": {"company": "ЭнергоСбыт", "industry": "энергетика", "employees": "500"}, "must_contain": ["score", "industry"], "must_not_contain": _NO_HALL, "notes": "Крупная энергетика"},
        {"id": "analyst-013", "intent": "create_lead", "slots": {"company": "СтартАп Лаб", "industry": "IT", "contact": "Анна"}, "must_contain": ["score", "next"], "must_not_contain": _NO_HALL, "notes": "Стартап"},
        {"id": "analyst-014", "intent": "create_lead", "slots": {"company": "МашПром", "industry": "производство", "city": "Екатеринбург"}, "must_contain": ["score", "bant"], "must_not_contain": _NO_HALL, "notes": "Производство"},
        {"id": "analyst-015", "intent": "create_lead", "slots": {"company": "Вектор", "industry": "ритейл", "stage": "квалификация", "note": "интерес к CRM"}, "must_contain": ["score", "need"], "must_not_contain": _NO_HALL, "notes": "Квалификация с заметкой"},
    ],
    "economist": [
        {"id": "economist-001", "intent": "analyze_lead", "slots": {"company": "Ромашка", "budget": "800000", "industry": "ритейл"}, "must_contain": ["бюджет", "deal"], "must_not_contain": _NO_HALL, "notes": "Бюджет заявлен"},
        {"id": "economist-002", "intent": "create_lead", "slots": {"company": "Север", "industry": "строительство"}, "must_contain": ["бюджет", "сегмент"], "must_not_contain": _NO_HALL, "notes": "Без бюджета — оценка"},
        {"id": "economist-003", "intent": "analyze_lead", "slots": {"company": "ТехноПарк", "budget": "5000000", "industry": "IT"}, "must_contain": ["ltv", "вероятност"], "must_not_contain": _NO_HALL, "notes": "Крупная сделка IT"},
        {"id": "economist-004", "intent": "analyze_lead", "slots": {"company": "Кафе Уют", "budget": "100000", "industry": "общепит"}, "must_contain": ["smb", "бюджет"], "must_not_contain": _NO_HALL, "notes": "SMB общепит"},
        {"id": "economist-005", "intent": "list_leads", "slots": {}, "must_contain": ["финансов", "анализ"], "must_not_contain": _NO_HALL, "notes": "Не требует анализа"},
        {"id": "economist-006", "intent": "analyze_lead", "slots": {"company": "ФинГрупп", "budget": "15000000", "industry": "финансы"}, "must_contain": ["enterprise", "риск"], "must_not_contain": _NO_HALL, "notes": "Enterprise финансы"},
        {"id": "economist-007", "intent": "analyze_lead", "slots": {"company": "АгроСоюз", "industry": "сельхоз", "budget": "600000"}, "must_contain": ["бюджет", "цен"], "must_not_contain": _NO_HALL, "notes": "Агро средний"},
        {"id": "economist-008", "intent": "create_lead", "slots": {"company": "МедЛайн", "budget": "2 млн руб", "industry": "медицина"}, "must_contain": ["бюджет", "ltv"], "must_not_contain": _NO_HALL, "notes": "Бюджет текстом"},
        {"id": "economist-009", "intent": "analyze_lead", "slots": {"company": "ЛогистикПро", "budget": "—", "industry": "логистика"}, "must_contain": ["оценк", "бюджет"], "must_not_contain": _NO_HALL, "notes": "Бюджет не указан"},
        {"id": "economist-010", "intent": "analyze_lead", "slots": {"company": "АвтоДилер", "budget": "4000000", "stage": "переговоры"}, "must_contain": ["вероятност", "цен"], "must_not_contain": _NO_HALL, "notes": "Переговоры авто"},
        {"id": "economist-011", "intent": "analyze_lead", "slots": {"company": "ЭнергоСбыт", "employees": "500", "budget": "8000000"}, "must_contain": ["mid_market", "бюджет"], "must_not_contain": _NO_HALL, "notes": "Mid market"},
        {"id": "economist-012", "intent": "create_lead", "slots": {"company": "СтартАп Лаб", "budget": "300000", "industry": "IT"}, "must_contain": ["smb", "дисконт"], "must_not_contain": _NO_HALL, "notes": "Стартап бюджет"},
        {"id": "economist-013", "intent": "analyze_lead", "slots": {"company": "МашПром", "industry": "производство", "budget": "1200000"}, "must_contain": ["бюджет", "риск"], "must_not_contain": _NO_HALL, "notes": "Производство"},
        {"id": "economist-014", "intent": "analyze_lead", "slots": {"company": "Вектор", "budget": "250000", "instruction": "оценить маржу"}, "must_contain": ["бюджет", "summary"], "must_not_contain": _NO_HALL, "notes": "С инструкцией"},
        {"id": "economist-015", "intent": "analyze_lead", "slots": {"company": "ООО Гамма", "budget": "1.5 млн", "city": "Казань"}, "must_contain": ["бюджет", "сегмент"], "must_not_contain": _NO_HALL, "notes": "Бюджет с городом"},
    ],
    "marketer": [
        {"id": "marketer-001", "intent": "write_email", "slots": {"company": "Ромашка", "topic": "CRM", "tone": "деловой", "industry": "ритейл"}, "must_contain": ["subject", "ромаш"], "must_not_contain": _NO_HALL, "notes": "Письмо ритейл"},
        {"id": "marketer-002", "intent": "create_lead", "slots": {"company": "СеверСтрой", "industry": "строительство", "contact": "Пётр"}, "must_contain": ["buyer", "касан"], "must_not_contain": _NO_HALL, "notes": "ABM стройка"},
        {"id": "marketer-003", "intent": "analyze_lead", "slots": {"company": "ТехноПарк", "industry": "IT"}, "must_contain": ["value", "touch"], "must_not_contain": _NO_HALL, "notes": "IT персонализация"},
        {"id": "marketer-004", "intent": "write_email", "slots": {"company": "МедЛайн", "topic": "автоматизация", "industry": "медицина"}, "must_contain": ["subject", "мед"], "must_not_contain": _NO_HALL, "notes": "Медицина email"},
        {"id": "marketer-005", "intent": "create_lead", "slots": {"company": "Кафе Уют", "industry": "общепит"}, "must_contain": ["buyer", "email"], "must_not_contain": _NO_HALL, "notes": "Малый бизнес"},
        {"id": "marketer-006", "intent": "write_email", "slots": {"company": "ФинГрупп", "topic": "интеграция", "tone": "формальный"}, "must_contain": ["subject", "фин"], "must_not_contain": _NO_HALL, "notes": "Финансы формально"},
        {"id": "marketer-007", "intent": "analyze_lead", "slots": {"company": "АгроСоюз", "industry": "сельхоз"}, "must_contain": ["touch", "value"], "must_not_contain": _NO_HALL, "notes": "Агро ABM"},
        {"id": "marketer-008", "intent": "write_email", "slots": {"company": "ЛогистикПро", "topic": "скорость внедрения"}, "must_contain": ["subject", "логист"], "must_not_contain": _NO_HALL, "notes": "Логистика"},
        {"id": "marketer-009", "intent": "create_lead", "slots": {"company": "АвтоДилер", "industry": "авто", "contact": "Олег"}, "must_contain": ["buyer", "касан"], "must_not_contain": _NO_HALL, "notes": "Авто дилер"},
        {"id": "marketer-010", "intent": "write_email", "slots": {"company": "ЭнергоСбыт", "topic": "отчётность"}, "must_contain": ["subject", "энерг"], "must_not_contain": _NO_HALL, "notes": "Энергетика"},
        {"id": "marketer-011", "intent": "analyze_lead", "slots": {"company": "СтартАп Лаб", "industry": "IT"}, "must_contain": ["touch", "hook"], "must_not_contain": _NO_HALL, "notes": "Стартап"},
        {"id": "marketer-012", "intent": "write_email", "slots": {"company": "МашПром", "topic": "производство", "tone": "деловой"}, "must_contain": ["subject", "маш"], "must_not_contain": _NO_HALL, "notes": "Производство"},
        {"id": "marketer-013", "intent": "create_lead", "slots": {"company": "Вектор", "industry": "ритейл", "note": "интерес к CRM"}, "must_contain": ["buyer", "value"], "must_not_contain": _NO_HALL, "notes": "Ритейл заметка"},
        {"id": "marketer-014", "intent": "write_email", "slots": {"company": "АКМЕ", "topic": "тендер", "tone": "срочный"}, "must_contain": ["subject", "акме"], "must_not_contain": _NO_HALL, "notes": "Тендер срочно"},
        {"id": "marketer-015", "intent": "analyze_lead", "slots": {"company": "Гамма", "industry": "e-commerce"}, "must_contain": ["touch", "buyer"], "must_not_contain": _NO_HALL, "notes": "E-commerce"},
    ],
    "tech_specialist": [
        {"id": "tech-001", "intent": "analyze_lead", "slots": {"company": "Ромашка", "industry": "ритейл"}, "must_contain": ["stack", "интеграц"], "must_not_contain": _NO_HALL, "notes": "Ритейл стек"},
        {"id": "tech-002", "intent": "create_lead", "slots": {"company": "СеверСтрой", "industry": "строительство"}, "must_contain": ["it_maturity", "риск"], "must_not_contain": _NO_HALL, "notes": "Стройка legacy"},
        {"id": "tech-003", "intent": "analyze_lead", "slots": {"company": "ТехноПарк", "industry": "IT"}, "must_contain": ["api", "advanced"], "must_not_contain": _NO_HALL, "notes": "IT компания"},
        {"id": "tech-004", "intent": "analyze_lead", "slots": {"company": "МедЛайн", "industry": "медицина"}, "must_contain": ["интеграц", "вопрос"], "must_not_contain": _NO_HALL, "notes": "Медицина compliance"},
        {"id": "tech-005", "intent": "analyze_lead", "slots": {"company": "ФинГрупп", "industry": "финансы"}, "must_contain": ["enterprise", "риск"], "must_not_contain": _NO_HALL, "notes": "Финансы enterprise"},
        {"id": "tech-006", "intent": "create_lead", "slots": {"company": "Кафе Уют", "industry": "общепит"}, "must_contain": ["basic", "stack"], "must_not_contain": _NO_HALL, "notes": "Малый бизнес basic"},
        {"id": "tech-007", "intent": "analyze_lead", "slots": {"company": "АгроСоюз", "industry": "сельхоз"}, "must_contain": ["1с", "сложност"], "must_not_contain": _NO_HALL, "notes": "Агро 1С"},
        {"id": "tech-008", "intent": "analyze_lead", "slots": {"company": "ЛогистикПро", "industry": "логистика"}, "must_contain": ["интеграц", "недел"], "must_not_contain": _NO_HALL, "notes": "Логистика ETL"},
        {"id": "tech-009", "intent": "analyze_lead", "slots": {"company": "АвтоДилер", "industry": "авто"}, "must_contain": ["stack", "presale"], "must_not_contain": _NO_HALL, "notes": "Авто дилер"},
        {"id": "tech-010", "intent": "create_lead", "slots": {"company": "ЭнергоСбыт", "industry": "энергетика", "employees": "500"}, "must_contain": ["it_maturity", "интеграц"], "must_not_contain": _NO_HALL, "notes": "Энергетика крупная"},
        {"id": "tech-011", "intent": "analyze_lead", "slots": {"company": "СтартАп Лаб", "industry": "IT", "note": "нужен webhook"}, "must_contain": ["api", "webhook"], "must_not_contain": _NO_HALL, "notes": "Стартап API"},
        {"id": "tech-012", "intent": "analyze_lead", "slots": {"company": "МашПром", "industry": "производство"}, "must_contain": ["1с", "риск"], "must_not_contain": _NO_HALL, "notes": "Производство ERP"},
        {"id": "tech-013", "intent": "analyze_lead", "slots": {"company": "Вектор", "industry": "e-commerce"}, "must_contain": ["bitrix", "интеграц"], "must_not_contain": _NO_HALL, "notes": "E-commerce"},
        {"id": "tech-014", "intent": "analyze_lead", "slots": {"company": "АКМЕ", "industry": "ритейл", "description": "сейчас Excel"}, "must_contain": ["excel", "миграц"], "must_not_contain": _NO_HALL, "notes": "Excel миграция"},
        {"id": "tech-015", "intent": "create_lead", "slots": {"company": "Гамма", "industry": "IT", "note": "SAP на пресейле"}, "must_contain": ["sap", "сложност"], "must_not_contain": _NO_HALL, "notes": "SAP интеграция"},
    ],
    "strategist": [
        {"id": "strategist-001", "intent": "analyze_lead", "slots": {"company": "Ромашка"}, "must_contain": ["decision", "next_action"], "must_not_contain": _NO_HALL, "notes": "Базовый синтез", "analyst_output": {"score": 72, "summary": "Средний потенциал ритейл", "next_steps": ["позвонить"]}, "economist_output": {"summary": "Бюджет 800к", "deal_probability_pct": 55}, "marketer_output": {"value_hook": "ускорение продаж"}},
        {"id": "strategist-002", "intent": "create_lead", "slots": {"company": "Север"}, "must_contain": ["priority", "final_reply"], "must_not_contain": _NO_HALL, "notes": "Новый лид", "analyst_output": {"score": 45, "summary": "Мало данных"}},
        {"id": "strategist-003", "intent": "analyze_lead", "slots": {"company": "ТехноПарк"}, "must_contain": ["high", "today"], "must_not_contain": _NO_HALL, "notes": "Горячий IT", "analyst_output": {"score": 88, "summary": "Горячий лид IT"}, "economist_output": {"deal_probability_pct": 75}},
        {"id": "strategist-004", "intent": "analyze_lead", "slots": {"company": "Кафе Уют"}, "must_contain": ["low", "nurture"], "must_not_contain": _NO_HALL, "notes": "Холодный SMB", "analyst_output": {"score": 30, "summary": "Малый бюджет"}},
        {"id": "strategist-005", "intent": "write_email", "slots": {"company": "МедЛайн"}, "must_contain": ["decision", "coach"], "must_not_contain": _NO_HALL, "notes": "Письмо контекст", "marketer_output": {"first_email": {"subject": "МедЛайн", "body": "текст"}}},
        {"id": "strategist-006", "intent": "analyze_lead", "slots": {"company": "ФинГрупп"}, "must_contain": ["decision", "rationale"], "must_not_contain": _NO_HALL, "notes": "Enterprise", "analyst_output": {"score": 80}, "economist_output": {"deal_segment": "enterprise"}},
        {"id": "strategist-007", "intent": "analyze_lead", "slots": {"company": "АгроСоюз"}, "must_contain": ["next_action", "final_reply"], "must_not_contain": _NO_HALL, "notes": "Агро", "analyst_output": {"score": 55, "risks": ["сезонность"]}},
        {"id": "strategist-008", "intent": "create_lead", "slots": {"company": "ЛогистикПро"}, "must_contain": ["medium", "decision"], "must_not_contain": _NO_HALL, "notes": "Логистика новый", "analyst_output": {"score": 50}},
        {"id": "strategist-009", "intent": "analyze_lead", "slots": {"company": "АвтоДилер"}, "must_contain": ["urgency", "next_action"], "must_not_contain": _NO_HALL, "notes": "Авто переговоры", "analyst_output": {"score": 70}, "economist_output": {"deal_probability_pct": 60}},
        {"id": "strategist-010", "intent": "analyze_lead", "slots": {"company": "ЭнергоСбыт"}, "must_contain": ["decision", "priority"], "must_not_contain": _NO_HALL, "notes": "Крупный энерго", "analyst_output": {"score": 75}, "tech_specialist_output": {"implementation_complexity": "high"}},
        {"id": "strategist-011", "intent": "analyze_lead", "slots": {"company": "СтартАп Лаб"}, "must_contain": ["this_week", "final_reply"], "must_not_contain": _NO_HALL, "notes": "Стартап", "analyst_output": {"score": 65, "summary": "IT стартап"}},
        {"id": "strategist-012", "intent": "analyze_lead", "slots": {"company": "МашПром"}, "must_contain": ["decision", "coach_tip"], "must_not_contain": _NO_HALL, "notes": "Производство", "analyst_output": {"score": 58}, "economist_output": {"pricing_strategy": "рассрочка"}},
        {"id": "strategist-013", "intent": "list_leads", "slots": {}, "must_contain": ["decision", "final_reply"], "must_not_contain": _NO_HALL, "notes": "Список лидов", "analyst_output": {"summary": "5 горячих лидов"}},
        {"id": "strategist-014", "intent": "analyze_lead", "slots": {"company": "Вектор"}, "must_contain": ["next_action", "rationale"], "must_not_contain": _NO_HALL, "notes": "Квалификация", "analyst_output": {"score": 62, "bant": {"need": "высокая"}}},
        {"id": "strategist-015", "intent": "analyze_lead", "slots": {"company": "АКМЕ"}, "must_contain": ["high", "today"], "must_not_contain": _NO_HALL, "notes": "Тендер срочно", "analyst_output": {"score": 90, "summary": "Срочный тендер"}, "marketer_output": {"value_hook": "выиграть тендер"}},
    ],
}


def _case_row(agent: str, raw: dict) -> dict:
    row = {k: v for k, v in raw.items() if k not in ("analyst_output", "economist_output", "marketer_output", "tech_specialist_output")}
    row["agent"] = agent
    extra = {}
    for key in ("analyst_output", "economist_output", "marketer_output", "tech_specialist_output"):
        if key in raw:
            extra[key] = raw[key]
    if extra:
        row["state_overrides"] = extra
    return row


def main() -> None:
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    for agent in AGENT_IDS:
        path = AGENTS_DIR / f"{agent}.jsonl"
        rows = [_case_row(agent, c) for c in _CASES[agent]]
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{agent}: {len(rows)} -> {path}")


if __name__ == "__main__":
    main()
