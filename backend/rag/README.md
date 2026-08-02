# RAG — база знаний и поиск

ChromaDB, загрузка документов, гибридный поиск (вектор + веб).

---

## Пакет `search/` — поиск компаний и prospect

| Файл | За что |
|------|--------|
| `providers.py` | Tavily, Brave, Exa и др. |
| `merge.py` | Слияние результатов источников |
| `company_search.py` | Поиск компании по запросу |
| `prospect.py` | prospect + `enrich_lead` |
| `research_lead.py` | `research_lead` — 🔍 Brave/Tavily/Serper + досье (`web_research`) + passport extract |
| `research_dossier.py` | Синтез досье Groq→Ollama (досье + JSON-паспорт одним проходом), читаемый fallback, `ensure_nonempty_summary` / `is_usable_dossier`, env-лимиты токенов/контекста |
| `research_passport.py` | Extract паспорта из веб (regex+LLM или JSON из досье); `allow_llm=False` — без второго вызова |
| `research_status.py` | Фазы 🔍 для UI/логов: `searching / synthesizing / done_llm / done_fallback` |
| `research_lead.py` | Оркестрация 🔍: ИНН→Checko→веб→BuiltWith/DNS; stages; second_pass по gaps; ~2.5 мин |
| `resolve_inn.py` | ИНН: EN→RU варианты → ЕГРЮЛ → веб-regex |
| `company_name_ru.py` | Алиасы брендов и очистка имени для ЕГРЮЛ |
| `field_fill.py` | Добор gaps: целевые запросы → extract → passport + Checko |
| `domain_enrich.py` | Параллельно BuiltWith + WhoIs/DNS для 🔍 (без ключа на DNS) |
| `enrich_sources.py` | Checko/ИНН, таргет-запросы, парсинг сайта, fetch URL из поиска |
| `checko_passport.py` | Сборка и merge `checko_json` для enrich; UF-почта → `company.emails` (`emails_from_bitrix_blobs`) |
| `brave_limit.py` | Кэш и semaphore Brave (429) |
| `rag_queries.py` | Запросы к Chroma |
| `relevance.py` | Score релевантности для авто-чанков |
| `cache.py` | Кэш поиска по компании |
| `enrich_cache.py` | Кэш полного результата enrich (company+ИНН+industry, TTL 24 ч) |
| `config.py` | Ключи и лимиты |

Старый монолит `search.py` в корне `rag/` — shim/re-export для совместимости.

---

## Файлы в корне `rag/`

| Файл | За что |
|------|--------|
| `chroma_store.py` | Работа с ChromaDB |
| `chroma.py` | Низкоуровневый клиент |
| `ingest.py` | Загрузка в индекс; `ingest_manual_text` + `_metadata_from_search_doc` (URL → `source_url` в чанках) |
| `auto_ingest.py` | Авто-чанки Search→RAG при relevance > порога |
| `dialogue_facts.py` | Факты из диалога агента → RAG; опц. `RAG_DIALOGUE_LLM=1` |
| `qa_structure.py` | LLM Q&A для auto-ingest; опц. `RAG_AUTO_STRUCTURE_LLM=1` |
| `search_hits.py` | Нормализация web-hits → документы ingest-batch |
| `retrieve.py` | Получение чанков по запросу |
| `chunking.py` | Разбиение текста на чанки |
| `parsers.py` | Парсинг PDF/HTML для ingest |
| `vendor_crawl_config.py` | Конфиг URL вендоров (JSON в `data/`) |
| `vendor_crawl_urls.py` | Фильтр мусора, приоритет ссылок |
| `vendor_crawl_quality.py` | Фильтр мусорного текста до чанков |
| `vendor_crawl_pdf_search.py` | Web search `site:домен filetype:pdf` |
| `vendor_crawl_pdf.py` | Скачивание и ingest PDF |
| `vendor_crawl_sitemap.py` | Опционально sitemap.xml → URL |
| `vendor_crawl_playwright.py` | Chromium: PDF-ссылки на SPA + fallback fetch |
| `vendor_crawl.py` | Краулинг; `_fetch_bytes` для PDF (без блока .pdf) |
| `vendor_crawl_background.py` | Фоновый планировщик (интервал из конфига) |

Эндпоинты: `api/routes/rag.py` (`/vendor-crawl/*`), UI `/ops/vendor-crawl`.
