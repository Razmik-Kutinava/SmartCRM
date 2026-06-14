# Сценарий tender evaluation — acceptance (Ф2 §2 п.394)

**PRD_MAP:** «Сценарий: оценка тендера (тех + эконом)»

## Было

- Оценка тендера только через HTTP `/api/tenders/analyze` (отдельные агенты tender/tech)
- Голос «оцени тендер» не имел fanout-сценария tech∥economist→strategist
- Нет `voice_action` modal с синтезом вердикта участия

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `scenarios/tender_evaluation.py` | intent `evaluate_tender`, tech+economist |
| `scenarios/tender_context.py` | слоты title/budget/ТЗ → контекст агентов |
| `supervisor` + `rescue` | parallel fanout + CPU-маршрут |
| `economist` / `tech_specialist` | `_analyze_tender()` |
| `strategist` | вердикт участия для evaluate_tender |
| `voice_action` | modal + synthesis + tender snapshot, route `/tenders` |
| `module_contract` | module `tenders` |

## Критерии

- [x] «оцени тендер …» → `evaluate_tender`, agents tech+economist, parallel
- [x] Strategist синтезирует решение → modal `payload.synthesis`
- [x] Секции tech + economics в модалке
- [x] pytest зелёный

## Не в scope

- п.395–396 (отчёт, похожие клиенты)
- автоподстановка карточки тендера из БД saved (можно передать slots с UI)

## Коммит

См. CHANGELOG текущего шага.
