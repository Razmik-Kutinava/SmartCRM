# Search→RAG: авто-чанки при relevance > порога (Ф2 §4 п.1)

**PRD_MAP:** «Авто-чанки при релевантности > порога»

## Было

- `find-for-rag` возвращал сниппеты без score релевантности
- Ингест только вручную: чекбоксы → превью → сохранить
- Порог авто-пути не был в env/коде

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `rag/search/relevance.py` | score 0–100, `RAG_AUTO_RELEVANCE_THRESHOLD` (default 65) |
| `rag/auto_ingest.py` | Q&A текст → `ingest_manual_text` для eligible hits |
| `POST /api/search/auto-ingest-rag` | поиск + авто-ингест eligible |
| `find-for-rag` | `relevance`, `auto_eligible`, `relevance_threshold` на каждый hit |
| `/search` вкладка RAG | бейдж %, автовыбор, кнопка «⚡ Авто-чанки» |

## Пайплайн

```
Поиск (Brave/Serper/…) → relevance score
        ↓
score >= RAG_AUTO_RELEVANCE_THRESHOLD
        ↓
Структура Q&A (вопрос + snippet) → semantic_chunks → Chroma
```

## Env

```env
RAG_AUTO_RELEVANCE_THRESHOLD=65
```

## Команды

```bash
cd backend
python -m pytest tests/rag/test_search_relevance.py tests/rag/test_auto_ingest_rag.py tests/api/test_search_auto_ingest_api.py -q --override-ini="filterwarnings="
```

## Критерии

- [x] Score на каждом результате find-for-rag
- [x] Авто-ингест только eligible (порог из env)
- [x] UI: автовыбор + кнопка авто-чанки
- [x] pytest без live search/LLM

## Не в scope

- LLM-структурирование пар Q&A (следующий шаг / BACKLOG)
- п.414–417 §4 (факты из диалога, save everywhere, enrich cache)
- Ручной путь «Сохранить в базу» — без изменений
