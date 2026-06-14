# Email фоновый синк — acceptance (Ф2 §3 п.403)

**PRD_MAP:** «Фоновый синк входящих»

## Было

- Синхронизация только вручную: кнопка на `/email`, `POST /api/email/sync`, smoke-скрипт
- При старте uvicorn IMAP не опрашивался — «Автофона нет» (Ф1 acceptance)
- Нет API «когда был последний фоновый прогон»

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `email_sync/sync_all.py` | общая логика sync всех аккаунтов (API + фон) |
| `email_sync/background.py` | `email_poll_loop`, state в `data/email_sync_state.json` |
| `main.py` lifespan | asyncio task при `EMAIL_AUTO_SYNC_MINUTES > 0` (default 5) |
| `GET /api/email/sync/status` | интервал, enabled, last_poll |
| `.env.example` | `EMAIL_AUTO_SYNC_MINUTES` |

## .env

```env
EMAIL_AUTO_SYNC_MINUTES=5   # 0 = выкл; нужны аккаунты в БД
```

## Команды

```bash
cd backend
pytest tests/email_sync/test_background_sync.py tests/api/test_email_sync_api.py -q
curl -s http://127.0.0.1:8000/api/email/sync/status -H "X-API-Key: ..."
python scripts/smoke_email_sync.py   # ручной POST /sync (как раньше)
```

## Критерии

- [x] Фоновый цикл IMAP INBOX по интервалу env
- [x] Graceful stop при shutdown uvicorn
- [x] State last_poll без секретов
- [x] pytest без live IMAP
- [x] Ручной `POST /sync` не сломан

## Не в scope

- UI `/email` (п.404)
- Анализ/черновик/апрув (п.405–407)
- Auto-bootstrap из env при старте (п.402 — отдельный POST)
