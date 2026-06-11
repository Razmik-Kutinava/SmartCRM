# Email Sync — синхронизация почты

| Файл | За что |
|------|--------|
| `sync.py` | IMAP: чтение входящих, привязка к лидам; лимит `EMAIL_IMAP_FETCH_LIMIT` (default 100) |

Настройки и роуты: `api/routes/email.py`, `db/models/email.py`.  
Секреты шифруются через `core/crypto.py`.
