# Coverage baseline (pytest-cov)

**Дата замера:** 2026-06-11  
**Baseline:** **51.4%** (line coverage, `TOTAL` в отчёте)

## Команда

```bash
cd backend
python -m venv .venv && .\.venv\Scripts\Activate.ps1   # Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest --cov=. --cov-config=.coveragerc --cov-report=term-missing
```

Источники: `api`, `core`, `agents`, `db`, `services`, `email_sync`, `leadgen`, `rag`, `integrations`, `voice`.  
Исключено: `tests/*`, `scripts/*`, `*/__init__.py` (см. `backend/.coveragerc`).

## Ориентиры по фазам (не gate)

| Фаза | Цель | Статус |
|------|------|--------|
| Ф2 старт | soft ~40% | ✅ 51.4% (выше) |
| Ф2 конец | ~60% | 🔲 |
| Ф3 | ~75% | 🔲 |

Порог **не блокирует** закрытие фазы — только ориентир для приоритизации тестов.

## Примечания

- Регрессия по умолчанию: `python -m pytest` (без `live_eval`; см. `pytest.ini`).
- Live LLM eval: `python -m pytest -m live_eval tests/core/test_hermes_eval.py`.
- `cryptography` обязателен (`core/crypto.py`) — в `requirements.txt`.
- CI с `--cov` и fail-under — отдельный шаг (PRD_MAP).

## История

| Дата | % | Коммит | Комментарий |
|------|---|--------|-------------|
| 2026-06-11 | 51.4% | `878e159` | Первый baseline: pytest-cov, requirements-dev, .coveragerc |
