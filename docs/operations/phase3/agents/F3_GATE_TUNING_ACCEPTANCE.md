# Ф3 — Quality gate tuning (acceptance)

**PRD_MAP:** Self-improvement → Quality gate tuning (все агенты ≥85%).

---

## Компромисс weak CPU (ноутбук)

Полный live gate 111 кейсов на CPU может занять **3–6 ч**. Закрываем пункт MAP по **трём уровням**:

| Уровень | Что проверяет | Команда | Критерий |
|---------|---------------|---------|----------|
| **A** | enrich + rescue (детерминированный слой) | `run_gate_enrich_smoke.py` | все агенты **≥85%**, overall `pass` |
| **B** | Hermes live `parse_intent` (Ollama→rescue) | `run_agents_quality_gate.py --hermes-only` | Hermes **≥85%** (36/36) |
| **C** | 5 агентов live Ollama | `run_agents_quality_gate.py --agents-only` | каждый **≥85%** |

**`[x]` в PRD_MAP** — когда **A + B + C** зелёные **или** владелец даёт «ок» на A+B при открытом C (ISSUES: долгий CPU).

**Закрыто 2026-06-17:** A+B+C зелёные + апрув «ок» → `[x]` PRD_MAP.

Профиль CPU (по умолчанию в gate): `GATE_CPU_PROFILE=1` → `qwen2.5:3b`, Hermes timeout 6 с → rescue.

---

## Журнал шагов

| Шаг | Дата | Результат |
|-----|------|-----------|
| 1 | 2026-06-16 | порог 85%, parse_intent, enrich Tech/Econ/Strategist |
| 2 | 2026-06-16 | rescue 36/36, enrich smoke **100%** |
| 3 | 2026-06-17 | live Hermes **36/36** (`gate_live_20260617_152400.log`); агенты — `--agents-only` CPU profile |
| 3b | 2026-06-17 | enrich smoke повтор **100%** (`agents_gate_enrich_smoke_20260617_113107.json`) |
| 3c | 2026-06-17 | live agents **C** — `overall_gate: pass` (~29 мин, CPU); Analyst/Marketer/Strategist/Tech **100%**, Economist **93.3%** (14/15, кейс `economist-005`); лог `gate_live_agents_20260617_161513.log` |

---

## Итог live agents (уровень C, 2026-06-17)

| Агент | Pass | Порог | Gate |
|-------|------|-------|------|
| Hermes (B) | 36/36 (100%) | 85% | ✅ |
| Analyst | 15/15 (100%) | 85% | ✅ |
| Marketer | 15/15 (100%) | 85% | ✅ |
| Strategist | 15/15 (100%) | 85% | ✅ |
| Tech | 15/15 (100%) | 85% | ✅ |
| Economist | 14/15 (93.3%) | 85% | ✅ |

Ollama на CPU часто падал по timeout — кейсы проходили через **enrich/rescue**. Economist-005: нет ключевого слова «финансов» (не блокер gate).

---

## Команды

```powershell
cd backend
$env:EVAL_OLLAMA_TIMEOUT = "3600"
$env:GROQ_API_KEY = ""
python scripts/run_gate_enrich_smoke.py --write-acceptance
python -u scripts/run_agents_quality_gate.py --write-acceptance --log-file data/artifacts/eval/gate_live_YYYYMMDD.log
```

См. также [`GATE_FULL_RUNBOOK.md`](../../phase2/agents/GATE_FULL_RUNBOOK.md), baseline [`AGENTS_GATE_TUNING_BASELINE.md`](../../baselines/AGENTS_GATE_TUNING_BASELINE.md).
