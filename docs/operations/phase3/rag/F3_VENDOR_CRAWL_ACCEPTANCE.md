# Ф3 — Краулинг URL вендоров → RAG тех. спеца

**PRD_MAP:** Self-improvement → Краулинг URL вендоров.

## Критерии

| # | Пункт | Проверка |
|---|-------|----------|
| 1 | Конфиг URL вендоров | `GET /api/rag/vendor-crawl/config` |
| 2 | Ручной краулинг | `POST /api/rag/vendor-crawl/run` |
| 3 | Чанки в RAG `tech_specialist` | `for_agent=tech_specialist`, `source_type=vendor_crawl` |
| 4 | Дедуп по URL | повторный crawl → тот же `source_id` (hash URL) |
| 5 | Статус последнего прогона | `GET /api/rag/vendor-crawl/status` |
| 6 | UI Ops | `/ops/vendor-crawl` — конфиг, запуск, автозапуск |
| 7 | Фон по расписанию | `auto_crawl_enabled` + `vendor_crawl_poll_loop` в lifespan |

## Конфиг

`backend/data/vendor_crawl_config.json` — список вендоров: `seed_url`, `max_pages`, `max_depth`, `enabled`.

## Команды

```bash
cd backend
python -m pytest tests/rag/test_vendor_crawl.py tests/api/test_vendor_crawl_api.py -q
```

Dry-run (без записи в Chroma):

```bash
curl -X POST http://127.0.0.1:8000/api/rag/vendor-crawl/run \
  -H "Content-Type: application/json" \
  -d '{"vendor_id":"demo_vendor","dry_run":true}'
```

Live crawl (нужен ключ API + `enabled: true` или явный `vendor_id`):

```bash
curl -X POST http://127.0.0.1:8000/api/rag/vendor-crawl/run \
  -H "Content-Type: application/json" \
  -d '{"vendor_id":"manageengine","dry_run":false}'
```

## Файлы

- `rag/vendor_crawl.py` — обход страниц, ingest
- `rag/vendor_crawl_config.py` — конфиг и state
- `api/routes/rag.py` — HTTP API

## Live-прогон (2026-06-17)

Конфиг: `backend/data/vendor_crawl_config.json` — ManageEngine RU + Positive Technologies.

| Вендор | Seed | Страниц OK | Чанков RAG |
|--------|------|------------|------------|
| ManageEngine | https://www.manageengine.com/ru/ | 7/8 | 33 |
| Positive Technologies | https://ptsecurity.com/ | 3/8 | 18 |
| **Итого** | | **10/16** | **51** |

Артефакт (локально, gitignore): `backend/data/artifacts/rag/vendor_crawl_live_20260617.json` · state: `vendor_crawl_state.json`.

Провалы ожидаемы: `favicon.ico`, шрифты `.woff2` на Next.js-сайте PT — не HTML.

Команда прогона:

```powershell
cd backend
python -c "import asyncio; from rag.vendor_crawl import run_vendor_crawl; asyncio.run(run_vendor_crawl(dry_run=False))"
```

## Не в scope (BACKLOG)

- PDF по ссылкам, логин на порталы
- Фильтр ссылок: не ходить на `/_next/static/`, `.woff2`
- UI: `/ops/vendor-crawl` ✅
- Фон: `vendor_crawl_background.py` + lifespan в `main.py` ✅
