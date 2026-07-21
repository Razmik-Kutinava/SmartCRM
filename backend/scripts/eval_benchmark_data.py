"""
Общие эталонные сценарии create_lead для seed и офлайн-прогона eval.
"""
from __future__ import annotations

BENCHMARK_SCENARIOS: list[dict] = [
    {
        "title": "Бенч: Ромашка (длинная)",
        "phrase": (
            "добавь лид ООО Ромашка связь с контактным лицом Петров Семён Викторович "
            "город Москва отрасль розничная торговля источник выставка Цветы-2025 "
            "бюджет 1 миллион 200 тысяч рублей заметка перезвонить в четверг после обеда"
        ),
        "expected_intent": "create_lead",
        "expected_slots": {
            "company": "ООО Ромашка",
            "contact": "Петров Семён Викторович",
            "phone": None,
            "email": None,
            "budget": "1200000",
            "note": (
                "Москва; розничная торговля; выставка Цветы-2025; перезвонить в четверг после обеда"
            ),
        },
        "success_criteria": (
            "Интент create_lead. Слоты: company=ООО Ромашка; contact=только ФИО Петров Семён Викторович; "
            "budget≈1.2 млн; в note — город Москва, отрасль, источник, текст заметки про четверг."
        ),
        "desired_outcome": "Длинная фраза не теряет компанию и ФИО; остальное в note/budget.",
    },
    {
        "title": "Бенч: TechSoft",
        "phrase": (
            "создай лид компания TechSoft LLC контакт Мария Иванова телефон плюс семь четыре девять "
            "пять один два три четыре пять шесть семь почта mari и собака techsoft точка ru "
            "город Санкт-Петербург отрасль информационные технологии источник заявка с сайта бюджет 800 тысяч"
        ),
        "expected_intent": "create_lead",
        "expected_slots": {
            "company": "TechSoft LLC",
            "contact": "Мария Иванова",
            "phone": "+74951234567",
            "email": "mari@techsoft.ru",
            "budget": "800000",
            "note": "Санкт-Петербург; IT; заявка с сайта",
        },
        "success_criteria": (
            "company TechSoft LLC; contact Мария Иванова; phone и email извлечены; budget 800000; "
            "город/отрасль/источник в note."
        ),
        "desired_outcome": "Корректное извлечение телефона и email из разговорной формулировки.",
    },
    {
        "title": "Бенч: Вектор",
        "phrase": (
            "новый лид ООО Вектор контактное лицо Петров Алексей город Казань "
            "почта petrov собака vector точка ru примечание клиент пришёл с холодного звонка бюджет не указан"
        ),
        "expected_intent": "create_lead",
        "expected_slots": {
            "company": "ООО Вектор",
            "contact": "Петров Алексей",
            "phone": None,
            "email": "petrov@vector.ru",
            "budget": None,
            "note": "Казань; холодный звонок",
        },
        "success_criteria": "company ООО Вектор; contact ФИО; email; note с городом и источником.",
        "desired_outcome": "Без бюджета — интент всё равно create_lead.",
    },
    {
        "title": "Бенч: Техпром",
        "phrase": (
            "нужен лид Техпром контакт Иванов Иван Иванович телефон восемь девять один шесть один два три "
            "четыре пять шесть семь бюджет два с половиной миллиона отрасль машиностроение источник рекомендация партнёра"
        ),
        "expected_intent": "create_lead",
        "expected_slots": {
            "company": "Техпром",
            "contact": "Иванов Иван Иванович",
            "phone": "+79161234567",
            "email": None,
            "budget": "2500000",
            "note": "машиностроение; рекомендация партнёра",
        },
        "success_criteria": (
            "company Техпром; contact полное ФИО; phone; budget 2.5 млн; отрасль и источник в note."
        ),
        "desired_outcome": "Распознавание бюджета в словесной форме и цифр телефона.",
    },
    {
        "title": "Бенч: Альфа (короткая)",
        "phrase": "добавь лид ООО Альфа контакт Сидоров Пётр телефон плюс семь девятьсот ноль один два три четыре пять шесть семь",
        "expected_intent": "create_lead",
        "expected_slots": {
            "company": "ООО Альфа",
            "contact": "Сидоров Пётр",
            "phone": "+79001234567",
            "email": None,
            "budget": None,
            "note": None,
        },
        "success_criteria": "Минимальный набор: company, contact, phone.",
        "desired_outcome": "Базовый короткий кейс без лишних полей.",
    },
]
