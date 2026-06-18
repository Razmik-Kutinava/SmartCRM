# Платформа — автономный поиск лидов (acceptance)

**PRD_MAP:** «Автономный поиск новых лидов агентами»

## Шаг 1 — каркас (этот документ §1)

### Было

- Лидоген только по команде оператора (голос, `/leadgen`)
- Нет фонового цикла и Ops-статуса

### Стало

| Компонент | Изменение |
|-----------|-----------|
| `lead_hunt_config.py` | конфиг: вкл, интервал, лимит кандидатов, порог скора |
| `lead_hunt_background.py` | scheduler, poll loop, ICP-превью из won-лидов |
| `GET /api/ops/lead-hunt/status` | статус планировщика |
| `GET/PUT /api/ops/lead-hunt/config` | настройки |
| `POST /api/ops/lead-hunt/run` | ручной прогон |
| `main.py` | фоновая задача при старте uvicorn |

ENV: `LEAD_HUNT_ENABLED`, `LEAD_HUNT_INTERVAL_HOURS` (override файла).

### Критерии шага 1

- [x] Планировщик due / state JSON
- [x] API status + config + manual run
- [x] Прогон строит ICP-портрет из выигранных сделок (без поиска кандидатов)
- [x] pytest unit + API

## Дальше (не этот шаг)

| Шаг | Содержание |
|-----|------------|
| 2 | ICP + Стратег, версионирование |
| 3 | `search_by_portrait` / prospect в цикле |
| 4 | Очередь approve → CRM |
| 5 | Уведомления |
| 6 | UI `/ops` или `/leadgen` |
