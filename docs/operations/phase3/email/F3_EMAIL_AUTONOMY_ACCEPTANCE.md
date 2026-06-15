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

## Live smoke (2026-06-15, полный прогон)

| Шаг | Команда | Результат |
|-----|---------|-----------|
| Connect me@ | `EMAIL_CONNECT_ONLY=1 python scripts/smoke_email_connect.py` | **OK** `imported=50` — `imap.yandex.com` |
| Connect ib@ | `EMAIL_CONNECT_ONLY=2 python scripts/smoke_email_connect.py` | **OK** `total=50` |
| me@ SMTP live | `python scripts/smoke_email_faq_live.py` | **OK** self-send me@ |
| FAQ live | `python scripts/smoke_email_faq_live.py` | **OK** ib@→me@ «прайс» → sync `faq_autoreplies=1` + outbound `faq_auto` |
| IMAP sync | `python scripts/smoke_email_sync.py` | OK |
| SMTP ib@ | `python scripts/smoke_email_smtp_send.py` | OK |
| Relink | `POST /api/email/relink-orphans?limit=100` | OK `scanned=100` |
| DevTools UI | `/email`, `/ops/email`, `/ops/email-agents` | OK: треды «прайс», Relink, FAQ-правила |

Backend: `uvicorn` :8000, фоновый auto-sync `imported=0 total=50` в логах.

## Коммит

См. SESSION_STATE.
