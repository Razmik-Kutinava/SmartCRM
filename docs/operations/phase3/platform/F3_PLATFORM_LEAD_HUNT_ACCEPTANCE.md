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
| `state.candidates` | `pending` / `approved` / `rejected` |
| `POST .../candidates/{id}/approve` | лид в CRM (`source=lead_hunt`) |
| `POST .../candidates/{id}/reject` | отклонение |
| `GET .../candidates` | список по статусу |
| `autosave_above_threshold` | опционально сразу в CRM |

- [x] Очередь в state
- [x] Approve создаёт Lead
- [x] pytest + API

## Шаг 5 — уведомления

| Компонент | Изменение |
|-----------|-----------|
| `lead_hunt_notifications.py` | in-app уведомления |
| `notify_ops_queue` | дублирование в Ops-очередь |
| `GET/PATCH .../notifications` | список / прочитано |

- [x] Уведомление при новом кандидате
- [x] Ops queue item `kind=lead_hunt`

## Шаг 6 — UI `/ops/lead-hunt`

| Компонент | Изменение |
|-----------|-----------|
| `leadHuntOps.js` | клиент API |
| `/ops/lead-hunt` | конфиг, ICP, очередь, approve/reject |
| `ops/+layout.svelte` | пункт навигации |

- [x] Экран Ops
- [x] Ручной прогон + одобрение кандидатов

## Критерии закрытия MAP

- [x] Шаги 1–6
- [x] pytest lead hunt (unit + API)
- [x] UI smoke в браузере (страница `/ops/lead-hunt`, nav «Lead Hunt»; API — после reload uvicorn)
