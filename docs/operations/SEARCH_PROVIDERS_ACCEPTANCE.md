# Поисковики Serper + Brave + Tavily — acceptance (2026-06-08)

PRD_MAP: **«Поиск и RAG (базово)» п.1**

## Команда

```bash
cd backend && python scripts/smoke_search_providers.py
```

pytest (моки) + опционально live при ключах в `.env`.

## Покрытие

| Зона | Файлы |
|------|--------|
| Провайдеры (моки httpx) | `tests/rag/test_search_providers.py` |
| Конфиг / кэш | `tests/rag/test_search_pkg.py` |
| API `/api/search/*` | `tests/api/test_search_providers_api.py` |

## Исправления в шаге

- `rag/search/company_search.py` — импорт `_cache_key/_cache_get/_cache_set` (без этого `/run` падал с NameError)

## DevTools (`localhost:5174/search`)

| Проверка | Результат |
|----------|-----------|
| `GET /api/search/providers` (через Vite proxy) | ✅ serper/brave/tavily `key_set: true` |
| UI бейджи Google/Brave/Tavily | ✅ ✓ в шапке |
| `POST /api/search/run` «Сбербанк» | ✅ `providers_used: [serper, brave, tavily]`, 7 результатов |

## Env

| Переменная | Провайдер |
|------------|-----------|
| `SERPER_API_KEY` | Google (Serper) |
| `BRAVE_API_KEY` | Brave Search |
| `TAVILY_API_KEY` | Tavily AI |

Опционально для фронта при auth: `PUBLIC_SMARTCRM_API_KEY` + Vite proxy (см. `frontend/vite.config.js`).

## Следующий пункт MAP

**п.2 — 6 режимов поиска** (отдельный перепроход).
