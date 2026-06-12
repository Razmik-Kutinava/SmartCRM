# CI baseline (GitHub Actions)

**Workflow:** `.github/workflows/ci.yml`  
**Коммит:** `0477431`  
**Триггер:** `push` и `pull_request` на `main`.

## Jobs

| Job | Что | БД |
|-----|-----|-----|
| **pytest** | Полная регрессия (`pytest -q`), без `live_eval` | sqlite in-memory (`conftest`) |
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

## Branch protection (ручная настройка в GitHub)

Settings → Branches → `main` → Require status checks:

- `pytest (sqlite)`
- `smoke (ops / leads / voice)`

Падение любого job → красный PR (не только ai-review).
