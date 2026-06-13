# Тендеры baseline — acceptance (2026-06-11)

PRD_MAP: **«Тендеры `/tenders`»** · Ф1 baseline **закрыт**.

## Команда

```bash
cd backend && python scripts/smoke_tenders_baseline.py
```

## Закрыто

| # | Пункт | Проверка |
|---|--------|----------|
| 1 | UI + API | `/tenders`, `/api/tenders/*` |
| 2 | Поиск + Gosplan tail | бейдж «без совпадения», баннер, кнопка «Скрыть» |
| 3 | Планы | `GET /api/tenders/plans/search` |
| 4 | Мои / Архив | `tender_saved`, `GET/POST/PATCH /api/tenders/saved` |
| 5 | Serper + Tavily | `web_search.py` в `/search`, `sources.serper/tavily` |
| 6 | Лимиты Ops | `/api/usage/stats` |
| 7 | Агенты | `POST /api/tenders/analyze` (LLM), сохранение анализа в БД |
| 8 | PDF/DOCX → текст | `POST /api/tenders/documents/extract` · UI → `document_text` в analyze |

## PDF extract — ручная проверка (live API)

**Ключ:** `SMARTCRM_API_KEY` в **корневом** `SmartCRM/.env` (не `backend/.env`).  
**Фикстура:** `backend/tests/fixtures/tenders/sample_tz.pdf` — путь относительно **корня репо**.

### Автомат (рекомендуется)

```bash
cd backend && python scripts/smoke_tender_pdf_extract.py
```

Входит в `smoke_tenders_baseline.py` после pytest, если API на `:8000` и ключ задан.

### PowerShell (из корня репо)

```powershell
cd C:\Tools\workarea\SmartCRM
$key = ((Get-Content .env | Select-String '^SMARTCRM_API_KEY=').Line -split '=',2)[1].Trim()
curl.exe -X POST "http://127.0.0.1:8000/api/tenders/documents/extract" `
  -H "X-API-Key: $key" `
  -F "file=@backend/tests/fixtures/tenders/sample_tz.pdf"
```

Ожидание: `{"ok":true,"text":"SMARTCRM_TZ_MARKER_44FZ","chars":23,...}`

**Частые ошибки:** `Unauthorized` — пустой `$key` (читали `.env` из `backend\`); `curl: (26)` — неверный путь к PDF (из `backend\` нужно `@tests/fixtures/...`, не `@backend/tests/...`). В PowerShell **не** использовать `^` для переноса (это cmd) — обратная кавычка `` ` `` или одна строка.

## Live (нужны ключи)

- `TENDERGURU_API_KEY`, `GROQ_API_KEY` — поиск и анализ
- `SERPER_API_KEY`, `TAVILY_API_KEY` — веб-результаты в выдаче
- `DATANEWTON_API_KEY` — обогащение заказчика (опц.)

## Опционально позже

- Ф2 §7: голосовые команды по тендерам
- Платный API Контур (gate по сделке)
