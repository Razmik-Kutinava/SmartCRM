# Email IMAP/SMTP из .env — acceptance (Ф2 §3 п.402)

**PRD_MAP:** «IMAP/SMTP, credentials в env»

## Было

- Переменные `EMAIL_*` были в `.env.example` и smoke-скрипте, но без единого модуля и API
- Нельзя было проверить «настроена ли почта из env» без чтения `.env`
- Bootstrap только через ручной `smoke_email_connect.py` или UI connect с телом JSON

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `core/email_config.py` | `load_accounts_from_env`, `email_env_status` — IMAP/SMTP из env |
| `services/email_bootstrap.py` | upsert + `bootstrap_accounts_from_env` |
| `GET /api/email/config/status` | пароль настроен?, ящики в env/БД, без секретов |
| `POST /api/email/bootstrap-from-env` | все `EMAIL_ACCOUNT_*` → БД (+ опция `sync: false`) |
| `smoke_email_connect.py` | использует `core.email_config` |
| `.env.example` | комментарии к bootstrap/status |

## .env (корень, не коммитить)

```env
EMAIL_APP_PASSWORD=...
EMAIL_IMAP_HOST=imap.yandex.com
EMAIL_SMTP_HOST=smtp.yandex.com
EMAIL_ACCOUNT_1_USER=you@yandex.ru
EMAIL_ACCOUNT_2_USER=ib@example.com
```

## Команды

```bash
cd backend
pytest tests/api/test_email_env_config.py tests/api/test_email_sync_api.py tests/email_sync/ -q
curl -s http://127.0.0.1:8000/api/email/config/status -H "X-API-Key: ..."
curl -X POST http://127.0.0.1:8000/api/email/bootstrap-from-env -H "Content-Type: application/json" -d '{"sync":false}'
python scripts/smoke_email_connect.py   # live, если .env заполнен
```

## Критерии

- [x] IMAP/SMTP хосты/порты и пароль — из env
- [x] API status без утечки пароля
- [x] Bootstrap из env в БД (шифрование через `core/crypto`)
- [x] pytest без live IMAP
- [x] Smoke-скрипт на общем конфиге

## Не в scope (следующие пункты MAP)

- Фоновый синк (п.403)
- UI `/email` (п.404)
- Черновик/апрув (п.405–407)
