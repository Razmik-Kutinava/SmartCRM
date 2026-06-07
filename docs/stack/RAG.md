# RAG — Система знаний

## Схема (актуальная)

```
Поисковый запрос / контекст лида
      ↓
[Brave Search API] + [Tavily] + [Serper] — веб-поиск (где вызывается из пайплайна)
      ↓
Сниппеты и документы → нормализация / фрагменты
      ↓
[Chroma] — векторизация и хранение (`backend/data/chroma_db`)
      ↓
[rag/retrieve.py] — запросы в Chroma, сборка блоков `_rag_*` для агентов
      ↓
[RAG контекст] → в промпт агента перед ответом
```

**Hermes** здесь не «парсит выдачу Google»: он выдаёт **интенты** (например `search_web`). Поиск и RAG выполняют отдельные модули (`rag/*`, API `/api/search/web`, `/api/rag/*`). Путаницы со старой схемой «Hermes фильтрует сниппеты» в документации больше нет.

## Когда агент идёт в поиск

1. Задан вопрос о конкретном клиенте/компании
2. В RAG не найдено релевантной информации
3. Маркетолог исследует нового лида
4. Стратег запрашивает актуальные данные рынка

## Chroma — векторная БД

```python
import chromadb

client = chromadb.Client()
collection = client.create_collection("smartcrm_knowledge")

# Добавить документ
collection.add(
    documents=["текст документа"],
    metadatas=[{"source": "brave_search", "lead_id": "123"}],
    ids=["doc_001"]
)

# Поиск
results = collection.query(
    query_texts=["запрос пользователя"],
    n_results=5
)
```

Персистентный клиент и пути — см. `rag/chroma_store.py`.

## Search-to-Q&A (Фаза 2)

Пайплайн пополнения RAG из веб-поиска (не дублировать сырой HTML в Chroma):

```
Brave / Tavily / Serper → сниппеты
        ↓
LLM (структурирование) → пары {question, answer, source, lead_id?}
        ↓
Фильтр релевантности (порог из Ops/env)
        ↓
Chroma.add → коллекция агента (analyst | marketer | tec | …)
```

- Ручной путь «Сохранить в базу» остаётся (Фаза 1).
- Авто-путь — только при score релевантности > порога.
- **tec:** приоритетная коллекция для PDF/спецификаций; краулинг URL вендора — Фаза 3 (`docs/product/PRD.md`).

См. `docs/modules/search.md`, `docs/product/PRD_MAP.md` (Фаза 2 → Поиск → RAG).

## Поисковики

| API | Бесплатный тариф | Для чего |
|-----|-----------------|---------|
| Brave Search | 2000 запросов/мес | Веб поиск, приватный |
| Tavily | лимиты по плану | AI-ориентированный поиск |
| Serper | лимиты по плану | Google SERP API |

---

## См. также

- Архитектура слоя: `docs/product/ARCHITECTURE.md`
- Переменные API ключей: `.env` (Brave, Tavily, Serper)
