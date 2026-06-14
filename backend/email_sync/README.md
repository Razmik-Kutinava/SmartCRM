# Email Sync — синхронизация почты

| Файл | За что |
|------|--------|
| `sync.py` | IMAP INBOX, парсинг дат, repair битого импорта |
| `sync_all.py` | Sync всех аккаунтов (API + фон) |
| `background.py` | Фоновый poll loop, `EMAIL_AUTO_SYNC_MINUTES`, state file |

Настройки и роуты: `api/routes/email.py`, `db/models/email.py`.  
Секреты шифруются через `core/crypto.py`.
