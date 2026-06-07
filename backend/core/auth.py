"""
Простая аутентификация через API-ключ (X-API-Key header).

Поведение:
  - SMARTCRM_API_KEY не задан → auth отключён, запросы проходят без проверки (dev mode)
  - SMARTCRM_API_KEY задан    → требует заголовок X-API-Key с правильным значением

Для включения: добавьте в .env
  SMARTCRM_API_KEY=ваш-секретный-ключ
"""
import os
import hmac
import logging
from fastapi import Header, HTTPException, Request
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("SMARTCRM_API_KEY", "").strip()
_REQUIRE_AUTH = os.getenv("SMARTCRM_REQUIRE_AUTH", "").strip().lower() in ("1", "true", "yes")

if _API_KEY:
    logger.info("Auth: API-ключ активен (X-API-Key)")
else:
    if _REQUIRE_AUTH:
        # Production mode: запрет старта без ключа.
        raise RuntimeError(
            "SMARTCRM_REQUIRE_AUTH=1, но SMARTCRM_API_KEY не задан. "
            "Задайте SMARTCRM_API_KEY в .env или отключите SMARTCRM_REQUIRE_AUTH."
        )
    logger.warning("Auth: SMARTCRM_API_KEY не задан — API открыт (dev mode)")

_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(x_api_key: str = Header(default=None, alias="X-API-Key")):
    """
    FastAPI dependency. Добавь в router:
      dependencies=[Depends(require_api_key)]
    """
    if not _API_KEY:
        return  # dev mode — пропускаем
    # Защита от timing-attack: постоянное время сравнения
    if not hmac.compare_digest((x_api_key or "").encode("utf-8"), _API_KEY.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Unauthorized")
