"""
SmartCRM — FastAPI entry point
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# При `cd backend && uvicorn` cwd не корень репо — явно подхватываем SmartCRM/.env
_BACKEND_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _BACKEND_DIR.parent
load_dotenv(_BACKEND_DIR / ".env")
load_dotenv(_REPO_ROOT / ".env", override=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SmartCRM запускается...")
    _bx = (os.getenv("BITRIX24_WEBHOOK_URL") or "").strip()
    logger.info(
        "BITRIX24_WEBHOOK_URL: %s",
        "задан (импорт лидов из Битрикс24)" if _bx else "не задан — добавьте в .env в корне репозитория",
    )
    from db.session import init_db
    try:
        await init_db()
        logger.info("БД инициализирована")
    except Exception as e:
        logger.warning(f"БД недоступна — лиды не сохранятся: {e}")
    yield
    logger.info("SmartCRM останавливается")


app = FastAPI(title="SmartCRM", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(voice_router)
app.include_router(leads_router)
app.include_router(tasks_router)
app.include_router(ops_router)
app.include_router(eval_scenarios_router)
app.include_router(training_datasets_router)
app.include_router(rag_router)
app.include_router(search_router)
app.include_router(email_router)
app.include_router(agent_email_router)
app.include_router(leadgen_router)
app.include_router(news_router)
app.include_router(usage_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "SmartCRM"}


@app.get("/health/llm")
async def health_llm():
    from core.llm import health_check
    return await health_check()


@app.get("/debug/hermes")
async def debug_hermes():
    import httpx
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    hermes_model = "qwen2.5:0.5b"
    payload = {
        "model": hermes_model,
        "messages": [{"role": "user", "content": 'Return JSON: {"intent":"create_lead","company":"ACME"}'}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
    }
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            r = await client.post(f"{ollama_host}/api/chat", json=payload)
            return {"raw": r.json()["message"]["content"], "model": hermes_model}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__, "model": hermes_model}


@app.get("/health/ollama")
async def health_ollama():
    import httpx
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{ollama_host}/api/tags")
            models = [m["name"] for m in r.json().get("models", [])]
            return {"status": "ok", "models": models}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
