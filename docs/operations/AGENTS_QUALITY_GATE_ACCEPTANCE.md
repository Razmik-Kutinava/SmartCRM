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

<!-- GATE_STATUS_START -->
| Агент | Pass | Fail | Pass rate | Порог | Gate | Дата | Артефакт |
|-------|------|------|-----------|-------|------|------|----------|
| Hermes | 0 | 2* | 0%* | 85% | 🔴 | 2026-06-12 | smoke `agents_gate_20260612_154027.json` |
| Analyst | 0 | 1* | 0%* | 75% | 🔴 | 2026-06-12 | smoke |
| Economist | 0 | 1* | 0%* | 75% | 🔴 | 2026-06-12 | smoke |
| Marketer | 0 | 1* | 0%* | 75% | 🔴 | 2026-06-12 | smoke |
| Strategist | 0 | 1* | 0%* | 75% | 🔴 | 2026-06-12 | smoke |
| Tech | 0 | 1* | 0%* | 75% | 🔴 | 2026-06-12 | smoke |
<!-- GATE_STATUS_END -->

Автообновление: `python scripts/run_agents_quality_gate.py --write-acceptance`

## Дыры (блокеры `[x]` в MAP)

<!-- GATE_GAPS_START -->
- **Hermes**: ReadTimeout на CPU @600–900s — полный прогон 36 кейсов не завершён
- **5 агентов**: фоновый `--agents-only` оборвался на analyst (Ollama timeout/ошибка) — артефакт не обновлён
- **MAP `[x]`** — не ставить, пока `overall_gate` ≠ pass
- **UI ✅** — смотреть цифры: `/ops/intents/eval`, дыры: `/ops/insights`
<!-- GATE_GAPS_END -->

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

**UI:** `/ops/intents/eval` → вкладка **Quality gate** (Hermes eval — отдельная вкладка).  
**API:** `GET .../latest/download`, `POST .../ensure-dataset`, `POST .../failed-to-dataset/bulk`, `POST .../run` (режимы/лимиты).

---

## Eval-кейсы (шаг 2, 2026-06-12)

| Агент | Файл | N | Эталоны |
|-------|------|---|---------|
| Hermes | `eval/cases.jsonl` | **36** | intent + slots |
| Analyst | `eval/agents/analyst.jsonl` | **15** | must_contain / must_not_contain |
| Economist | `eval/agents/economist.jsonl` | **15** | то же |
| Marketer | `eval/agents/marketer.jsonl` | **15** | то же |
| Strategist | `eval/agents/strategist.jsonl` | **15** | то же + `state_overrides` |
| Tech | `eval/agents/tech_specialist.jsonl` | **15** | то же |

Загрузка: `core.agent_eval` · smoke: `pytest tests/core/agent_eval/test_cases.py` · сид: `scripts/seed_agent_eval_cases.py`.

---

## Что сделано

- [x] Пороги X% и N на агента (таблица выше)
- [x] Цикл обучения: `AGENTS_LEARNING_MAP.md`
- [x] Решение: eval через **Ollama**, не Groq
- [x] Eval-кейсы ≥N на агента (шаг 2)
- [x] Скрипт `run_agents_quality_gate.py` + `POST /api/ops/eval/agents-gate` (шаг 3)
- [x] Acceptance sync: таблица + дыры (`acceptance_sync.py`, `--write-acceptance`)
- [x] UI `/ops/tuning` — импорт failed из gate → `eval-failed-gate` (шаг 6, 2026-06-13)
- [x] Дельта в отчёте gate: **было % → стало %** (`gate_delta.py`, карточки eval + insights)
- [ ] Полный live-прогон ≥ порогов (smoke 🔴; Hermes timeout CPU)
- [x] UI `/ops/intents/eval` — вкладки **Hermes eval** | **Quality gate**; download JSON; режимы all/hermes-only/agents-only + лимиты; bulk failed→`eval-failed-gate`; «В датасет» (2026-06-13)
- [x] `/ops/insights` — pass rate grid 6 агентов + hint без артефакта
- [ ] `[x]` в PRD_MAP (только при `overall_gate: pass`)

---

## Hermes baseline (без gate)

- Детерминированный rescue/fastpath: `tests/core/test_hermes_lead_rescue.py`, `smoke_hermes_leads.py`
- LLM eval: `eval/cases.jsonl` (36 кейсов), `pytest -m live_eval`

---

## CI

- Hermes CPU — в pytest (CI зелёный)
- **LLM gate — не в CI** (Ollama, долго, flaky); отдельная команда + артефакт в `data/artifacts/eval/`
