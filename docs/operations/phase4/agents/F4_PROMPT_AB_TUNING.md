# Ф4 — A/B промптов по трейсам (тюнинг)

**Откуда:** Ф3 — базовый A/B на `/ops/intents/improve` — см. [`F3_PROMPT_AB_TRACES_ACCEPTANCE.md`](../../phase3/agents/F3_PROMPT_AB_TRACES_ACCEPTANCE.md).

**Сейчас:** 👎 трейсы → редактор промпта → кнопка «A/B по трейсам» (hermes3); `expected` intent — только если есть eval-сценарий с той же фразой.

**Зачем Ф4:** без эталона и регрессии A/B показывает «интент сменился», а не «стало лучше»; нет истории прогонов и A/B для агентов.

**PRD_MAP:** Фаза 4 → A/B промптов (тюнинг).

---

## Чеклист (после «ок» на Ф3 A/B)

| # | Задача | Что сделать | Проверка |
|---|--------|-------------|----------|
| 1 | **Эталон при 👎** | При минусе на трейсе — спросить «какой intent должен был быть»; сохранить в трейсе / сценарий eval | A/B считает accuracy без ручного дубля в scenarios |
| 2 | **Больше кейсов** | Лимит >15; опция «все 👎 за N дней»; дедуп с лимитом по intent | Отчёт стабильнее при n≥30 |
| 3 | **Регрессия good** | В A/B добавить выборку 👍 / approved eval — «вариант не сломал рабочее» | `regressions` на known-good фразах |
| 4 | **Модель в UI** | Выбор groq / hermes3 / обе; подпись «как в проде» | Прогон с Groq без правки кода |
| 5 | **A/B агентов** | Тот же поток на `/ops/agents` (не только Hermes) | API + UI для marketer, tech_specialist, … |
| 6 | **Suggest → A/B** | После «Предложи правку» — кнопка «Сразу A/B» (вариант = редактор с few-shot) | Один клик после Groq-анализа |
| 7 | **История отчётов** | Сохранять JSON A/B в `data/artifacts/` + строка в `/ops/history` (label, Δ accuracy, версия промпта) | Сравнение «было / стало» по версиям |
| 8 | **Dr. QA в UI** | Обёртка над `qa_agent` / KPI-gate на Ops (сейчас CLI) | Canary / gate без терминала |

---

## Не в этом чеклисте

- Отдельная страница «A/B лаборатория» — только если improve + agents не хватит
- Авто-применение выигравшего промпта без апрува оператора

---

## Связанные файлы

- `backend/core/prompt_ab_traces.py`
- `backend/core/eval_runner.py`
- `api/routes/ops/hermes_routes.py` — `POST /hermes/prompt/ab-traces`
- UI `frontend/src/routes/ops/intents/improve/+page.svelte`
- Трейсы: `core/traces.py`, `/ops/traces`
