# SmartCRM — CRM и раздел «Лиды»

Документ описывает, как устроены воронка, скоринг, приоритеты и URL после переноса основного UI в **`/leads`**, а также связь с настройками в Ops и файлом `crm_settings.json` на бэкенде.

---

## Кратко: что сделано

1. **Основной интерфейс работы с лидами** — под префиксом **`/leads`**: воронка, список, календарь, задачи, фокус, аналитика и карточка сделки **`/leads/{id}`**. В боковом меню приложения пункт называется **«Лиды»** и ведёт на **`/leads`** (корень редиректит на **`/leads/list`**).

2. **Путь `/crm/*` сохранён только для совместимости**: отдельных страниц под `/crm` больше нет — везде стоит **редирект 308** на эквивалентный путь под **`/leads`**, чтобы старые закладки и интеграции не ломались.

3. **Единая конфигурация воронки и порогов** (в духе «CRM Points»): этапы воронки, диапазон скора, пороги приоритета и скор по умолчанию для новых лидов задаются в **`backend/data/crm_settings.json`** и редактируются в **Ops → CRM** (`/ops/crm`). Для обычного UI без ключей Ops доступен лёгкий read-only эндпоинт **`GET /api/crm/config`**.

4. **Приоритет по скорингу**: в списке лидов добавлена колонка «Приоритет» (уровни вроде критический / высокий / средний / низкий по порогам из конфига); на карточке лида рядом со скором показывается тот же бейдж. Дефолтный **`score`** при создании лида с голоса берётся из **`default_new_lead_score`**, если конфиг уже успел загрузиться.

5. **Массовая рассылка по лиду** перенесена на **`/leads/campaign/{id}`** (раньше был конфликт динамических сегментов `[id]` и `[leadId]`).

---

## Маршруты фронтенда

| URL | Назначение |
|-----|------------|
| `/leads` | Редирект на `/leads/list` |
| `/leads/list` | Таблица лидов, фильтры по этапам из конфига, Bitrix-импорт |
| `/leads/funnel` | Канбан по этапам |
| `/leads/calendar`, `/leads/tasks`, `/leads/focus`, `/leads/analytics` | Остальные экраны CRM |
| `/leads/{id}` | Карточка сделки |
| `/leads/campaign/{id}` | Черновик кампании по лиду |

Таб-навигация: `frontend/src/routes/leads/+layout.svelte`. Канон маршрутов для смоука: `frontend/src/lib/leads/leadsRouteManifest.js`; регрессия: `cd backend && python scripts/smoke_leads_block.py`.

Общий лейаут приложения (`+layout.svelte`) для интентов голоса считает зону «лиды» и по **`/leads`**, и по **`/crm`**, чтобы редирект не ломал сценарии «покажи лиды».

---

## Редиректы с `/crm` (обратная совместимость)

Отдельные **`frontend/src/routes/crm/**/+page.js`** только бросают `redirect(308, ...)`.

| Запрос | Куда |
|--------|------|
| `/crm` | `/leads/list` |
| `/crm/list` | `/leads/list` |
| `/crm/funnel` | `/leads/funnel` |
| `/crm/calendar` | `/leads/calendar` |
| `/crm/tasks` | `/leads/tasks` |
| `/crm/focus` | `/leads/focus` |
| `/crm/analytics` | `/leads/analytics` |
| `/crm/{id}` | `/leads/{id}` |
| `/crm/campaign/{id}` | `/leads/campaign/{id}` |

---

## API и данные

### Лиды (как и раньше)

- **`/api/leads`** — список, создание, **`PATCH /api/leads/{id}`** — поля лида, включая **`score`**, **`stage`**, **`approvals`** (чеклист булевых «доков»; веса влияют на **`scoreAdvisory`**, не на `score` в БД), гейты по `stage_transition_rules`, аудит полей.
- **`GET/POST /api/leads/{id}/comments`**, **`GET /api/leads/{id}/audit`** — комментарии и история полей; в аудите у записей есть **`eventType`** (например `field_change`, `communication`) и **`metadata`** при событиях вне диффа полей.
- **`GET/POST /api/leads/{id}/communications`** — лог касаний (тип, текст, автор, время); при POST дополнительно пишется строка аудита с `eventType=communication`.
- Источник правды по записям — PostgreSQL, модель **`Lead`** (`backend/db/models/lead.py`), поля в т.ч. `checko_json`, `tech_json`, `financials_json` для обогащения.

### Конфиг CRM для UI

- **`GET /api/crm/config`** — JSON для фронтенда: `stages`, `priority_thresholds`, `score_range`, `default_new_lead_score`. Реализация: `backend/api/routes/crm.py`, данные из `core.crm_settings_store.load_settings()`.
- Те же настройки целиком (включая мета про Битрикс без секрета) читаются/пишутся в Ops: **`GET/PUT /api/ops/crm-settings`** — см. `backend/api/routes/ops.py`.

Файл на диске: **`backend/data/crm_settings.json`**. При отсутствии файла подставляются значения по умолчанию из `backend/core/crm_settings_store.py` (в т.ч. пороги приоритета под шкалу скора 0–100).

### Фронтенд: модуль воронки и приоритета

- **`frontend/src/lib/crmStages.js`**: `loadCrmConfig()`, `leadPriorityTier()`, стили бейджей; массив **`CRM_STAGES`** обновляется после успешной загрузки конфига.

---

## Связанные документы

- HTTP-описание API: `docs/api/API.md`
- Импорт из Битрикс24: `docs/modules/bitrix.md`
- Ops и качество (в т.ч. настройки CRM в UI): `docs/start/RUNBOOK.md`, страница **`/ops/crm`**

---

## История правок (для ревью)

- Перенос полного дерева Svelte из **`routes/crm`** в **`routes/leads`** с заменой ссылок и редирект-only деревом под **`routes/crm`**.
- Добавлены **`GET /api/crm/config`**, расширены **`crmStages.js`**, колонка приоритета и бейдж на карточке.
- P3 (референс CRM points): **`approvals`**, **`/communications`**, расширение аудита; UI чеклиста апрувов и касаний на **`/leads/[id]`**.
- Обновлены ссылки с дашборда, лидогенерации и навигации на **`/leads/...`**.
