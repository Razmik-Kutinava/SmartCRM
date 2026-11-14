# Ф4 — Агенты по синтезу (контекст + промпты + суфлёр)

## Статус

🔲 **Спека** — PHASE 1 (todo.md заполнен, ждёт `go` на RED)  
🔲 Код — `backend/agents/agent_synthesis.py` + правки `orchestrator.py` / `hermes_prompt_profiles.py`  
🔲 Тест — `tests/agents/test_agent_synthesis.py`  
🔲 Регрессия — `crm_leads` + `analyst`  
🔲 UI smoke — карточка → плитка «Агенты» → «Синтез»  
🔲 `[x]` в `CHECKLIST_F4.md` — только после «ок»

## Заказ (дословно, из `todo.md`)

Собирает контекст лида (этап, задачи, паспорт, 🔍, переписка) → вызывает 5 агентов → выдаёт единый совет: 1–3 следующих шага простым языком + суфлёр `missing_data` на карточке + задача из `next_action`.

## Зависимость

Требует: **«Агенты на карточке работают»** — `POST /api/agents/email/run` без ошибок, аналитик с `lead_id`, дайджест переписки урезан. Без этого синтез не запустится.

## Что реализовать (SBR)

### PHASE 0 INTAKE (в `todo.md`)

Дословный заказ + пункт чеклиста Ф4 «Агенты по синтезу (контекст+промпты+суфлёр)».

### PHASE 1 SPEC

- Тест: `tests/agents/test_agent_synthesis.py` (новый) — проверяет: контекст собирается → 5 агентов отвечают → есть `next_action` + `missing_data` на карточке
- Файлы: `orchestrator.py`, `hermes_prompt_profiles.py`, `agent_synthesis.py` (новый модуль)
- Читать: `СИНТЕЗ_АГЕНТЫ_ВОРКФЛОУ_И_ПРОМПТЫ.md` § «Синтез в код», `F4_LEADS_ACCEPTANCE.md`

### PHASE 2 BUILD (RED→GREEN)

1. RED: тест падает (нет синтеза)
2. GREEN: код синтеза — собирает слоты (паспорт, 🔍, этап, задачи, email) → прогоняет агентов → возвращает структурированный ответ для UI

### PHASE 3 REVIEW

- Регрессия: `crm_leads` + `analyst` (из `smartcrm-dev-gates.mdc`)
- UI smoke: открыть карточку → плитка «Агенты» → кнопка «Синтез» → совет отображается

## Контекст / суфлёр

Уже в коде, не дублировать:
- `backend/core/agent_email_context.py` — `build_agent_slots` (lead_id, company, checko, tech, web_research_brief, email digest, context_gaps)
- `backend/core/agent_gaps.py` — `gaps_for_agent`, `card_suffler`, `merge_missing`
- `backend/api/routes/agent_email.py` — `POST /api/agents/email/run` (запуск отдельного агента, apply задачи из next_action)

## Приёмка

- [ ] Тест зелёный
- [ ] Регрессия `crm_leads` + `analyst` PASS
- [ ] На карточке лида в плитке «Агенты» нажал «Синтез» → получил 1–3 шага + `missing_data` блок
- [ ] `go` пользователя → `[x]` в чеклисте Ф4

## Куда писать результат

- `docs/operations/phase4/leads/F4_AGENT_SYNTHESIS.md` (этот файл)
- `SESSION_STATE.md` / `CHANGELOG.md` / `HANDOFF.md` — в том же коммите
