# Email nurture — цепочка касаний

## Шаблонная цепочка (20 касаний)

Детерминированные шаблоны + `{{company}}` / `{{contact}}` при отправке.

- Код: `services/email_nurture_plan.py`, `services/email_nurture.py`
- API: `POST /api/email/nurture/start`, `/start-segment`, `/process-due`
- Acceptance: `docs/operations/phase3/email/F3_EMAIL_AUTONOMY_ACCEPTANCE.md`

## LLM-цепочка под продукт (маркетолог)

**Фича:** маркетолог анализирует лида из CRM и генерирует **N писем** (пилот: 3) под конкретный продукт (например **Positive Technologies MaxPatrol VM**), затем запускается nurture-цепочка с кастомным планом.

| Шаг | Что |
|-----|-----|
| 1 | Выбор лида (`pick_nurture_lead`) или `lead_id` |
| 2 | Опц. подмена email на тестовый (`client_email`) |
| 3 | `agents/marketer_nurture.py` — LLM: профиль, attack surface, 3 письма |
| 4 | `services/email_nurture_llm.py` — план → `start_nurture_chain(plan=...)` |
| 5 | `send_now=true` — все шаги `scheduled_at=now` → `process-due` |

**API:** `POST /api/email/nurture/start-llm`

```json
{
  "account_id": 11,
  "product_name": "Positive Technologies MaxPatrol VM",
  "email_count": 3,
  "sender_name": "Иван Б.",
  "sender_email": "ib@agneko.com",
  "client_email": "ib@agneko.com",
  "send_now": true
}
```

**Live smoke:** `python scripts/smoke_email_nurture_llm_live.py`

**Расширение до 20 касаний:** тот же пайплайн, `email_count: 20` + промпт маркетолога (после апрува пилота).
