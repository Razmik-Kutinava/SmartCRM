# CI baseline (GitHub Actions)

**Workflow:** `.github/workflows/ci.yml`  
**Коммит:** `0477431`  
**Триггер:** `push` и `pull_request` на `main`.

## Jobs

| Job | Что | БД |
|-----|-----|-----|
| **pytest** | Полная регрессия + **cov в логе** (`--cov-report=term`, без fail-under) | sqlite in-memory (`conftest`) |
| **smoke** | `python scripts/ci_smoke.py` — ops, leads, voice | то же |

Live Groq, IMAP (`EMAIL_SYNC_LIVE`), Bitrix webhook, frontend DevTools — **не** в CI.

**`14 deselected`** в отчёте pytest — норма: маркер `live_eval` (Groq). Не в CI, локально: `python -m pytest -m live_eval`.

## Локально

```bash
cd backend
python -m venv .venv && .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q --tb=short
python scripts/ci_smoke.py
```

## CI env (без `.env`)

В workflow явно: `HERMES_ENABLE_FASTPATH=0` — как на GitHub Actions без локального `.env` (иначе rescue/fastpath расходятся с dev).

## Branch protection

Required checks на `main`:

- `pytest (sqlite)`
- `smoke (ops / leads / voice)`

**Статус (2026-06-12):** включено на `main` через API — `strict: true`, оба check обязательны. Падение любого job → красный PR / блок merge.
