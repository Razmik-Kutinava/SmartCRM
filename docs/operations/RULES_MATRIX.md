# Матрица правил SmartCRM

> Живой чеклист: обновлять при изменении `.cursor/rules/smartcrm-*.mdc`.

## Сводка

| # | Правило | Где в репо | Enforcement | Статус |
|---|---------|------------|-------------|--------|
| R0 | SmartCRM `.mdc` выше глобальных User Rules (коммит/ops) | `dev-gates` п.0, `agent-workflow` §0, User Rules snippet | User Rules в Cursor (вставлено ✅) | ✅ |
| R1 | **`git commit` безусловно** (если менялись файлы) | `agent-workflow` §0–1 | `check_agent_step.py` → **FAIL** | ✅ |
| R1b | **Запрещено** «коммит не делал / скажи если нужен» | `agent-workflow` §0, `task-workflow` | — | ✅ |
| R2 | **Ops безусловно** | `agent-workflow` §2 | `check_agent_step.py` → **FAIL** | ✅ |
| R3 | Старт сессии: 3 строки | `task-workflow` § Старт сессии | дисциплина + матрица | ✅ |
| R4 | `go` на новую задачу; стоп после шага | `task-workflow`, `agent-workflow` §3 | дисциплина | ✅ |
| R5 | Тест на изменение + регрессия зоны | `task-workflow`, `dev-gates` | `run_zone_regression.py` | ✅ |
| R6 | Honest report в каждом отчёте | `task-workflow` § Честный отчёт | дисциплина | ✅ |
| R7 | BACKLOG ↔ пункт PRD_MAP | `task-workflow` § Бэклог, `BACKLOG.md` | таблица хвоста в BACKLOG | ✅ |
| R8 | Сплит >200 строк | `code-split.mdc` | ревью | ✅ |
| R9 | Backend README sync | `repo-layout` §5 | финиш-чеклист | ✅ |
| R10 | Push только по апруву | `task-workflow`, `agent-workflow` | — | ✅ |

## Старт сессии (шаблон агента)

| Поле | Откуда читать | Что писать |
|------|---------------|------------|
| `last_done:` | `HANDOFF.md` — последний шаг / коммиты | 1–2 предложения |
| `current_state:` | `SESSION_STATE.md`, `ISSUES.md` 🔴 | где стоим, блокеры |
| `next_step:` | `HANDOFF.md`, `PRD_MAP.md` | **один** логический шаг |

## Регрессия: что запускать и что записать

| Затронуто | Команда (`cd backend`) | В отчёт шага | В SESSION_STATE |
|-----------|------------------------|--------------|-----------------|
| Лиды CRM | `python scripts/run_zone_regression.py crm_leads` | команда + PASS/FAIL + хвост вывода | зона + результат |
| Лидоген | `… leadgen` | то же | то же |
| Голос | `… voice` | то же | то же |
| Hermes интенты | `… hermes_eval` | то же; FAIL → ISSUES | то же |
| Тендеры | `… tenders` | то же | то же |
| RAG | `… rag` | то же | то же |
| Несколько зон / сплиты | `python scripts/run_zone_regression.py p6` | то же | то же |
| Смоук P1 (общий) | `python scripts/run_zone_regression.py p1` | то же | то же |
| Только docs/rules | `check_agent_step.py` (без pytest) | «регрессия не требовалась» | «docs-only шаг» |

## Финиш шага (обязательный порядок)

| # | Действие | Проверка |
|---|----------|----------|
| 1 | Тесты зелёные (или docs-only) | вывод команды в отчёте |
| 2 | `git commit` | `check_agent_step.py` |
| 3 | SESSION_STATE | свежая строка с датой |
| 4 | CHANGELOG + HANDOFF | HANDOFF — последние 3 коммита |
| 5 | BACKLOG / ISSUES | если был хвост / баг |
| 6 | Отчёт пользователю (6 пунктов task-workflow) | honest report |
| 7 | **Стоп** — ждать `go` | — |

## Локальная проверка перед «done»

```bash
# из корня репо
python backend/scripts/check_agent_step.py
cd backend && python scripts/run_zone_regression.py p6
```
