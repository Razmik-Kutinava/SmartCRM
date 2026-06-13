# Вход в Фазу 2 — handoff для следующего агента

**Дата решения:** 2026-06-13  
**Решение владельца:** Ф1 DoD закрыта (6/6); **идём в Ф2** по [`PRD_MAP.md` § Порядок Ф2](../product/PRD_MAP.md#порядок-фазы-2). Хвосты Ф1 (🟡 spot-check, Битрикс-туннель) **не блокируют** старт Ф2.

---

## Git

| | |
|---|---|
| **Ветка** | `main` |
| **Push** | ❌ **ждём явный go** владельца (перед push — ещё одна задача) |
| **Незакоммичено** | только runtime: `backend/data/*.json`, кэши, `.coverage`, venv — **не коммитить** |
| **Код quality gates** | ✅ в коммитах до `3b91a58` |

**Последние коммиты (quality gates + ops):**

- `3b91a58` — SESSION_STATE smoke+full
- `450e981` — gate CLI cp1251; smoke artifact; full gate started
- `c47a007` / `70fd98d` — шаг 7 pytest 34 passed
- `60d9a51` — gate CLI `--log-file`
- `71b2206` — tools API key 401 fix
- `7be7bdb` … `596d2e1` — UI gate, learning loop

---

## Фаза 1 — что закрыто / что висит

| | |
|---|---|
| **DoD Ф1** | ✅ 6/6 — mic E2E, блоки MAP baseline |
| **Не блокер Ф1** | 🟡 spot-check approve/fanout (5 мин руками); 🟡 Битрикс туннель (Ф2/DevOps); quality gates live (Ф2) |
| **MAP § хвосты Ф1** | [`PRD_MAP.md` L306–318](../product/PRD_MAP.md) — указатель → `BACKLOG.md` |

---

## Quality gates (Ф2, параллельно)

| | |
|---|---|
| **Инфра + UI + pytest** | ✅ шаги 0–7 |
| **Smoke** | `backend/data/artifacts/eval/agents_gate_20260613_143114.json` (limit 2, overall fail) |
| **Full live gate** | 🔄 был запущен 2026-06-13 — лог `gate_full_20260613.log`; Hermes прошёл, на analyst; **нового full JSON может не быть** — перепроверить процесс/Ollama |
| **MAP `[x]` gate** | только после green `overall_gate` + «ок» владельца |
| **Команда** | `cd backend && python scripts/run_agents_quality_gate.py --write-acceptance` |

Доки: [`AGENTS_QUALITY_GATE_ACCEPTANCE.md`](../phase2/agents/AGENTS_QUALITY_GATE_ACCEPTANCE.md) · [`AGENTS_LEARNING_MAP.md`](../phase2/agents/AGENTS_LEARNING_MAP.md)

---

## Фаза 2 — как начинать

1. **Ждать `go` с номером очереди** из MAP (не «что ближе»).
2. **Кандидаты без go:** очередь **1** §1 Voice Layer **или** **5** §8 leadgen+голос (MAP уже помечает 5 как in progress).
3. **Процесс:** один пункт MAP → тест → код → commit → `SESSION_STATE` + `HANDOFF` + `CHANGELOG`.
4. **Push/deploy** — только по явному go.

**Канон:** [`PRD_MAP.md`](../product/PRD_MAP.md) · [`HANDOFF.md`](HANDOFF.md) · [`BACKLOG.md`](BACKLOG.md) · [`smartcrm-task-workflow.mdc`](../../.cursor/rules/smartcrm-task-workflow.mdc)

---

## Следующий шаг (на момент handoff)

- Владелец: **ещё одна задача**, потом push (go), потом **`go` на пункт Ф2**.
- Агент: **не начинать код Ф2** без номера очереди; можно дочитать gate-арtefakt / обновить acceptance если full gate завершился.
