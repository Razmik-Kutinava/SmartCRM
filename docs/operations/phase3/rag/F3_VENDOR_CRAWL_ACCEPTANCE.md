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
| 10 | Фильтр качества до чанков | `vendor_crawl_quality.py`, `quality_rejected` в stats |
| 11 | Playwright SPA PDF | `use_playwright`; `playwright_pdf_found`; fallback fetch |

## Конфиг

`backend/data/vendor_crawl_config.json` — вендор: `seed_url`, **`doc_urls`**, **`search_pdfs`**, **`use_playwright`**, **`max_pdf_pages`**, `max_pages`, `max_depth`, `use_sitemap`, `enabled`.

## Команды

```bash
cd backend
python -m pytest tests/rag/test_vendor_crawl_quality.py tests/rag/test_vendor_crawl_urls.py tests/rag/test_vendor_crawl_pdf.py tests/rag/test_vendor_crawl_pdf_search.py tests/rag/test_vendor_crawl_playwright.py tests/rag/test_vendor_crawl.py tests/api/test_vendor_crawl_api.py -q
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
- `rag/vendor_crawl_playwright.py` — Chromium SPA PDF
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

## Шаг 2 — фильтр качества (2026-06-17)

**Было:** весь текст → чанки без проверки.

**Стало:** `vendor_crawl_quality.py` — отсев до ingest:
- слишком короткий
- кракозябры (`\ufffd`)
- мало уникальных слов
- одинаковое слово >45% текста
- мало букв/цифр

Статистика: `quality_rejected` в отчёте и UI. pytest **23 PASS**.

## Шаг 3 — live PDF + RAG (2026-06-17)

| Метрика | Значение |
|---------|----------|
| HTML OK | 80 |
| **PDF OK** | **10** (1 отброшен quality:too_short) |
| PDF search нашёл | 11 |
| **Всего чанков** | **871** |
| RAG tech_specialist | ✅ фрагменты из PDF (ServiceDesk, NGFW, datasheet) |

Фикс: `_fetch_bytes` не использует `_is_fetchable_url` (там `.pdf` запрещены).

Артефакт: `backend/data/artifacts/rag/vendor_crawl_step3_20260617.json`.

## Шаг 4 — Playwright SPA PDF (2026-06-17)

**Было:** PDF только из HTML/поиска; ссылки за JS на SPA (PT и др.) не попадали в очередь.

**Стало:**
- `vendor_crawl_playwright.py` — Chromium headless, `networkidle`, сбор `a[href]` / `data-href` / `data-url`
- `use_playwright` в конфиге; PT включён
- Fallback `fetch_pdf_bytes_playwright` если httpx не скачал PDF
- Статистика `playwright_pdf_found`; UI чекбокс «Playwright SPA»
- `playwright install chromium` перед live

**Live smoke:** discover на PT seed/doc_urls — 0 новых PDF (шаг 3 search уже дал 10); инфра и fallback готовы.

## Тюнинг → Фаза 4

См. [`F4_VENDOR_CRAWL_TUNING.md`](../../phase4/rag/F4_VENDOR_CRAWL_TUNING.md) — автокраул, doc_urls, метаданные, eval retrieval.

## Не в scope (BACKLOG)

- Голосом «добавь ссылку на доки» (интент → API)
