"""
Шифрование чувствительных данных (SMTP пароли и др.) через Fernet (AES-128-CBC).

Настройка: добавьте в .env
  SECRET_KEY=<ключ>

Сгенерировать ключ:
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Поведение:
  - SECRET_KEY не задан → используется эфемерный ключ (предупреждение в логе)
    Зашифрованные данные не переживут рестарт сервера. Только для dev.
  - SECRET_KEY задан → стабильное шифрование.

При расшифровке: если значение не является Fernet-токеном (legacy plaintext) —
возвращается как есть. Это позволяет мигрировать существующие записи без даунтайма.
"""
import os
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_raw = os.getenv("SECRET_KEY", "").strip()

if _raw:
    try:
        _fernet = Fernet(_raw.encode() if isinstance(_raw, str) else _raw)
        logger.info("Crypto: Fernet инициализирован из SECRET_KEY")
    except Exception as e:
        logger.error(
            "Crypto: SECRET_KEY невалиден (%s). "
            "Сгенерируйте ключ: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"",
            e,
        )
        _fernet = Fernet(Fernet.generate_key())
else:
    _ephemeral = Fernet.generate_key()
    _fernet = Fernet(_ephemeral)
    logger.warning(
        "Crypto: SECRET_KEY не задан — используется эфемерный ключ. "
        "Зашифрованные данные не переживут рестарт. Добавьте SECRET_KEY в .env для продакшена."
    )


def encrypt(value: str) -> str:
    """Зашифровать строку. Возвращает Fernet-токен (строка)."""
    return _fernet.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    """
    Расшифровать строку.
    Если value не является Fernet-токеном (legacy plaintext) — возвращает как есть.
    """
    try:
        return _fernet.decrypt(value.encode()).decode()
    except (InvalidToken, Exception):
        # Старая запись без шифрования — возвращаем как есть
        return value
