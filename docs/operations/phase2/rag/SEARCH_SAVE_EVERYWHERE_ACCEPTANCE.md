# Search: «Сохранить в базу» везде (Ф2 §4 п.3)

**PRD_MAP:** «Сохранить в базу» везде в поиске

## Было

- Кнопка «✓ Сохранить в базу» только на вкладке **Поиск для RAG**
- company / free / prospect / enrich / agent — результаты без пути в Chroma

## Стало

| Вкладка | `data-testid` | Источник документов |
|---------|---------------|---------------------|
| Поиск по компании | `search-company-save-rag` | `raw_results` |
| Свободный запрос | `search-free-save-rag` | AI-ответ + `raw_results` |
| Проспектинг | `search-prospect-save-rag` | карточки компаний ICP |
| Обогащение лида | `search-enrich-save-rag` | `enriched` + `raw_results` |
| Задача агенту | `search-agent-save-rag` | ответ агента + источники |
| Поиск для RAG | `search-rag-save` (как было) | полный flow с превью |

Общий UI: `SearchSaveRagBar.svelte` → `POST /api/rag/ingest-batch`

## Команды

```bash
cd backend
python -m pytest tests/rag/test_search_hits.py tests/api/test_rag_ingest_batch_api.py -q --override-ini="filterwarnings="
python scripts/smoke_rag_save_from_search.py
```

## Критерии

- [x] Бар «Сохранить в базу» на 5 вкладках (кроме RAG — свой flow)
- [x] Выбор агента-получателя + превью + save
- [x] `source_url` через ingest-batch metadata
- [x] pytest search_hits + ingest-batch

## Не в scope

- п.4 кэш enrich
- Полный fetch страницы по URL
