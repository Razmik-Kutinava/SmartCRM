# Quality gates — baseline и цель Ф3 (тюнинг)

> **Ф2:** закрываем функционал и smoke/full gate с **текущими порогами** (Hermes ≥85%, остальные ≥75%).  
> **`[x]` gate в MAP** — только когда `overall_gate=pass` на этих порогах.  
> **Ф3:** после «всё работает» — довести **всех агентов ≥85%**, цель **90–100%** (не блокер Ф2).

Снимок прогона: **2026-06-14** · артефакт `agents_gate_20260614_140940.json` · лог `gate_full_20260614_1628.log`

---

## Текущие показатели (baseline)

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
