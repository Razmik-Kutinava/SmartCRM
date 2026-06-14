# Leads: кнопка «Обогатить» на карточке (Ф2 §9)

**PRD_MAP:** Кнопка «Обогатить» на `/leads/{id}`

## Было

- Enrich только через `/search` → вкладка «Обогащение» → выбор лида → «Сохранить в карточку»
- На карточке лида нет one-click обогащения

## Стало

| Компонент | Поведение |
|-----------|-----------|
| `enrichLeadOnCard.js` | `POST /api/search/enrich-lead` → `enrichedToLeadPatch` → `PATCH /api/leads/{id}` |
| `/leads/{id}` header | Кнопка `data-testid="lead-card-enrich"` |
| Сообщение | `lead-card-enrich-msg` — поля обновлены / кэш / ошибка |

Пайплайн тот же, что на `/search` enrich (включая кэш 24 ч и `page_fetch`).

## Команды

```bash
cd backend
python -m pytest tests/rag/test_enrich_cache.py tests/api/test_search_enrich_lead_api.py tests/lib/test_enrich_lead_apply.py -q --override-ini="filterwarnings="
python scripts/smoke_search_enrich_lead.py
```

## Критерии

- [x] Кнопка на карточке без перехода в `/search`
- [x] PATCH полей после enrich
- [x] Бейдж/сообщение о результате
- [x] pytest enrich apply + API

## Не в scope

- Голос «обогати лид …» (опц. MAP §9 п.2)
