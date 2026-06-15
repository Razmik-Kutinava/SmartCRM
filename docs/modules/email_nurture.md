# Email nurture — цепочка касаний

## Шаблонная цепочка (20 касаний)

Детерминированные шаблоны + `{{company}}` / `{{contact}}` при отправке.

- Код: `services/email_nurture_plan.py`, `services/email_nurture.py`
- API: `POST /api/email/nurture/start`, `/start-segment`, `/process-due`

## LLM-цепочка под продукт (маркетолог)

Маркетолог анализирует лида → **N писем** под продукт → nurture с кастомным планом.

- `agents/marketer_nurture.py` — LLM, строгий RAG
- `services/email_nurture_llm.py`, `services/email_nurture_rag.py`
- API: `preview-llm`, `test-send`, `start-llm`

**Live smoke:** `python scripts/smoke_email_nurture_llm_live.py`

## Этап A — UI `/email` (точечные касания) ✅

Вкладка **«Касания (1 лид)»**:

| Шаг | API |
|-----|-----|
| Превью | `POST /nurture/preview-llm` |
| Тест ib@ | `POST /nurture/test-send` |
| Запуск | `POST /nurture/start-llm` |
| История | `GET /nurture/chains` |

UI: `frontend/src/components/EmailNurturePanel.svelte`  
Логика: `frontend/src/lib/email/nurtureTouchLogic.js`

Настройки: 1/3/20 касаний, продукт, LLM или свои шаблоны, аккаунт, подпись.

## С карточки лида ✅

Кнопка **«Рассылка»** на `/leads/{id}` → drawer с реестром типов (`leadMailingTypes.js`).

| Компонент | Путь |
|-----------|------|
| Drawer | `components/LeadMailingDrawer.svelte` |
| Реестр типов | `lib/leads/leadMailingTypes.js` |
| Deep link | `/email?lead={id}&panel=nurture` |

Сейчас один тип: **цепочка касаний** (тот же `EmailNurturePanel`, `lockLead` + `compact`). Новые типы — строка в `LEAD_MAILING_TYPES`.

## Дальше (план B–D)

- B: массовый сегмент + апрув 3 примеров
- C: тип цепочки new/cross/upsell + `products_owned`
- D: справочник отраслей
