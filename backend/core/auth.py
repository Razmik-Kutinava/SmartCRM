"""
Простая аутентификация через API-ключ (X-API-Key header).

Поведение:
  - SMARTCRM_API_KEY не задан → auth отключён, запросы проходят без проверки (dev mode)
  - SMARTCRM_API_KEY задан    → требует заголовок X-API-Key с правильным значением

Для включения: добавьте в .env
  SMARTCRM_API_KEY=ваш-секретный-ключ
"""
import os
import logging
from fastapi import Header, HTTPException, Request
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("SMARTCRM_API_KEY", "").strip()

if _API_KEY:
    logger.info("Auth: API-ключ активен (X-API-Key)")
else:
    logger.warning("Auth: SMARTCRM_API_KEY не задан — API открыт (dev mode)")

_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(x_api_key: str = Header(default=None, alias="X-API-Key")):
    """
    FastAPI dependency. Добавь в router:
      dependencies=[Depends(require_api_key)]
    """
    if not _API_KEY:
        return  # dev mode — пропускаем
    if x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
