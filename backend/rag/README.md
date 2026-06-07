# RAG — база знаний и поиск

ChromaDB, загрузка документов, гибридный поиск (вектор + веб).

---

## Пакет `search/` — поиск компаний и prospect

| Файл | За что |
|------|--------|
| `providers.py` | Tavily, Brave, Exa и др. |
| `merge.py` | Слияние результатов источников |
| `company_search.py` | Поиск компании по запросу |
| `prospect.py` | Поиск prospect-лидов |
| `rag_queries.py` | Запросы к Chroma |
| `cache.py` | Кэш поиска |
| `config.py` | Ключи и лимиты |

Старый монолит `search.py` в корне `rag/` — shim/re-export для совместимости.

---

## Файлы в корне `rag/`

| Файл | За что |
|------|--------|
| `chroma_store.py` | Работа с ChromaDB |
| `chroma.py` | Низкоуровневый клиент |
| `ingest.py` | Загрузка документов в индекс |
| `retrieve.py` | Получение чанков по запросу |
| `chunking.py` | Разбиение текста на чанки |
| `parsers.py` | Парсинг PDF/HTML для ingest |

Эндпоинты: `api/routes/rag.py`, `api/routes/search.py`.
