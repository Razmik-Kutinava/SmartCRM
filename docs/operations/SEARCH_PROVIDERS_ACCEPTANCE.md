# Поисковики Serper + Brave + Tavily — acceptance (2026-06-08)

PRD_MAP: **«Поиск и RAG (базово)» п.1**

## Команда

```bash
cd backend && python scripts/smoke_search_providers.py
```

pytest (моки) + live probe при ключах в `.env` (скрипт грузит `backend/.env` и корневой `.env`).

## Сделано / проверено

| # | Задача | Сделано | Проверено |
|---|--------|---------|-----------|
| 1 | Провайдеры Serper / Brave / Tavily (`providers.py`) | ✅ | pytest моки httpx |
| 2 | Fanout + дедуп (`company_search.py`) | ✅ | pytest + фикс импорта кэша |
| 3 | API `/api/search/providers`, `/config`, `/run` | ✅ | `test_search_providers_api.py` |
| 4 | Кэш поиска (`cache.py`) | ✅ | `test_search_pkg.py` |
| 5 | Смоук CLI + live probe | ✅ | `smoke_search_providers.py` + `.env` |
| 6 | UI `/search` — все вызовы через `apiFetch` / `apiPost` | ✅ | DevTools (см. ниже) |
| 7 | UI: ввод компании → «Найти» → результат на экране | ✅ | DevTools `data-testid=search-company-submit` |

## Покрытие тестов

| Зона | Файлы |
|------|--------|
| Провайдеры (моки httpx) | `tests/rag/test_search_providers.py` |
| Конфиг / кэш | `tests/rag/test_search_pkg.py` |
| API `/api/search/*` | `tests/api/test_search_providers_api.py` |

## Исправления в шаге

- `rag/search/company_search.py` — импорт `_cache_key/_cache_get/_cache_set` (без этого `/run` падал с NameError)
- `frontend/src/routes/search/+page.svelte` — `fetch` → `apiFetch` / `apiPost` (providers, run, leads, rag ingest)

## DevTools (`localhost:5174/search`)

| Проверка | Результат |
|----------|-----------|
| `GET /api/search/providers` (Vite proxy + API key) | ✅ serper/brave/tavily `key_set: true` |
| UI бейджи Google/Brave/Tavily | ✅ ✓ в шапке |
| Ввод «Сбербанк» → кнопка «Найти» | ✅ чипы провайдеров + «Результатов: N» на экране |
| `POST /api/search/run` (через UI) | ✅ `providers_used: [serper, brave, tavily]` |

## Env

| Переменная | Провайдер |
|------------|-----------|
| `SERPER_API_KEY` | Google (Serper) |
| `BRAVE_API_KEY` | Brave Search |
| `TAVILY_API_KEY` | Tavily AI |
| `PUBLIC_SMARTCRM_API_KEY` | Фронт → Vite proxy (см. `frontend/vite.config.js`) |

## Следующий пункт MAP

**п.2 — 6 режимов** → `SEARCH_MODES_ACCEPTANCE.md` ✅. Дальше **п.3 Chroma RAG**.
