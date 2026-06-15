# Email Sync — синхронизация почты

| Файл | За что |
|------|--------|
| `sync.py` | IMAP INBOX, парсинг дат, repair битого импорта |
| `sync_all.py` | Sync всех аккаунтов (API + фон) |
| `background.py` | Фоновый poll loop, nurture steps, `EMAIL_AUTO_SYNC_MINUTES` |
| `../services/email_lead_match.py` | Ф3: линковка лида по email/домену |
| `../services/email_faq_autoreply.py` | Ф3: автоответ FAQ после sync |
| `../services/email_nurture.py` | Ф3: цепочки 20 касаний |

Настройки и роуты: `api/routes/email.py`, `db/models/email.py`.  
Секреты шифруются через `core/crypto.py`.
