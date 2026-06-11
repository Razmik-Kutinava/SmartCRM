# Backend SmartCRM

Python-сервер на FastAPI. Всё, что делает API, AI, лиды, тендеры и голос — здесь.

## С чего начать

```bash
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

Тесты: `python -m pytest -q` (не голый `pytest` — на Windows может не быть в PATH).

Переменные окружения — в корне репо: `.env.example` → `.env`.

## Карта папок

| Папка | Простыми словами |
|-------|------------------|
| [`main.py`](main.py) | Старт сервера, подключение роутов, CORS, lifespan |
| [`api/`](api/README.md) | HTTP-эндпоинты для фронта |
| [`core/`](core/README.md) | Ядро: LLM, Hermes, auth, CRM-логика, ops |
| [`agents/`](agents/README.md) | AI-агенты (маркетолог, экономист, оркестратор) |
| [`leadgen/`](leadgen/README.md) | Пайплайн лидогенерации и внешние источники |
| [`rag/`](rag/README.md) | База знаний: Chroma, веб-поиск, ingest |
| [`db/`](db/README.md) | PostgreSQL: модели и сессия |
| [`services/`](services/README.md) | Клиенты внешних API тендеров |
| [`voice/`](voice/README.md) | Голос: Whisper + связка с Hermes |
| [`email_sync/`](email_sync/README.md) | Синхронизация почты IMAP/SMTP |
| [`integrations/`](integrations/README.md) | Битрикс24 |
| [`scripts/`](scripts/README.md) | CLI: бенчмарки, seed, eval (не pytest) |
| [`tests/`](tests/README.md) | Автотесты |
| [`data/`](data/README.md) | Кэши, JSON-артефакты, runtime-файлы |

## Файлы в корне `backend/`

| Файл | За что |
|------|--------|
| `requirements.txt` | Зависимости Python |
| `requirements-dev.txt` | pytest, pytest-cov, aiosqlite (тесты) |
| `pytest.ini` | Настройки pytest (+ маркер `live_eval`) |
| `.coveragerc` | Источники coverage (без tests/scripts) |
| `eval_benchmark_data.py` | Данные для eval-бенчмарков Hermes |

## Поток запроса (упрощённо)

```
Фронт → api/routes/* → core / agents / leadgen / db
Голос → voice/pipeline → core/hermes → agents/orchestrator → leadgen/pipeline
```

Подробнее по зонам — README в каждой папке.
