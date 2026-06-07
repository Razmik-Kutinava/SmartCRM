# Security Audit — апрель 2026

## Что нашли → как исправили

| # | Проблема | Файл | Решение | Статус |
|---|----------|------|---------|--------|
| 1 | Нет auth на всех эндпоинтах | `main.py` | `core/auth.py` — X-API-Key, dev-mode без ключа; Vite proxy добавляет ключ автоматически | ✅ |
| 2 | `/debug/hermes` в продакшене | `main.py` | Удалён | ✅ |
| 3 | SMTP пароли plaintext в БД | `email.py`, `sync.py` | `core/crypto.py` — Fernet шифрование, legacy fallback | ✅ |
| 4 | `str(e)` в 500-ках — утечка внутренностей | все routes | generic message + `logger.exception` | ✅ |
| 5 | Нет лимита файла `/api/voice/transcribe` | `voice.py` | Лимит 10 МБ | ✅ |

## Переменные окружения (добавить в `.env`)

```
SMARTCRM_API_KEY=<случайный ключ>   # auth
SECRET_KEY=<fernet ключ>            # шифрование паролей
```

Сгенерировать:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Что осталось (не критично)

- Rate limiting на `/api/leadgen/analyze` (slowapi)
- `SaveRequest: card: dict` — заменить на типизированную схему
- `DATABASE_URL` — убрать дефолтный пароль в коде
- Unbounded кэши: `_user_cache` в bitrix24.py, `_portrait_review_cache` в pipeline.py
