# Загрузка PDF/текста в `/rag` — acceptance (2026-06-08)

PRD_MAP: **«Поиск и RAG (базово)» п.4**

## Команда

```bash
cd backend && python scripts/smoke_rag_upload.py
```

8 pytest + probe фронта `/rag`.

---

## Было → стало (простыми словами)

| Было | Стало |
|------|--------|
| В MAP галочка «загрузка PDF/текста», но **без перепрохода** — не было тестов upload/preview | **8 pytest**: txt/md ingest, PDF (mock), multipart API |
| Не было смоука и acceptance | `smoke_rag_upload.py` + этот документ |
| UI загрузки был, но без `data-testid` для автопроверки | `rag-file-input`, `rag-upload-preview`, `rag-upload-submit`, `rag-text-submit` |
| Не фиксировали живые PDF в базе | DevTools: **3 PDF** в источниках (624+503+457 чанков) + ручной текст «В базу» |

---

## ✅ СДЕЛАНО и ПРОВЕРЕНО

| # | Формат | API | UI `/rag` | Тест |
|---|--------|-----|-----------|------|
| 1 | TXT / MD | `POST /api/rag/upload` | файл + предпросмотр | pytest + API |
| 2 | PDF | `upload` + `pypdf` | список источников | pytest mock + live PDF в базе |
| 3 | DOCX / XLSX / CSV / JSON | `ingest_bytes` | кнопки загрузки | код `ingest.py` (без live в CI) |
| 4 | Текст вручную | `POST /api/rag/ingest` | «В базу» | DevTools ✅ 1 чанк |
| 5 | Предпросмотр | `POST /api/rag/preview` | «Предпросмотр пайплайна» | API dry_run, без записи в Chroma |
| 6 | JSON вручную | `POST /api/rag/ingest-json` | «Загрузить JSON» | код + UI |

**DevTools (`localhost:5173/rag`):**

| Проверка | Результат |
|----------|-----------|
| Шапка 1592 чанков | ✅ |
| Источники: PDF economist (503+457), RAG pdf (624) | ✅ |
| Текст вручную → «✓ Текст добавлен: 1 чанков» | ✅ |
| Пайплайн + превью чанка на экране | ✅ |

---

## ❌ НЕ СДАЛИ (следующий пункт MAP)

| Что | Куда |
|-----|------|
| Кнопка «сохранить в базу» из `/search` | ✅ `SEARCH_RAG_SAVE_ACCEPTANCE.md` |
| Смоук enrich-lead | MAP / BACKLOG |
| Авто-чанки из поиска/диалога | **Фаза 2** |
| Live E2E загрузки PDF через file picker в DevTools | 👤 опционально (ручной клик) |

---

## Файлы

| Зона | Путь |
|------|------|
| Парсеры | `backend/rag/parsers.py` |
| Ингест | `backend/rag/ingest.py` |
| API | `backend/api/routes/rag.py` |
| UI | `frontend/src/routes/rag/+page.svelte` |
| Тесты | `tests/rag/test_rag_upload.py`, `tests/api/test_rag_upload_api.py` |
| Смоук | `backend/scripts/smoke_rag_upload.py` |

---

## Следующий пункт MAP

**п.5 закрыт** → `SEARCH_RAG_SAVE_ACCEPTANCE.md`. Дальше enrich-lead или Ф2 авто-чанки.
