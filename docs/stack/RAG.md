# RAG — Система знаний

## Схема

```
Поисковый запрос
      ↓
[Brave Search API] + [Tavily AI Search] + [Serper Google]
      ↓ результаты
[Hermes] — парсит, фильтрует, оставляет релевантное
      ↓ чистый текст
[Chroma] — векторизация и сохранение
      ↓
[RAG контекст] → в промпт агента перед ответом
```

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

## Поисковики

| API | Бесплатный тариф | Для чего |
|-----|-----------------|---------|
| Brave Search | 2000 запросов/мес | Веб поиск, приватный |
| Tavily | 1000 запросов/мес | AI-оптимизированный поиск |
| Serper | 2500 запросов/мес | Google результаты |
