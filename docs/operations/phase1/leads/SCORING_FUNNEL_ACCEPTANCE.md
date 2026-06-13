# Балльная воронка — acceptance (2026-06-08)

## Что это

Система подсказок по баллу лида: менеджер сам ставит `score` (0–100), а `scoreAdvisory` считает **suggestedScore**, предупреждения и breakdown (этап, сумма ₽, апрувы, просроченные задачи). В списке `/leads/list` приоритет (критический/высокий/…) берётся из `priority_thresholds` в `GET /api/crm/config`.

## Команда

```bash
cd backend && python scripts/smoke_scoring_funnel.py
```

## Покрытие (21 pytest)

| Зона | Файлы |
|------|--------|
| Формула | `tests/test_lead_score_advisory.py` |
| Приоритет (зеркало UI) | `tests/core/test_lead_priority_tier.py` |
| Список фильтр/сорт | `tests/lib/test_lead_list_filter.py` |
| API смоук | `tests/smoke/test_scoring_funnel_smoke.py` |

## Ключевые проверки

- `GET /api/crm/config` — пороги 85/70/40, `agentsMayUpdateScore=false`
- `GET /api/leads/{id}` — `scoreAdvisory.suggestedScore`, `warnings`, `breakdown`
- PATCH `score` меняет только балл менеджера, не ломает advisory
- Golden: этап «Новый» + 500k ₽ → suggestedScore 43 (28+15)

## Хвост (не блокер)

- Экспорт по баллам / расширенные SLA → Фаза 3
- Лидоген использует свои пороги 80/60/40 в `score_card.py` (не CRM config)
