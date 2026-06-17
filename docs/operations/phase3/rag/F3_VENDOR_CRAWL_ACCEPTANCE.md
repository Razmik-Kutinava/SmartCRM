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
| 8 | Поле doc_urls + фильтр мусора + PDF | `vendor_crawl_urls.py`, UI textarea, stats в отчёте |
| 9 | Автопоиск PDF `site:домен filetype:pdf` | `search_pdfs` + `max_pdf_pages`; Brave/Tavily в `.env` |

## Конфиг

`backend/data/vendor_crawl_config.json` — вендор: `seed_url`, **`doc_urls`**, **`search_pdfs`**, **`max_pdf_pages`**, `max_pages`, `max_depth`, `use_sitemap`, `enabled`.

## Команды

```bash
cd backend
python -m pytest tests/rag/test_vendor_crawl_urls.py tests/rag/test_vendor_crawl_pdf.py tests/rag/test_vendor_crawl_pdf_search.py tests/rag/test_vendor_crawl.py tests/api/test_vendor_crawl_api.py -q
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

- `rag/vendor_crawl_urls.py` — фильтр мусора, приоритет ссылок
- `rag/vendor_crawl_sitemap.py` — sitemap.xml
- `rag/vendor_crawl_pdf_search.py` — web search PDF
- `rag/vendor_crawl_pdf.py` — ingest PDF байтов
- `rag/vendor_crawl_config.py` — конфиг и state
- `api/routes/rag.py` — HTTP API

## Live-прогон v1 (2026-06-17, до улучшений)

| Вендор | Страниц OK | Чанков |
|--------|------------|--------|
| ManageEngine | 7/8 | 33 |
| PT | 3/8 | 18 |
| **Итого** | 10/16 | **51** |

## Live-прогон v2 (2026-06-17, doc_urls + фильтр + depth 2)

| Вендор | Страниц OK | Чанков | Настройки |
|--------|------------|--------|-----------|
| ManageEngine | **40/40** | 239 | doc_urls×4, sitemap, max 40 |
| PT | **40/40** | 343 | doc_urls×3, max 40, depth 2 |
| **Итого** | **80/80** | **582** | |

Артефакт: `backend/data/artifacts/rag/vendor_crawl_v2_20260617.json` (gitignore).

Провалы v1: favicon, woff2 — в v2 отфильтрованы на входе.

## Шаг 1 — автопоиск PDF (2026-06-17)

**Было:** PDF только если прямая ссылка `.pdf` в HTML; v2 live — 0 PDF.

**Стало:**
- `search_for_rag(site:домен, content_type=pdf)` при `search_pdfs: true`
- Отдельный лимит `max_pdf_pages` (не съедает HTML-бюджет)
- Распознавание PDF по байтам `%PDF` при редиректе
- `is_pdf_url` + пути `/pdf/`
- UI: чекбокс «поиск PDF», лимит PDF
- pytest **18 PASS**

**Live:** без ключей Brave/Tavily поиск вернул 0 URL — нужен `.env` провайдера; код и тесты с mock OK.

## Не в scope (BACKLOG)

- **Шаг 2:** фильтр мусора в PDF до чанков
- Playwright/JS-render для SPA
- Голосом «добавь ссылку на доки» (интент → API)
