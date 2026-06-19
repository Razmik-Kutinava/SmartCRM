# Платформа — SLA-протоколы (acceptance)

**PRD_MAP:** «Расширенные SLA-протоколы + эскалация» (баллы P3)

## Было

- `sla_due` и `escalated` вручную на задаче
- Фильтр overdue, без протоколов по стадии

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `core/sla_protocols.py` | каталог протоколов в `crm_settings.sla_protocols` |
| `services/sla_protocol_runner.py` | назначение на лид, автозадачи |
| `services/sla_escalation*.py` | фон: просрочка → escalated + Ops queue + Telegram critical |
| `PUT /api/leads/{id}/sla-protocol` | назначение протокола |
| `GET /api/leads/sla-protocols` | каталог |
| UI карточки + `/ops/crm` | выбор протокола, редактор JSON |
| Смена стадии | авто-назначение протокола по `stage` |

## Критерии

- [x] Пресеты протоколов (Новый / КП / Переговоры)
- [x] Назначение → задачи с `sla_due` и маркером `sla_step:`
- [x] Фоновая эскалация + Ops
- [x] pytest unit + API
- [ ] Ручной smoke: смена стадии → задачи → просрочка → Ops

## Дальше

- Экспорт отчёта по баллам (вторая строка P3 MAP)
