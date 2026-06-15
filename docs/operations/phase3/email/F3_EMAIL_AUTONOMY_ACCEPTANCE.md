# Ф3 Email — автономия

**PRD_MAP:** Фаза 3 → Email (4 пункта).

## Критерии

| # | Пункт | Проверка |
|---|-------|----------|
| 1 | FAQ auto-reply по Ops | `AgentEmailIntent.auto_send` + триггеры; после IMAP sync → `try_faq_autoreply` |
| 2 | Рассылки по сегменту | `POST /api/email/campaigns` с `segment`; UI `/email` campaigns |
| 3 | 20 касаний автономно | `POST /api/email/nurture/start`; фон `process_due_nurture_steps` |
| 4 | Автолинк по домену | `find_lead_for_email` domain; `POST /api/email/relink-orphans` |

## Автотесты

```bash
cd backend
python -m pytest tests/email/test_email_f3.py tests/api/test_email_sync_api.py -q
```

## ENV

- `EMAIL_FAQ_AUTOREPLY=1` (default) — вкл FAQ
- `EMAIL_FAQ_MAX_PER_DAY=50` — лимит автоответов/день

## Ops UI

- `/ops/email-agents` — правила FAQ + toggle автоответ
- `/ops/email` — nurture chains + relink

## Live smoke (2026-06-15)

| Шаг | Команда | Результат |
|-----|---------|-----------|
| Connect | `python scripts/smoke_email_connect.py` | **ib@agneko.com** OK `imported=1 total=50`; **me@agneko.am** FAIL HTTP 400 (синк/креды) |
| IMAP sync | `python scripts/smoke_email_sync.py` | OK `imported=0 updated=50 total=50` account id=2 |
| SMTP send | `python scripts/smoke_email_smtp_send.py` | OK self-send → thread 512, message outbound |
| Relink | `POST /api/email/relink-orphans` | timeout >60s на полной БД — отдельно не блокер IMAP/SMTP |
| FAQ live | — | не гоняли (нет входящего с триггером в этом прогоне) |

Backend: `uvicorn` :8000, фоновый auto-sync `imported=0 total=50` в логах.

## Коммит

См. SESSION_STATE.
