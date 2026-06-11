# Тендеры baseline — acceptance (2026-06-11)

PRD_MAP: **«Тендеры `/tenders`»** · Ф1 baseline **закрыт**.

## Команда

```bash
cd backend && python scripts/smoke_tenders_baseline.py
```

## Закрыто

| # | Пункт | Проверка |
|---|--------|----------|
| 1 | UI + API | `/tenders`, `/api/tenders/*` |
| 2 | Поиск + Gosplan tail | бейдж «без совпадения», баннер, кнопка «Скрыть» |
| 3 | Планы | `GET /api/tenders/plans/search` |
| 4 | Мои / Архив | `tender_saved`, `GET/POST/PATCH /api/tenders/saved` |
| 5 | Serper + Tavily | `web_search.py` в `/search`, `sources.serper/tavily` |
| 6 | Лимиты Ops | `/api/usage/stats` |
| 7 | Агенты | `POST /api/tenders/analyze` (LLM), сохранение анализа в БД |
| 8 | PDF/DOCX → текст | `POST /api/tenders/documents/extract` · UI → `document_text` в analyze |

## Live (нужны ключи)

- `TENDERGURU_API_KEY`, `GROQ_API_KEY` — поиск и анализ
- `SERPER_API_KEY`, `TAVILY_API_KEY` — веб-результаты в выдаче
- `DATANEWTON_API_KEY` — обогащение заказчика (опц.)

## Опционально позже

- Ф2 §7: голосовые команды по тендерам
- Платный API Контур (gate по сделке)
