# Ф4 — Vendor crawl: тюнинг RAG tech_specialist

**Откуда:** Ф3 краулинг закрыт (шаги 1–4, live 871 чанк, 10 PDF) — см. [`F3_VENDOR_CRAWL_ACCEPTANCE.md`](../../phase3/rag/F3_VENDOR_CRAWL_ACCEPTANCE.md).

**Зачем:** база есть, но без регулярного обновления и метаданных retrieval слабее; дыры не видны без eval.

**PRD_MAP:** Фаза 4 → Vendor crawl (тюнинг).

---

## Чеклист (делать после «ок» на Ф3 crawl)

| # | Задача | Что сделать | Проверка |
|---|--------|-------------|----------|
| 1 | **Автокраул** | `auto_crawl_enabled: true` в `vendor_crawl_config.json`; интервал `auto_crawl_interval_hours`; убедиться что `vendor_crawl_poll_loop` в lifespan | Статус `/api/rag/vendor-crawl/status` — прогоны по расписанию |
| 2 | **Глубже doc_urls** | Добавить KB, datasheet, release notes, support/docs — не только продуктовые лендинги (ME, PT) | Больше PDF/HTML чанков по продуктам; меньше «маркетинг без цифр» |
| 3 | **Метаданные чанков** | При ingest: `product`, `doc_type` (datasheet, manual, kb, release_notes) в metadata Chroma | `retrieve_context` для tech_specialist — фильтр/буст по типу |
| 4 | **Eval retrieval** | 10–20 вопросов к tech_specialist: «нашёл ли правильный фрагмент?» (golden + manual или скрипт) | Отчёт pass rate; список промахов → doc_urls / промпт |

---

## Не в этом чеклисте (отдельно)

- Больше вендоров (3-й, 4-й…) — по мере продаж
- Голосом «добавь ссылку на доки» — BACKLOG / интент Hermes
- Playwright click-through на кнопки SPA — если search + doc_urls не хватает

---

## Связанные файлы

- `backend/data/vendor_crawl_config.json`
- `backend/rag/vendor_crawl_background.py`
- `backend/rag/vendor_crawl.py` · `vendor_crawl_pdf.py`
- UI `/ops/vendor-crawl`
