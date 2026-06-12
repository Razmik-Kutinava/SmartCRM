# Quality gates агентов — acceptance (2026-06-12)

> **`[x]` в PRD_MAP** — только когда в таблице ниже все строки **✅** после **live** прогона Ollama.  
> Карта обучения: [`AGENTS_LEARNING_MAP.md`](AGENTS_LEARNING_MAP.md).

---

## Пороги (зафиксировано)

| Агент | Метрика | Порог | N кейсов | Модель eval |
|-------|---------|-------|----------|-------------|
| Hermes (parse) | intent pass rate | **≥ 85%** | **30** | Ollama `hermes3` |
| Analyst | ключевые фразы / no-hallucination | **≥ 75%** | **15** | Ollama |
| Economist | то же | **≥ 75%** | **15** | Ollama |
| Marketer | то же | **≥ 75%** | **15** | Ollama |
| Strategist | то же | **≥ 75%** | **15** | Ollama |
| Tech (`tech_specialist`) | то же | **≥ 75%** | **15** | Ollama |

**Pass** = кейс совпал с эталоном (intent для Hermes; для агентов — обязательные подстроки / отсутствие запрещённых паттернов).  
**Warn** = порог −5 п.п. **Fail** = ниже warn.

---

## Статус прогона (обновлять после live gate)

| Агент | Pass | Fail | Pass rate | Порог | Gate | Дата | Артефакт |
|-------|------|------|-----------|-------|------|------|----------|
| Hermes | — | — | — | 85% | 🔲 | — | — |
| Analyst | — | — | — | 75% | 🔲 | — | — |
| Economist | — | — | — | 75% | 🔲 | — | — |
| Marketer | — | — | — | 75% | 🔲 | — | — |
| Strategist | — | — | — | 75% | 🔲 | — | — |
| Tech | — | — | — | 75% | 🔲 | — | — |

*Пока нет live-прогона — инфра и рамка в шаге 0–1 (2026-06-12).*

---

## Команды (целевые, шаг 3+)

```bash
# Ollama
ollama serve
ollama pull hermes3

cd backend
# Hermes только (уже есть)
python scripts/run_eval_hermes3_inline.py

# Все 6 агентов — один отчёт (шаг 3)
python scripts/run_agents_quality_gate.py
# → backend/data/artifacts/eval/agents_gate_YYYYMMDD.json
```

**UI:** `/ops/intents/eval` (фильтр по агенту — шаг 5).  
**API (шаг 3):** `POST /api/ops/eval/agents-gate`.

---

## Что сделано в шаге 0–1

- [x] Пороги X% и N на агента (таблица выше)
- [x] Цикл обучения: `AGENTS_LEARNING_MAP.md`
- [x] Решение: eval через **Ollama**, не Groq
- [ ] Eval-кейсы ≥N на агента (Hermes: 36 в `cases.jsonl`, порог 30 — ок по количеству)
- [ ] Скрипт `run_agents_quality_gate.py`
- [ ] Live-прогон + JSON-артефакт
- [ ] UI фильтр / failed → датасет
- [ ] `[x]` в PRD_MAP

---

## Hermes baseline (без gate)

- Детерминированный rescue/fastpath: `tests/core/test_hermes_lead_rescue.py`, `smoke_hermes_leads.py`
- LLM eval: `eval/cases.jsonl` (36 кейсов), `pytest -m live_eval`

---

## CI

- Hermes CPU — в pytest (CI зелёный)
- **LLM gate — не в CI** (Ollama, долго, flaky); отдельная команда + артефакт в `data/artifacts/eval/`
