# 6 режимов поиска — acceptance (2026-06-08)

PRD_MAP: **«Поиск и RAG (базово)» п.2**

## Команда

```bash
cd backend && python scripts/smoke_search_modes.py
```

19 pytest (моки API + unit) + опционально live `free_search` при ключах в `.env`.

---

## ✅ СДЕЛАНО и ПРОВЕРЕНО

| # | Режим | API | UI таб | Автотест | Live |
|---|--------|-----|--------|----------|------|
| 1 | **company** — поиск по компании | `POST /api/search/run` | `search-tab-company` | pytest mock + п.1 DevTools | ✅ Сбербанк → 7 результатов (п.1) |
| 2 | **free** — свободный запрос | `POST /api/search/ask` | `search-tab-free` | pytest mock | ✅ DevTools «CRM для ритейла» → 10 результатов |
| 3 | **prospect** — проспектинг ICP | `POST /api/search/prospect` | `search-tab-prospect` | pytest mock + unit LLM mock | CLI smoke only |
| 4 | **enrich** — обогащение лида | `POST /api/search/enrich-lead` | `search-tab-enrich` | pytest mock + unit | CLI smoke only |
| 5 | **rag** — материалы для RAG | `POST /api/search/find-for-rag` | `search-tab-rag` | pytest mock + unit fanout | CLI smoke only |
| 6 | **agent** — задача агенту ReAct | `POST /api/search/agent-task` | `search-tab-agent` | pytest mock | CLI smoke only |

**Инфраструктура шага:**

- `frontend/src/routes/search/+page.svelte` — 6 табов, формы, `data-testid` на табах и кнопках submit
- Все вызовы API — `apiFetch` / `apiPost` (закрыто в п.1)
- `tests/api/test_search_modes_api.py` — 6 эндпоинтов + валидация 400
- `tests/rag/test_search_modes.py` — unit `search_for_rag`, `prospect_companies`, `enrich_lead`
- `smoke_search_modes.py` — агрегатор pytest + live `free_search` + probe фронта

**DevTools (`localhost:5174/search`):**

| Проверка | Результат |
|----------|-----------|
| 6 табов `data-testid=search-tab-*` | ✅ все найдены |
| 6 кнопок submit при переключении таба | ✅ |
| company live (п.1) | ✅ |
| free live «CRM для ритейла» | ✅ `serper, brave, tavily` · 10 результатов |

---

## ❌ НЕ СДАЛИ (следующие пункты MAP — не баг п.2)

| Что | Почему не в п.2 | Куда |
|-----|-----------------|------|
| **Chroma RAG ~1592 чанка**, разделение по агентам | п.3 MAP | `go` п.3 |
| **Загрузка PDF/текста** на `/rag` | п.4 MAP | `go` п.4 |
| **Кнопка «сохранить в базу»** (базово) | п.5 MAP; в табе rag есть ingest-batch, но acceptance Chroma — п.3–5 | `go` п.5 |
| **Смоук enrich-lead end-to-end** (live LLM + веб) | отдельная строка MAP п.110 | `BACKLOG.md` |
| **Авто-чанки** из поиска/диалога | Фаза 2 | `BACKLOG.md` / RAG.md |
| **Live DevTools** prospect / enrich / agent (нужен Groq, 30–60 с) | дорого в CI; API покрыты моками | 👤 spot-check по желанию |
| **«+ В CRM»** в проспектинге — полный E2E до списка лидов | вне scope п.2 (лиды закрыты отдельно) | опционально |

---

## Файлы

| Зона | Путь |
|------|------|
| UI | `frontend/src/routes/search/+page.svelte` |
| API | `backend/api/routes/search.py` |
| Логика | `rag/search/company_search.py`, `prospect.py`, `rag_queries.py` |
| Тесты API | `backend/tests/api/test_search_modes_api.py` |
| Тесты unit | `backend/tests/rag/test_search_modes.py` |
| Смоук | `backend/scripts/smoke_search_modes.py` |
| Артефакт | `backend/data/artifacts/search/modes_smoke.json` |

---

## Следующий пункт MAP

**п.3 — Chroma RAG, разделение по агентам** → отдельный перепроход, см. `BACKLOG.md`.
