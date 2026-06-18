# Вердикт участия в тендере — acceptance (Ф3 § Тех. спец — тендеры)

**PRD_MAP:** «Решение участвовать/нет с обоснованием (Тех. спец + Экономист → Стратег)»

## Было

- `POST /api/tenders/evaluate` возвращал сырой `result` без структурированного вердикта
- UI: полная оценка писала текст в «Тенд. спец», без вкладки «Вердикт» и бейджа
- Вердикт не сохранялся в `snapshot` сохранённого тендера
- Стратег не просил явное поле `participation_verdict`

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `core/tender_participation.py` | `extract_participation()` — participate / caution / no + обоснование |
| `api/routes/tenders/evaluate_routes.py` | ответ `participation`, enrichment в слотах, `evaluated_at` |
| `agents/strategist.py` | для `evaluate_tender` — поле `participation_verdict` в JSON |
| `/tenders` UI | вкладка «Вердикт», баннер в шапке карточки, сохранение в snapshot |
| pytest | `tests/core/test_tender_participation.py`, расширен `test_evaluate_tender_api` |

## Критерии

- [x] Полная оценка: fanout tech∥economist → strategist
- [x] API возвращает `participation.verdict` + `label` + rationale/next_action
- [x] UI показывает Участвовать / Осторожно / Не участвовать
- [x] Вердикт в snapshot при сохранении в «Мои тендеры»
- [x] pytest зелёный (без live LLM)

## Не в scope

- Аналитика v2, Контур.Закупки (Ф4)
- Автозапуск оценки из мониторинга без действия оператора
