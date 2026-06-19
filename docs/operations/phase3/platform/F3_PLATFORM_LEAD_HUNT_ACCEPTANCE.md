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

## Шаг 6 — UI `/ops/lead-hunt`

| Компонент | Изменение |
|-----------|-----------|
| `leadHuntOps.js` | клиент API |
| `/ops/lead-hunt` | конфиг, ICP, очередь, approve/reject |
| `ops/+layout.svelte` | пункт навигации |

- [x] Экран Ops
- [x] Ручной прогон + одобрение кандидатов

## Шаг 7 — цикл поиска (агенты)

| Компонент | Изменение |
|-----------|-----------|
| `lead_hunt_search_cycle.py` | ICP → portrait + prospect → pipeline light → fanout |
| `run_pipeline(deep_analysis=False)` | лёгкий скоринг топ-N |
| `fanout` | analyst + marketer + economist (как generate_lead) |
| dedup | ИНН / company в БД |
| очередь | не в CRM (autosave ≥ порога — настройка) |

- [x] Пайплайн прогона с агентами
- [x] pytest integration моки Checko/Serper/pipeline/fanout

## Критерии закрытия MAP

- [x] Шаги 1–6
- [x] pytest lead hunt (unit + API)
- [x] UI smoke в браузере (страница `/ops/lead-hunt`, nav «Lead Hunt»; API — после reload uvicorn)
