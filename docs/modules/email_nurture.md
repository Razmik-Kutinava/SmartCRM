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
| Drawer | `components/LeadMailingDrawer.svelte` + **`LeadMailingHost`** в корневом layout |
| Store | `lib/leads/leadMailingUi.js` — `openLeadMailing(lead)` с любой страницы |
| Deep link | `/email?lead={id}&panel=nurture` |

Сейчас один тип: **цепочка касаний** (тот же `EmailNurturePanel`, `lockLead` + `compact`). Новые типы — строка в `LEAD_MAILING_TYPES`.

| Реестр типов | `lib/leads/leadMailingTypes.js` |

Host в корневом `+layout.svelte` — `fixed` поверх всего UI, без prop-drilling.

## Этап B — массовая рассылка (сегмент) ✅

Вкладка **«Массовая (сегмент)»** на `/email`:

| Шаг | API |
|-----|-----|
| Счётчик сегмента | `POST /campaigns/segment-preview` |
| 3 примера (маркетолог + RAG) | `POST /campaigns/preview-llm` |
| Тест ib@ | `POST /campaigns/test-send` |
| Отправить | `POST /campaigns` + `send_now: true` |
| История | `GET /campaigns` |

UI: `EmailCampaignPanel.svelte` · логика: `campaignSegmentLogic.js`

Фильтры: stage, score, industry (справочник), city, search, `industry_verified`. Апрув чекбокс после 3 примеров.

## Этап D — отрасль (справочник и дозаполнение) ✅

| Что | Где |
|-----|-----|
| Справочник | `GET /api/leads/industries` — фиксированный список + значения из CRM (`services/industry_catalog.py`) |
| Поле лида | `industry` + флаг `industryVerified` (`industry_verified` в БД) |
| Модалка | `LeadIndustryModal` + `LeadIndustryHost` в root layout |
| Пустая отрасль | Перед рассылкой с карточки (`openLeadMailing`) и перед превью nurture |
| Массовый сегмент | Select отрасли, чекбокс «только проверенные», счётчик `withoutIndustry` |

UI: `industryCatalog.js`, `leadIndustryUi.js`, карточка `/leads/{id}` — datalist + «Указать отрасль».

## Дальше (план C)

- C: тип цепочки new/cross/upsell + `products_owned`
