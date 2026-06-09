# Chroma RAG + разделение по агентам — acceptance (2026-06-08)

PRD_MAP: **«Поиск и RAG (базово)» п.3**

## Команда

```bash
cd backend && python scripts/smoke_rag_chroma.py
```

11 pytest (изолированная Chroma) + live-статистика локальной базы `data/chroma_db`.

---

## Было → стало (простыми словами)

| Было | Стало |
|------|--------|
| В MAP п.3 стояла галочка, но **не было** перепрохода: ни смоука, ни API-тестов, ни DevTools-чеклиста | **Перепроход закрыт**: смоук, pytest, acceptance, UI через `apiFetch` |
| `/rag` ходил в API голым `fetch` (401 при auth) | Все вызовы кроме upload-progress → `apiFetch` / `apiPost` / `apiDelete`; upload XHR с `X-API-Key` |
| Не было явной проверки «~1592 чанка + по агентам» | Live: **1592 чанка**, 11 источников, `economist:960`, `all:624`, `marketer:8` |
| Фильтр `for_agent` был в коде, но не в acceptance | pytest: чанк `economist` не виден `marketer` и наоборот |

---

## ✅ СДЕЛАНО и ПРОВЕРЕНО

| # | Что | Где | Проверка |
|---|-----|-----|----------|
| 1 | Chroma коллекция `smartcrm_knowledge` | `rag/chroma_store.py` | live count 1592 |
| 2 | Метаданные `for_agent` при ingest | `rag/ingest.py` | unit + API test |
| 3 | Query с фильтром агента | `query_documents(for_agent=…)` | pytest isolated |
| 4 | Prefetch RAG в слоты агентов | `rag/retrieve.py` | `test_prefetch_rag_fills_slots` |
| 5 | API `/api/rag/*` | `api/routes/rag.py` | `test_rag_api.py` |
| 6 | UI `/rag` — счётчик, поиск, ingest | `routes/rag/+page.svelte` | DevTools |
| 7 | Смоук CLI | `smoke_rag_chroma.py` | 11 pytest + артефакт JSON |

**Агенты в базе (live):** `all`, `analyst`, `strategist`, `economist`, `marketer`, `tech_specialist` — в ingest; в данных сейчас в основном `economist` + `all` + немного `marketer`.

---

## DevTools (`localhost:5174/rag`)

> На шаге бэк/фронт не были запущены — UI проверить при `npm run dev` + uvicorn.

| Проверка | Результат |
|----------|-----------|
| Live Chroma `collection_count()` | ✅ 1592 |
| pytest ingest + query + agent filter | ✅ 11 passed |
| UI `data-testid=rag-chunk-count` | 👤 при запущенном фронте |

---

## ❌ НЕ СДАЛИ (следующие пункты MAP)

| Что | Пункт |
|-----|--------|
| Загрузка PDF/текста — **полный** перепроход UI (preview/upload E2E) | **п.4** |
| Кнопка «сохранить в базу» из поиска — acceptance | **п.5** |
| Смоук enrich-lead | MAP п.110 |
| Авто-чанки | **Фаза 2** |
| Миграция Chroma → pgvector | BACKLOG инфра |

---

## Следующий пункт MAP

**п.4 — загрузка PDF/текста в `/rag`** (отдельный перепроход).
