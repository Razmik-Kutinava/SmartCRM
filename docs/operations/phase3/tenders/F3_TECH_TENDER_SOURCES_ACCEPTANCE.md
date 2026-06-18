# Ф3 — Дожать бесплатные источники тендеров

**PRD_MAP:** Тех. спец — тендеры → п.3 (вместо Контура в Ф3).

**Цель:** Gosplan prod, TenderGuru + фильтры, мониторинг через `tender_sources`, DataNewton на карточке, доки → `/evaluate`. Переход на Контур — Ф4 без смены UI/API.

---

## Сделано

| # | Что | Где |
|---|-----|-----|
| 1 | Слой `tender_sources` (legacy / kontur-stub) | `services/tender_sources/` |
| 2 | Gosplan prod | `GOSPLAN_USE_PROD=1` |
| 3 | Фильтр релевантности | `TENDER_SEARCH_MIN_RELEVANCE`, `min_relevance` в search |
| 4 | Мониторинг на `search_for_monitor` + `search_min_relevance` в config | `tender_monitor.py` |
| 5 | DataNewton на карточке | кнопка на `/tenders`, API `/enrich/{inn}` |
| 6 | Доки → evaluate | вкладка «Документы» + «Полная оценка» (было) |
| 7 | Статус провайдера | `GET /api/tenders/provider/status` |

---

## Проверка

```bash
cd backend
python -m pytest tests/services/test_tender_provider_layer.py tests/services/test_tender_monitor.py tests/api/test_tenders_provider_api.py -q
```

1. `GOSPLAN_USE_PROD=1` → `provider/status` → `gosplan_use_prod: true`
2. Поиск с `min_relevance=30` — меньше шума
3. Карточка тендера с ИНН → DataNewton
4. PDF → «Полная оценка»

---

## Не в шаге

- Контур API → [`F4_KONTUR_GATE.md`](../../phase4/tenders/F4_KONTUR_GATE.md)
- Решение участвовать/нет (следующий пункт MAP)
