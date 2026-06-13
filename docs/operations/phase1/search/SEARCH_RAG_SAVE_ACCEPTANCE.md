# «Сохранить в базу» из `/search` — acceptance (2026-06-08)

PRD_MAP: **«Поиск и RAG (базово)» п.5**

## Команда

```bash
cd backend && python scripts/smoke_rag_save_from_search.py
```

6 pytest + probe фронта `/search`.

---

## Было → стало (простыми словами)

| Было | Стало |
|------|--------|
| `ingest-batch` сохранял только `title` — **URL источника терялся** в метаданных чанков | `source` → `source_url` в Chroma; URL дублируется в тексте чанка |
| `total_chunks` в ответе только при `dry_run` | `total_chunks` всегда (preview и реальный save) |
| Кнопка «Загрузить в RAG», без testid | **«✓ Сохранить в базу»** + `search-rag-preview`, `search-rag-save` |
| Нет тестов ingest-batch | **6 pytest** dry_run → save → query + metadata |
| Нет смоука и acceptance | `smoke_rag_save_from_search.py` + этот документ |

---

## ✅ СДЕЛАНО и ПРОВЕРЕНО

| # | Шаг | API | UI `/search` таб RAG | Тест |
|---|-----|-----|----------------------|------|
| 1 | Поиск материалов | `POST /api/search/find-for-rag` | запрос + «Найти материалы» | live DevTools 12 результатов |
| 2 | Выбор + превью | `POST /api/rag/ingest-batch` `dry_run: true` | «Посмотреть чанки» | pytest + DevTools 1 чанк |
| 3 | Сохранение | `ingest-batch` `dry_run: false` | **«✓ Сохранить в базу»** | pytest + DevTools |
| 4 | Метаданные для агентов | `source_url` в hits | URL в тексте «Источник: …» | pytest `test_ingest_batch_save_and_query_with_source_url` |
| 5 | Фильтр агента | `for_agent` в batch | combobox агент-получатель | pytest agent_filter |

**DevTools (`localhost:5173/search`, таб «Поиск для RAG»):**

| Проверка | Результат |
|----------|-----------|
| Запрос «ключевая ставка ЦБ инфляция 2025» → 12 результатов | ✅ |
| Выбор 1 док → превью 1 чанк с `Источник: https://www.cbr.ru/...` | ✅ |
| «✓ Сохранить в базу» → «Загружено 1 документов · 1 чанков → RAG (агент: all)» | ✅ |
| Шаг 3 «Загружено» | ✅ |

---

## ❌ НЕ СДАЛИ (следующий scope)

| Что | Куда |
|-----|------|
| Смоук enrich-lead live E2E | MAP / `BACKLOG.md` |
| Авто-чанки из поиска/диалога без ручного approve | **Фаза 2** |
| Полный fetch страницы по URL (сейчас title+snippet) | улучшение, не блокер п.5 |
| Миграция Chroma → pgvector | `BACKLOG.md` инфра |

---

## Файлы

| Зона | Путь |
|------|------|
| Ингест + metadata | `backend/rag/ingest.py` (`_metadata_from_search_doc`) |
| API batch | `backend/api/routes/rag.py` |
| UI flow | `frontend/src/routes/search/+page.svelte` |
| Тесты | `tests/api/test_rag_ingest_batch_api.py`, `tests/rag/test_rag_ingest_batch.py` |
| Смоук | `backend/scripts/smoke_rag_save_from_search.py` |

---

## Следующий пункт

Блок **«Поиск и RAG (базово)» п.1–5 закрыт** → enrich-lead smoke или **Фаза 2** (авто-чанки).
