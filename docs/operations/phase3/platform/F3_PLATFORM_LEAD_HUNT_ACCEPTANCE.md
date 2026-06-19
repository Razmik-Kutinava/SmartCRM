# Платформа — автономный поиск лидов (acceptance)

**PRD_MAP:** «Автономный поиск новых лидов агентами»

## Шаг 1 — каркас

| Компонент | Изменение |
|-----------|-----------|
| `lead_hunt_config.py` | конфиг: вкл, интервал, лимит кандидатов, порог скора |
| `lead_hunt_background.py` | scheduler, poll loop |
| `GET /api/ops/lead-hunt/status` | статус планировщика |
| `GET/PUT /api/ops/lead-hunt/config` | настройки |
| `POST /api/ops/lead-hunt/run` | ручной прогон |
| `main.py` | фоновая задача при старте uvicorn |

ENV: `LEAD_HUNT_ENABLED`, `LEAD_HUNT_INTERVAL_HOURS`.

- [x] Планировщик due / state JSON
- [x] API status + config + manual run
- [x] pytest unit + API

## Шаг 2 — ICP из CRM

| Компонент | Изменение |
|-----------|-----------|
| `lead_hunt_icp.py` | `build_icp_from_won` + `funnelBySource` |
| `strategist_enrich_icp` | 1 LLM-вызов (fallback эвристика) |
| `state.icp` | версионированный ICP |
| `GET/POST .../icp/refresh` | текущий ICP / пересборка |

- [x] Портрет из выигранных + топ источников
- [x] Стратег: город/отрасль/размер
- [x] Версии ICP в state
- [x] pytest

## Шаг 3 — поиск кандидатов

| Компонент | Изменение |
|-----------|-----------|
| `lead_hunt_candidates.py` | `search_candidates` → `search_by_portrait` |
| `run_scheduled_lead_hunt` | ICP → поиск → очередь |
| фаза `search` | в отчёте прогона |

- [x] Поиск по `search_portrait` из ICP
- [x] Фильтр по `min_score_threshold`
- [x] pytest mock

## Шаг 4 — очередь approve → CRM

| Компонент | Изменение |
|-----------|-----------|
| `lead_hunt_queue.py` | нормализованный вид: company, score, summary, status |
| `state.candidates` | `pending` / `approved` / `rejected` |
| `GET .../lead-hunt/queue` | список по статусу (алиас `/candidates`) |
| `POST .../queue/{id}/approve` | `save_candidate_to_crm` + опционально nurture |
| `POST .../queue/{id}/reject` | отклонение |
| UI | блок «Найдено агентами» на `/ops/queue` и `/leadgen` |

- [x] Очередь в state + нормализованный API
- [x] Approve → CRM (`source=lead_hunt`), nurture опционально
- [x] pytest queue + API + UI panel

## Шаг 5 — фон + уведомления

| Компонент | Изменение |
|-----------|-----------|
| `main.py` | `lead_hunt_poll_loop` в lifespan (как tender_monitor) |
| `lead_hunt_run_log.py` | trace `lead_hunt_run` + `agent_run_log` при approve |
| `core/traces.py` | `record_lead_hunt_run` |
| UI ops | баннер + счётчик непрочитанных в nav |
| Telegram | → BACKLOG (позже) |

- [x] Фоновый loop в main.py
- [x] In-app уведомления + баннер / badge в Ops
- [x] Trace + agent_run_log для eval
- [x] pytest

## Шаг 6 — UI оператора

| Компонент | Изменение |
|-----------|-----------|
| `LeadHuntOperatorPanel.svelte` | вкл/выкл, интервал, последний прогон, очередь |
| `/ops/lead-hunt` | экран оператора (тёмная тема Ops) |
| `/leadgen` вкладка «Авто-охота» | тот же панель в лидогене |
| `POST .../queue/approve-above` | «Одобрить всех ≥70» |
| `leadHuntOps.js` | `approveLeadHuntAbove`, `getApiUrl` |

- [x] Вкл/выкл, интервал, последний прогон, очередь
- [x] «Запустить сейчас», «Одобрить всех ≥70»
- [x] DevTools smoke (data-testid + клики)

## Шаг 7 — закрытие MAP (ждёт «ок» пользователя)

| Компонент | Изменение |
|-----------|-----------|
| Acceptance | шаги 1–7 полные |
| `backend/leadgen/README.md` | секция lead hunt |
| `backend/main.py` | lead hunt в lifespan |
| `PRD_MAP.md` | `[x]` — **только после «ок»** |

- [x] Acceptance полный
- [x] README + main.py
- [ ] `[x]` в PRD_MAP — после апрува оператора

## Критерии закрытия MAP

- [x] Шаги 1–7 (код + pytest)
- [x] pytest lead hunt suite (unit + API + bulk)
- [x] UI smoke `/ops/lead-hunt` + `/leadgen` вкладка «Авто-охота»
- [ ] PRD_MAP `[x]` — по «ок» пользователя
