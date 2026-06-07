# Импорт лидов из Битрикс24 в SmartCRM

Подробное описание реализации входящего вебхука, REST-импорта, правок окружения и типовых сбоев.

---

## 1. Что сделано

### 1.1 Бэкенд

- **Модуль** `backend/integrations/bitrix24.py`
  - Вызовы REST по базовому URL из переменной **`BITRIX24_WEBHOOK_URL`** (формат: `https://<портал>/rest/<user_id>/<секрет>/`).
  - **`bitrix_call(method, params)`** — POST на `<base>/<method>` с JSON-телом; разбор ответов Битрикса с ошибками в теле (в т.ч. при HTTP 401).
  - **`fetch_bitrix_lead_total(date_from)`** — лёгкий запрос `crm.lead.list` с `select: ["ID"]`, чтение поля **`total`** (сколько лидов попадает под фильтр `DATE_CREATE >= date_from`).
  - **`import_leads_from_bitrix(db, date_from, max_items)`** — постраничная выгрузка `crm.lead.list`, маппинг полей в модель `Lead`, **upsert** по полю **`bitrix_lead_id`**.
  - Справочники стадий/источников: `crm.status.list` (ENTITY_ID `STATUS` и `SOURCE`).
  - Ответственные: `user.get` по `ASSIGNED_BY_ID` с кэшем пользователей.
  - Дополнительные поля Битрикса в **`tech_json`**, в т.ч. UF-поля для последующего разбора.

- **Модель лида** `backend/db/models/lead.py`
  - Колонка **`bitrix_lead_id`** (уникальный идентификатор лида в Битриксе) + лёгкая миграция через `ALTER TABLE` в `backend/db/session.py` (`init_db`).

- **API** (`backend/api/routes/leads.py`)
  - **`POST /api/leads/import-bitrix`** — тело: `date_from`, `max_items` (**`0` = без верхнего лимита**, идём по `next` до конца).
  - В ответе: `imported`, `updated`, `skipped`, `total_processed`, **`bitrix_total`**, **`local_bitrix_leads_count`**, `unlimited`, `stopped_by_limit`, `sync_note`, `errors`, `error_count`.
  - **`GET /api/leads/bitrix-import-stats?date_from=...`** — сводка: `total` из Битрикса + число записей в нашей БД с **`bitrix_lead_id IS NOT NULL`** (все периоды).

- **Исключение** `BitrixWebhookError` — используется для возврата **403** с понятным текстом (нет прав, неверный секрет и т.д.).

### 1.2 Фронтенд

- **`frontend/src/lib/leadsStorage.js`**
  - `apiImportBitrix({ date_from, max_items })` — по умолчанию **`max_items: 0`** (полный прогон страниц).
  - `fetchBitrixImportStats(date_from)` — запрос статистики для подписи в UI.

- **`frontend/src/routes/leads/+page.svelte`**
  - Кнопка **«Битрикс24»** — запуск импорта.
  - Строка под заголовком: лидов в Битриксе по фильтру и число наших записей с Bitrix ID.
  - Тост после импорта с числами и подсказкой из `sync_note` при необходимости.

### 1.3 Окружение и запуск

- В **`backend/main.py`** явная загрузка `.env`:
  - сначала `backend/.env`, затем **`../.env` (корень репо SmartCRM) с `override=True`**, чтобы при запуске `uvicorn` из папки **`backend/`** подтягивался основной файл **`SmartCRM/.env`**.
- В **`.env.example`** задокументировано **`BITRIX24_WEBHOOK_URL`**.

### 1.4 Тесты (без моков, живой портал)

- Файл **`backend/tests/test_bitrix_integration.py`**
  - Три теста: **`profile`**, **`fetch_bitrix_lead_total`**, первая страница **`crm.lead.list`**.
  - Если **`BITRIX24_WEBHOOK_URL`** не задан — тесты **пропускаются** (`pytest.skip`).
  - Используется **`asyncio.run`**, без обязательного **pytest-asyncio**.

### 1.5 Git / безопасность

- При первом снимке коммита в репозиторий попал **`Groq` API key** в `.claude/settings.local.json` — **GitHub Push Protection** заблокировал push.
- Файл **`settings.local.json`** исключён через **`.gitignore`**, коммит пересобран без секрета.

---

## 2. Проблемы и как их решили

### 2.1 `401` / `insufficient_scope` при `crm.lead.list` и `crm.status.list`

**Симптом:** HTTP 401, в JSON часто `insufficient_scope` — «запрос требует больших привилегий, чем даёт токен вебхука».

**Причина:** у входящего вебхука не отмечены права на **CRM** (и при необходимости **Пользователи**). Вебхук только с открытыми линиями / без `crm` CRM-методы не вызывает.

**Решение:** в Битрикс24 в настройках вебхука включить минимум **CRM (`crm`)** и **`user`**, сохранить, при необходимости **скопировать новый URL** (секрет может смениться) в **`BITRIX24_WEBHOOK_URL`**.

---

### 2.2 `INVALID_CREDENTIALS`

**Симптом:** ошибка `INVALID_CREDENTIALS` в теле ответа.

**Причины (типично):**

- неверный или **отозванный** секрет в URL;
- в **`.env`** попал **неполный** URL или лишние символы;
- после смены прав вебхука Битрикс выдал **новый** URL — старый больше не действует.

**Решение:** заново скопировать строку «Вебхук для вызова rest api» целиком, в конце **`/`**, без лишнего `profile.json` в пути к секрету, обновить `.env`, перезапустить бэкенд.

---

### 2.3 Переменная **`BITRIX24_WEBHOOK_URL`** не подхватывалась

**Симптом:** казалось, что URL в корневом `.env` указан верно, но запросы шли со старыми/пустыми данными → снова **`INVALID_CREDENTIALS`** или странное поведение.

**Причина:** **`load_dotenv()`** без пути ищет `.env` в **текущей рабочей директории**. При запуске **`cd backend && uvicorn ...`** файл **`SmartCRM/.env`** из корня репозитория **не загружался**.

**Решение:** в **`main.py`** загрузка **`backend/.env`**, затем **`Path(__file__).resolve().parent.parent / ".env"`** с **`override=True`**.

**Дополнительно:** значение URL **обрезаются обрамляющие кавычки** в `webhook_base()`.

---

### 2.4 `httpx` и «тихий» успех при ошибке Битрикса

**Симптом:** лог с **401** и трейсом **`raise_for_status`**, а API импорта отдавал **200** с пустой статистикой.

**Причина:** ответ Битрикса с ошибкой часто приходит с **HTTP 401**, но с **JSON** в теле (`error`, `error_description`). Вызов **`raise_for_status()`** до разбора JSON превращал это в исключение; часть логики глотала ошибку и возвращала «успех» с `error_count`.

**Решение:**

- разбор ответа **без** слепого `raise_for_status`: сначала JSON, затем маппинг кодов в **`BitrixWebhookError`** с текстом на русском;
- для **`BitrixWebhookError`** эндпоинт импорта отдаёт **403** с деталями;
- импорт **не подавляет** `BitrixWebhookError` в цикле — сразу пробрасывается наверх.

---

### 2.5 Порт **`Address already in use` (8000)**

**Причина:** уже запущен другой процесс **`uvicorn`** на том же порту.

**Решение:** завершить процесс (`kill` / диспетчер задач) или выбрать другой порт.

---

### 2.6 Как понять, выгружен ли **весь** список лидов

Логика импорта при **`max_items: 0`**: перебор страниц, пока в ответе есть **`next`**.

**Критерии проверки:**

- в ответе импорта **`bitrix_total`** (если Битрикс отдал поле `total`) и **`total_processed`** должны быть **согласованы** (после полного прогона — близки; полное равенство зависит от того, отдаёт ли портал `total` и совпадает ли фильтр с «экспортом в Excel»);
- **`local_bitrix_leads_count`** — сколько у нас записей с **`bitrix_lead_id`** (по смыслу накопленный импорт, не только один запуск);
- **`stopped_by_limit: false`** при **`max_items: 0`** — обрез по лимиту не использовался;
- **`GET /api/leads/bitrix-import-stats`** — быстрая сводка **N в Битриксе / M у нас**.

Расхождения с Excel (~10k строк, из них «нормальных» меньше) обычно из‑за **другого фильтра**, дублей, пустых строк или выгрузки не только лидов.

---

## 3. Полезные команды

```bash
# Тесты к живому порталу (нужен BITRIX24_WEBHOOK_URL в .env в корне репо)
cd backend
python -m pytest tests/test_bitrix_integration.py -v
```

```bash
# Сводка без полного импорта
curl "http://127.0.0.1:8000/api/leads/bitrix-import-stats?date_from=2023-01-01"
```

---

## 4. Файлы (ориентир)

| Область | Путь |
|--------|------|
| Клиент Битрикс | `backend/integrations/bitrix24.py` |
| Роуты лидов | `backend/api/routes/leads.py` |
| Модель лида | `backend/db/models/lead.py` |
| Миграции колонок | `backend/db/session.py` |
| Точка входа, `.env` | `backend/main.py` |
| UI лидов | `frontend/src/routes/leads/+page.svelte` |
| API с фронта | `frontend/src/lib/leadsStorage.js` |
| Интеграционные тесты | `backend/tests/test_bitrix_integration.py` |

---

*Документ отражает состояние на момент внедрения; при смене версии REST Битрикс24 возможны отличия в полях `total` и пагинации.*
