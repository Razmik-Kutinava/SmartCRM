# Тендеры baseline — acceptance (2026-06-11)

PRD_MAP: **«Тендеры `/tenders`»** · Ф1 baseline.

## Команда

```bash
cd backend && python scripts/smoke_tenders_baseline.py
```

Или только pytest:

```bash
cd backend && python -m pytest tests/test_tender_sources.py tests/smoke/test_tenders_baseline_smoke.py -q
```

## Что закрыто

| # | Пункт MAP | Проверка |
|---|-----------|----------|
| 1 | UI + API | `/tenders` (frontend); `/api/tenders/search`, `plans/search`, `save` |
| 2 | Поиск 44/223, фильтры | mocked WS search; невалидная дата → **400** (не 500) |
| 3 | Планы закупок | `GET /api/tenders/plans/search` (mock TenderGuru) |
| 5 | TenderGuru + Gosplan | `sources.gosplan` / `sources.tenderguru` в ответе search |
| 6 | Лимиты Ops | `GET /api/usage/stats` — сервисы `gosplan`, `datanewton` |

## Хвосты (не блокер baseline)

| Хвост | Где |
|-------|-----|
| «Мои тендеры» / «Архив» — заглушки UI | `BACKLOG.md` 🟡 |
| Gosplan free: unfiltered tail в выдаче | `BACKLOG.md` 🟡 |
| Serper/Tavily в тендерах | только `/search`, не `/api/tenders` |
| Агенты на карточке — MOCK | Ф2 §7 |
| `POST /save` — `persisted: false` | Ф2 §7 + БД |

## DevTools (опционально)

1. Backend `:8000`, `npm run dev`
2. `/tenders` → поиск по ключевым словам → список + панель карточки
3. `/ops/api-limits` — счётчики gosplan/datanewton после поиска

## Связь MAP

- Блок «Тендеры» → ✅ baseline
- Ф2 очередь **9** §7 — агентский анализ (не этот шаг)
