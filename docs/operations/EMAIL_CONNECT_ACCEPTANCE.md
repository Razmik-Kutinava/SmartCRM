# Email connect — acceptance (2026-06-11)

PRD_MAP: **Инфра dev п.5** · live connect **частично** (ib ✅, me@ — отдельный пароль/сервер).

## .env (корень репо, не коммитить)

```env
EMAIL_APP_PASSWORD=...          # пароль приложения Яндекс
EMAIL_IMAP_HOST=imap.yandex.com
EMAIL_SMTP_HOST=smtp.yandex.com
EMAIL_IMAP_FETCH_LIMIT=50       # первая синхронизация быстрее
EMAIL_ACCOUNT_2_USER=ib@agneko.com
EMAIL_ACCOUNT_1_USER=me@agneko.am
EMAIL_ACCOUNT_1_IMAP_HOST=mail.agneko.am
```

`SMARTCRM_API_KEY` = тот же, что `PUBLIC_SMARTCRM_API_KEY` в `frontend/.env`.

## Команды

```bash
cd backend
python scripts/smoke_email_connect.py              # оба аккаунта из .env
EMAIL_CONNECT_ONLY=2 python scripts/smoke_email_connect.py   # только ib
pytest tests/email_sync/test_fetch_imap_mock.py -q
```

## Закрыто

| # | Проверка | Статус |
|---|----------|--------|
| 1 | `emailStorage.js` → `apiFetch` (X-API-Key) | ✅ |
| 2 | `ib@agneko.com` + `imap.yandex.com` | ✅ API + UI 504 тредов |
| 3 | DevTools `/email` — входящие, письма | ✅ |
| 4 | Unit IMAP mock | ✅ `test_fetch_imap_mock.py` |

## Хвост

| Пункт | Действие |
|-------|----------|
| `me@agneko.am` | `mail.agneko.am` — нужен **свой** пароль приложения в `.env` |
| Рассылки / UX | Ф2 — «криво работает», чинить отдельно |
| `test_email_sync.py` live | только `EMAIL_SYNC_LIVE=1` |
