"""
SmartCRM — FastAPI entry point
"""
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# При `cd backend && uvicorn` cwd не корень репо — явно подхватываем SmartCRM/.env
_BACKEND_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _BACKEND_DIR.parent
load_dotenv(_BACKEND_DIR / ".env")
load_dotenv(_REPO_ROOT / ".env", override=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_OPS_LOG_HANDLER = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _OPS_LOG_HANDLER
    logger.info("SmartCRM запускается...")
    _bx = (os.getenv("BITRIX24_WEBHOOK_URL") or "").strip()
    logger.info(
        "BITRIX24_WEBHOOK_URL: %s",
        "задан (импорт лидов из Битрикс24)" if _bx else "не задан — добавьте в .env в корне репозитория",
    )
    if _OPS_LOG_HANDLER is None:
        from core.ops_log_buffer import OpsLogHandler

        _OPS_LOG_HANDLER = OpsLogHandler(level=logging.WARNING)
        _OPS_LOG_HANDLER.setFormatter(logging.Formatter("%(name)s: %(message)s"))
        logging.getLogger().addHandler(_OPS_LOG_HANDLER)

    from db.session import init_db
    try:
        await init_db()
        logger.info("БД инициализирована")
    except Exception as e:
        logger.warning(f"БД недоступна — лиды не сохранятся: {e}")
    yield
    logger.info("SmartCRM останавливается")


app = FastAPI(title="SmartCRM", version="0.1.0", lifespan=lifespan)

_DEFAULT_CORS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
_cors_env = (os.getenv("SMARTCRM_CORS_ORIGINS") or "").strip()
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()] or _DEFAULT_CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Auth
from core.auth import require_api_key

# Роуты
from api.routes.voice import router as voice_router
from api.routes.leads import router as leads_router
from api.routes.tasks import router as tasks_router
from api.routes.ops import router as ops_router
from api.routes.eval_scenarios import router as eval_scenarios_router
from api.routes.training_datasets import router as training_datasets_router
from api.routes.rag import router as rag_router
from api.routes.search import router as search_router
from api.routes.email import router as email_router
from api.routes.agent_email import router as agent_email_router
from api.routes.leadgen import router as leadgen_router
from api.routes.news import router as news_router
from api.routes.usage import router as usage_router
from api.routes.tenders import router as tenders_router
from api.routes.crm import router as crm_public_router
_auth = [Depends(require_api_key)]

app.include_router(voice_router,            dependencies=_auth)
app.include_router(leads_router,            dependencies=_auth)
app.include_router(tasks_router,            dependencies=_auth)
app.include_router(ops_router,              dependencies=_auth)
app.include_router(eval_scenarios_router,   dependencies=_auth)
app.include_router(training_datasets_router,dependencies=_auth)
app.include_router(rag_router,              dependencies=_auth)
app.include_router(search_router,           dependencies=_auth)
app.include_router(email_router,            dependencies=_auth)
app.include_router(agent_email_router,      dependencies=_auth)
app.include_router(leadgen_router,          dependencies=_auth)
app.include_router(news_router,             dependencies=_auth)
app.include_router(usage_router,            dependencies=_auth)
app.include_router(tenders_router,          dependencies=_auth)
app.include_router(crm_public_router,      dependencies=_auth)


@app.middleware("http")
async def ops_http_log_middleware(request: Request, call_next):
    """Пишет каждый HTTP-запрос в буфер Ops → Логи (кроме частого опроса логов)."""
    if request.url.path.startswith("/api/ops/logs"):
        return await call_next(request)
    t0 = time.perf_counter()
    try:
        response = await call_next(request)
        dt_ms = (time.perf_counter() - t0) * 1000
        from core.ops_log_buffer import append

        append(
            "INFO",
            f"{request.method} {request.url.path} → {response.status_code} ({dt_ms:.1f} ms)",
            component="http",
            method=request.method,
            path=str(request.url.path),
            status=response.status_code,
            duration_ms=round(dt_ms, 2),
        )
        return response
    except Exception as e:
        dt_ms = (time.perf_counter() - t0) * 1000
        from core.ops_log_buffer import append

        append(
            "ERROR",
            f"{request.method} {request.url.path}: {e} ({dt_ms:.1f} ms)",
            component="http",
            path=str(request.url.path),
        )
        raise


@app.get("/health")
async def health():
    return {"status": "ok", "service": "SmartCRM"}


@app.get("/health/llm")
async def health_llm():
    from core.llm import health_check
    return await health_check()



@app.get("/health/ollama")
async def health_ollama():
    import httpx
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{ollama_host}/api/tags")
            models = [m["name"] for m in r.json().get("models", [])]
            return {"status": "ok", "models": models}
    except Exception:
        # Не утекаем внутренние детали (URLs, пути) во внешний health-эндпоинт.
        logger.exception("health/ollama failed")
        return {"status": "error", "detail": "ollama unavailable"}
