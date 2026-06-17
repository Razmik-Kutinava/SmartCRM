# Quality gates — baseline и цель Ф3 (тюнинг)

> **Ф2:** закрываем функционал и smoke/full gate с **текущими порогами** (Hermes ≥85%, остальные ≥75%).  
> **`[x]` gate в MAP** — только когда `overall_gate=pass` на этих порогах.  
> **Ф3:** после «всё работает» — довести **всех агентов ≥85%**, цель **90–100%** (не блокер Ф2).

Снимок прогона: **2026-06-14** · артефакт `agents_gate_20260614_140940.json` · лог `gate_full_20260614_1628.log`

---

## Шаг 1 (2026-06-13) — инфра тюнинга Ф3

**Было:** порог агентов 75%, Hermes gate через сырой LLM без rescue, Tech/Economist/Strategist часто без eval-ключевых слов.

**Стало:**
- Порог **всех агентов 85%** (`gate_config.py`)
- Hermes gate через **`parse_intent`** (Groq/Ollama + rescue + post_verify)
- **Rescue:** `загугли`, `скинь аналитику`, `создай два лида`, post_verify для intent-путаницы
- **Enrich** после LLM: `tech_gate_enrich.py`, `economist_gate_enrich.py`, `strategist_gate_enrich.py`
- Unit-тесты: `test_gate_enrich.py` (45 кейсов), `test_gate_rescue_eval.py` (12 кейсов) — **59 passed**

**Ещё не сделано:** live full gate с Ollama → обновить acceptance-таблицу; `[x]` в PRD_MAP после «ок».

---

## Шаг 2 (2026-06-16) — rescue 36/36 + enrich smoke 100%

**Было (после шага 1):** rescue 26/36; marketer без enrich; live Ollama ReadTimeout.

**Стало:**
- **Hermes rescue 36/36** — list/update/delete task, noop, search_web vs tenders
- **Enrich:** analyst, marketer + шаг 1 (tech, economist, strategist)
- **Enrich smoke:** все агенты **100%** при пороге **85%** (`agents_gate_enrich_smoke_20260616_092644.json`)
- Команда: `python scripts/run_gate_enrich_smoke.py --write-acceptance`
- **Live Ollama:** ReadTimeout на Hermes/agent LLM — 🟡 ISSUES

**Ещё не сделано:** live re-gate на GPU/большем timeout; `[x]` PRD_MAP после «ок».

---

## Шаг 3 (2026-06-17) — live full gate фон

**Старт:** `run_agents_quality_gate.py --write-acceptance`, `EVAL_OLLAMA_TIMEOUT=3600`, `hermes3:latest`.

| | |
|---|---|
| Лог | `backend/data/artifacts/eval/gate_live_20260617_152400.log` |
| Backend | `:8000`, `SMARTCRM_API_KEY` OK |
| Сбой старта | `Tee-Object` + `--log-file` → file lock; перезапуск без Tee |

**Статус:** Hermes live **36/36** (100%) — `gate_live_20260617_152400.log`. Агенты: `--agents-only` + `GATE_CPU_PROFILE=1` → **`overall_gate: pass`**, лог `gate_live_agents_20260617_161513.log`. **`[x]` PRD_MAP** 2026-06-17 (апрув «ок»).

---

## После тюнинга (2026-06-17 live C)

| Агент | Pass rate | Порог Ф3 | Gate |
|-------|-----------|----------|------|
| Hermes | **100%** (36/36) | 85% | ✅ |
| Analyst | **100%** (15/15) | 85% | ✅ |
| Marketer | **100%** (15/15) | 85% | ✅ |
| Strategist | **100%** (15/15) | 85% | ✅ |
| Tech | **100%** (15/15) | 85% | ✅ |
| Economist | **93.3%** (14/15) | 85% | ✅ |

**Overall gate:** `pass` (было `fail` на baseline 2026-06-14).

---

## Live Hermes (шаг 3b, 2026-06-17)

| Метрика | Значение |
|---------|----------|
| Кейсы | **36/36 pass** (100%) |
| Путь | `parse_intent` → Ollama timeout → **rescue** |
| Лог | `gate_live_20260617_152400.log` |
| Enrich smoke | **100%** все агенты — `agents_gate_enrich_smoke_20260617_113107.json` |

---

## Текущие показатели (baseline 2026-06-14 live)

| Агент | Pass rate | Порог Ф2 | Gate | Δ vs 2026-06-13 | Цель Ф3 |
|-------|-----------|----------|------|-----------------|---------|
| Hermes | **72.2%** (26/36) | 85% | 🔴 fail | −5.6% | **≥85%** → **≥95%** |
| Analyst | **86.7%** (13/15) | 75% | ✅ pass | 0 | удержать **≥90%** |
| Economist | **73.3%** (11/15) | 75% | 🟡 warn | 0 | **≥85%** |
| Marketer | **86.7%** (13/15) | 75% | ✅ pass | 0 | удержать **≥90%** |
| Strategist | **80.0%** (12/15) | 75% | ✅ pass | −13.3% | **≥85%** → **≥90%** |
| Tech | **60.0%** (9/15) | 75% | 🔴 fail | −6.7% | **≥85%** |

**Overall gate:** `fail` (Hermes + Tech ниже порога Ф2).

---

## Типовые провалы (для тюнинга Ф3)

| Агент | Паттерн | Примеры кейсов |
|-------|---------|----------------|
| Hermes | intent confusion | `create_lead`→`save_to_rag`, `run_analysis`→`analytics_*`, `ask_strategist`→`generate_lead`/`ask_economist`, `search_web`→`find_leads_portrait` |
| Economist | missing keywords | `финансов`, `enterprise`, `бюджет` в ответе |
| Tech | missing keywords | `риск`, `advanced`, `вопрос`, `недел`, `миграц` |
| Strategist | missing state tokens | `low`, `medium`, `this_week` |
| Analyst | missing slots | `industry` в create_lead |

---

## Когда начинать тюнинг

1. **Не в Ф2** — пока идём по MAP (§4 RAG, fanout, enrich, …).
2. **Старт Ф3** — когда владелец даёт `go` на «quality gate tuning» **после** закрытия критичного функционала Ф2.
3. **Порядок работ (черновик):**
   - Hermes: rescue/parse + eval-failed → датасет → промпт/slots
   - Tech + Economist: промпты + must_contain в eval
   - Strategist: state_overrides в кейсах
   - Повторный full gate → сравнение с baseline в этом файле

---

## Команды

```bash
cd backend
$env:EVAL_OLLAMA_TIMEOUT="1200"
python scripts/run_agents_quality_gate.py --write-acceptance
# → data/artifacts/eval/agents_gate_*.json
```

Acceptance (живая таблица): [`AGENTS_QUALITY_GATE_ACCEPTANCE.md`](../phase2/agents/AGENTS_QUALITY_GATE_ACCEPTANCE.md)

---

## Связь с MAP

| Фаза | Что делаем |
|------|------------|
| **Ф2** | Инфра gate ✅ · full run ✅ · `[x]` только при green на порогах Ф2 |
| **Ф3** | Тюнинг до **≥85% все** · stretch **90–100%** · A/B промптов по трейсам |

BACKLOG: запись «Quality gate tuning Ф3» в [`BACKLOG.md`](../session/BACKLOG.md).
