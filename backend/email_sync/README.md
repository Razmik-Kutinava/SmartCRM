# Email Sync — синхронизация почты

| Файл | За что |
|------|--------|
| `sync.py` | IMAP INBOX, парсинг дат, repair битого импорта, `POST /sync` |

Настройки и роуты: `api/routes/email.py`, `db/models/email.py`.  
Секреты шифруются через `core/crypto.py`.
