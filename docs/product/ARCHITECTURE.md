# SmartCRM — Архитектура системы

## Общая схема

```
Пользователь (голос / UI)
       ↓
[SvelteKit — веб-интерфейс]
       ↓ WebSocket / HTTP
[FastAPI — бэкенд]
       ↓
[Groq Whisper] → текст → [Hermes — parse_intent]
                                ↓
                    [LangGraph оркестратор]
                    ↙  ↙  ↓  ↘  ↘
              Аналитик Стратег Экономист Маркетолог Тех.спец
                    ↘  ↘  ↓  ↙  ↙
                    [PostgreSQL / Redis / Chroma]
```

---

## Слои системы

### 1. Голосовой пайплайн

```
Аудио → Groq Whisper (STT) → текст
текст → Hermes (Groq и/или Ollama — см. `docs/stack/LLM.md`) → intent JSON
intent → LangGraph → нужный агент
```

Дополнительно в Hermes: **fastpath** (без LLM для простых фраз), **кэш**, опционально **память**, при недоступности моделей — **rescue**-эвристики (детерминированный роутинг).

### 2. LLM слой

- **Агенты (`core/llm.py`):** по умолчанию **Groq** (`GROQ_MODEL`, чаще `llama-3.1-8b-instant`) → при ошибке/лимите **Ollama** (`OLLAMA_MODEL`, например Qwen 2.5).
- **Hermes (`core/hermes.py`):** не «только локально»: при наличии `GROQ_API_KEY` и политике `default` сначала **Groq**, иначе **Ollama**; при `HERMES_ROUTING_POLICY=local_first` короткие low-risk фразы могут идти **сначала в Ollama**, затем Groq при необходимости. Цепочка локальных моделей: `HERMES_MODEL` → `HERMES_FALLBACK`.

### 3. Агентный слой (LangGraph)

- Агенты запускаются **параллельно** через LangGraph
- **Стратег** получает результаты от всех и принимает решение
- Каждый агент = промпт уровня PhD + набор инструментов

### 4. Поисковый слой → RAG

```
Запрос / контекст лида
      ↓
[Brave + Tavily + Serper] → сниппеты веб-поиска (где применимо)
      ↓
[rag/retrieve.py] — запросы в Chroma, форматирование контекста для агентов
      ↓
[Chroma] — векторная БД (`data/chroma_db`)
      ↓
Фрагменты в промпт агента перед ответом
```

**Hermes** здесь не парсит HTML выдачи; интенты для поиска задаётся отдельно (например `search_web` из Hermes → оркестратор → инструменты поиска). Путаницы с «Hermes фильтрует Google» избегаем — см. `docs/stack/RAG.md`.

### 5. Хранилище

- **PostgreSQL** — лиды, задачи, пользователи, история, eval-сценарии
- **Redis** — кэш, очереди, сессии WebSocket
- **Chroma** — векторная БД для RAG

---

## Поток голосовой команды

1. Нажал кнопку запись → браузер пишет аудио
2. WebSocket `/ws/voice` → FastAPI → Groq Whisper → текст
3. Текст → **Hermes** → JSON: `intent`, `module`, `slots`, `ui_action` (опционально)
4. Простой интент → handler API / один агент; комплексный → **Стратег** (supervisor, fanout)
5. Агенты работают; мутации → PostgreSQL
6. Ответ → WebSocket → **`voice_action`** → SvelteKit (навигация / модалка / фильтр / апрув)

> Не вводить отдельный Event Bus — расширять существующий WS тем же каналом.

---

## Контракт `voice_action`

Единый пакет от бэкенда на фронт (Фаза 1–2). Пример:

```json
{
  "type": "voice_action",
  "ui": "modal",
  "route": null,
  "title": "Анализ + письмо",
  "payload": {
    "analysis": {},
    "draft_email": { "subject": "", "body": "" },
    "actions": ["send", "save", "reject"]
  },
  "agents_used": ["analyst", "marketer"],
  "reply": "Краткий текст для TTS/чата"
}
```

| Поле `ui` | Поведение SvelteKit |
|-----------|---------------------|
| `navigate` | `route` обязателен → `goto(route)` |
| `modal` | оверлей поверх текущей страницы |
| `filter` | `payload.filter` → query/store списка |
| `approve` | блокирующий апрув перед `send` / delete |

Hermes для навигации: `{"intent":"navigate","ui_action":"navigate","slots":{"target":"/leads/123"}}`.

Голосовой CRUD лидов: существующие интенты `update_lead`, `create_task` + расширение слотов (`field`, `comment`, `communication_type`) — без обхода ORM.

См. также: `docs/product/PRD.md` (Voice Layer), `docs/agents/langgraph.md`.

---

## Безопасность

- LLM не выполняет произвольный код — только строгие intent handlers
- Нет произвольных SQL запросов от LLM — только через ORM
- Запросы к **Groq** уходят в облако (текст команды/контекст по политике продукта); **Ollama** остаётся локально на машине с `OLLAMA_HOST`
- Опционально защита API: `SMARTCRM_API_KEY` → заголовок `X-API-Key` (см. `docs/api/API.md`)

---

## Тендеры и внешние каталоги закупок

Отдельный поток UI (**`/tenders`**) и API **`/api/tenders`**: агрегация поиска (TenderGuru, Gosplan/EИС, обогащение DataNewton и др.), режим **планов закупок**, учёт вызовов в статистике лимитов. Подробно: `docs/modules/tenders.md`.

Маршруты **`/crm/*`** не дублируют вёрстку — редиректы на **`/leads/*`**. См. `docs/modules/leads.md`.

---

## Домен «Лиды» и балльный скоринг (архитектура фичи 2026-05)

### Цель архитектурного слоя

Дать **один детерминированный путь** расчёта `Lead.score` из конфигурируемых весов и состояния лида/задач, не ломая существующие HTTP-контракты `/api/leads` и UI `/leads/*`. LLM-агенты остаются **надстройкой качества**, а не скрытым источником операционного балла.

### Текущее состояние (as-is)

| Компонент | Расположение | Заметки |
|-----------|--------------|---------|
| Модель лида | `backend/db/models/lead.py` | Поля CRM + JSON обогащения; `stage`, `score`. |
| REST лидов | `backend/api/routes/leads/` | CRUD, Bitrix-импорт, engagement. |
| Настройки воронки | `backend/core/crm_settings_store.py`, файл `backend/data/crm_settings.json` | `stages`, `priority_thresholds`, `score_range`, `default_new_lead_score`. |
| Задачи | `backend/db/models/task.py`, роуты задач | `lead_id`, `sla_due`, `escalated`, `status`. |
| Фронт стадий/приоритета | `frontend/src/lib/crmStages.js`, маршруты `frontend/src/routes/leads/**` | `loadCrmConfig()`, бейджи приоритета. |

### Целевое состояние (to-be) — логическая схема

```
crm_settings.json (+ опционально lead_scoring_weights.json)
        │
        ▼
crm_settings_store (расширенный merge DEFAULT + файл)
        │
        ▼
lead_score_calculator (pure function + async gather задач при необходимости)
        │
        ▼
leads routes / task routes — после commit вызывают apply_score(lead_id)
        │
        ▼
PostgreSQL: leads.score (+ опционально leads.score_breakdown JSON / отдельная таблица логов)
```

### Решения по умолчанию (зафиксировано с PRD приложение C, 2026-05-04)

1. **Шкала:** `score_range` 0–100; подсказка `suggestedScore` тоже в 0–100.
2. **Победитель:** **`score` в БД задаёт только менеджер** (UI / прямой PATCH). Автоматика не перезаписывает `score`. Подсказка и `warnings` — в ответе `scoreAdvisory` на `GET/PATCH /api/leads/{id}`.
3. **Агенты и `score`:** при `manager_sets_score=true` и `agents_may_update_score=false` (дефолт) инструмент `update_lead_score` **не вызывает** PATCH по `score` (пропуск с `skipped: true`). Включить запись скора агентами можно в Ops, выставив `agents_may_update_score: true`.
4. **Деньги:** колонки `leads.amount_rub`, `leads.paid_amount_rub` (NUMERIC); в JSON API — `amountRub`, `paidAmountRub`.
5. **Апрувы (P3):** колонка `leads.approvals` (JSON, булевы ключи camelCase). Они **не** перезаписывают `score`; веса в `crm_settings.json` → `scoring_advisory.approval_weights` и `approval_bonus_cap` увеличивают только **`suggestedScore`** в `scoreAdvisory`. Лог касаний — таблица `lead_communication_logs`; расширение аудита — `lead_field_audits.event_type`, `metadata` (например запись при POST касания).

### Данные и миграции (план)

| Изменение | Назначение | Откат |
|-----------|------------|--------|
| Новые колонки на `leads` (P1) | `amount_rub`, `paid_amount_rub` NUMERIC(14,2) nullable | `ALTER TABLE … DROP COLUMN` |
| Таблица `lead_comments` (P2) | `id`, `lead_id`, `author`, `body`, `created_at` | drop table |
| Таблица `lead_field_audits` (P2) | поле, old, new, `changed_at`, `actor`; (P3) `event_type`, `metadata` | drop table / откат колонок |
| Колонка `leads.approvals` (P3) | JSON чеклиста апрувов | `DROP COLUMN` |
| Таблица `lead_communication_logs` (P3) | касания по лиду | drop table |
| Расширение JSON на диске | секция `scoring_weights` в `crm_settings.json` | восстановить файл из бэкапа |

**Migration Gate:** любые DDL только после явного `go`, с бэкапом БД в non-dev.

### Контракты API (план расширения)

| Метод | Путь | Поведение |
|-------|------|-----------|
| GET | `/api/crm/config` | Публично: `managerSetsScore`, `agentsMayUpdateScore`, `scoringAdvisoryEnabled` (+ воронка как раньше). |
| GET/PUT | `/api/ops/crm-settings` | Редактирование расширенного JSON (как сейчас для стадий). |
| PATCH | `/api/leads/{id}` | После успешного обновления — `recalculate_lead_score(lead_id)` (идемпотентно). |
| POST/PATCH | `/api/tasks/...` | При изменении `lead_id` или статуса задачи — пересчёт балла связанного лида. |
| GET | `/api/leads/{id}/comments` | Список комментариев к лиду (P2). |
| POST | `/api/leads/{id}/comments` | Добавить комментарий (`body`, `author`). |
| GET | `/api/leads/{id}/audit` | История изменений отслеживаемых полей лида (P2); элементы с `eventType` / `metadata` (P3). |
| GET/POST | `/api/leads/{id}/communications` | Лог касаний (P3). |

**P2 (код):** `PATCH /api/leads/{id}` проверяет `stage_transition_rules` из `crm_settings.json`, при успехе пишет строки в `lead_field_audits`; опциональный заголовок `X-Actor-Name` — для поля `actor` в аудите. Публичный `GET /api/crm/config` отдаёт `stageTransitionRules`.

**P3 (код):** в `PATCH` передаётся `approvals` (merge с дефолтами); `POST /communications` дублирует событие в аудите с `event_type=communication`.

Точные пути задач сверить с `backend/api/routes/tasks.py` (или актуальным модулем) при реализации — не дублировать бизнес-логику в двух местах: вынести `apply_lead_score_for_lead_id` в `core/`.

### Модульная раскладка файлов (предложение)

| Файл | Ответственность |
|------|-----------------|
| `backend/core/lead_score_calculator.py` | Чистая функция расчёта + типы входа/выхода. |
| `backend/core/lead_score_service.py` | Загрузка лида, агрегат задач, вызов калькулятора, `UPDATE` score. |
| `backend/core/crm_settings_store.py` | Merge новых ключей по умолчанию для весов. |
| Тесты `backend/tests/test_lead_score_calculator.py` | Фикстуры весов и сценарии краёв (отрицательный клиппинг, «Провал»). |

### Фронтенд (SvelteKit)

- Карточка лида: отобразить **балл**, **tier**, опционально tooltip с breakdown (если поле есть).
- Список: без смены URL; использовать уже загружаемый конфиг.
- Не тянуть тяжёлый breakdown в каждый row списка (только на карточке / по клику).

### Безопасность

- Веса и формулы не содержат секретов; файл в `backend/data/` не должен попадать в публичный репозиторий с продакшен-специфичными заметками — только шаблон в репо, реальные веса на сервере.
- API изменения `/api/crm/config` остаются **read-only** для клиента без Ops-ключа (как сейчас).

### Порядок внедрения (инкременты)

1. Конфиг + калькулятор + юнит-тесты (без DDL, «сухой прогон» из скрипта или временного эндпоинта dev-only — не в прод).
2. Миграция колонок (после `go`) + вызов сервиса из `leads` PATCH.
3. Хук в задачах + регрессионные тесты API.
4. P2: комментарии и аудит — реализовано (таблицы `lead_comments`, `lead_field_audits`, эндпоинты, UI карточки, правила стадий в CRM/Ops).
5. P3: `approvals`, `lead_communication_logs`, расширение аудита, веса апрувов в `lead_score_advisory`, UI на карточке лида.

### Наблюдаемость и отладка

- Структурированный лог при расхождении стадии лида и списка `stages` в конфиге (warning).
### Риски реализации и митигация

| Риск | Как снимаем |
|------|-------------|
| Циклический импорт routes ↔ service | Сервис в `core/`, роуты только вызывают публичную функцию. |
| Гонки при параллельных PATCH | Одна транзакция: обновление полей лида + score в одном commit или `SELECT … FOR UPDATE` при необходимости. |
| Дрейф весов без версии | Поле `scoring_weights_version` int в JSON, логировать в audit P2. |

---

## См. также

- Операционный обзор: `docs/start/RUNBOOK.md`
- Детали LLM и env: `docs/stack/LLM.md`
- Тендеры и планы закупок: `docs/modules/tenders.md`
- CRM и зеркальные URL лидов: `docs/modules/leads.md`
- Продуктовые требования к балльной воронке: `docs/product/PRD.md` (раздел фичи и приложения)

---

## Приложение к архитектуре — Псевдокод триггера

```
on_get_or_patch_lead(lead, tasks):
  settings = load_settings()
  if not settings.get("scoring_advisory_enabled", True):
    return { scoreAdvisory: disabled }
  return { scoreAdvisory: compute_lead_score_advisory(lead_dict, tasks, settings) }
```

---

## Приложение — Матрица совместимости с агентами

| Компонент | До фичи | После P1 |
|-----------|---------|----------|
| `analyst` / `update_lead_score` | Мог писать `score` в БД | По умолчанию **пропуск** (`skipped`), пока `agents_may_update_score=false`. |
| Hermes `create_lead` | Ставит дефолтный score | Остаётся `default_new_lead_score`, затем сервис может пересчитать на первом save. |

Конкретные правки в `backend/agents/*.py` — в таске реализации; архитектурно избегаем дублирования формулы вне `lead_score_calculator`.

---

## Приложение — Соответствие референс-Rails (traceability)

| Rails | SmartCRM (план) |
|-------|-----------------|
| `ScoreCalculator` | `lead_score_calculator.py` |
| `Setting#weights` | секция `scoring_weights` в JSON настроек |
| `after_save :apply_calculated_score` | явный вызов сервиса из роутов/Unit of Work |
| `LeadStateMachine` | P2: валидации переходов на API |
| `LeadComment` | P2: `lead_comments` |

---

## Приложение — Чеклист архитектурной готовности

- [ ] Зафиксирован формат JSON весов (JSON Schema опционально в `backend/schemas/`).
- [ ] Описан rollback DDL в `docs/operations/` или в теле миграции комментарием.
- [ ] Пройден smoke: создание лида → смена стадии → score обновился.

---

## Приложение — Границы ответственности модулей

**Запрещено:** копировать формулу в фронтенд как источник правды. Фронт только отображает результат с бэка.

**Разрешено:** дублировать **клиппинг** порогов приоритета на фронте для мгновенного UI при оптимистичных обновлениях — но источник порогов тот же `GET /api/crm/config`.

---

## Справочник стека

Принцип: каждый слой — одна ответственность. **Groq → Ollama** fallback для LLM.

```
┌─────────────────────────────────────┐
│  SvelteKit + Tailwind + Vite        │  /leads /email /agents /rag /ops
└──────────────┬──────────────────────┘
               │ HTTP / WebSocket
┌──────────────▼──────────────────────┐
│  FastAPI + asyncio                  │  REST + /ws/voice
└──────┬───────────┬──────────────────┘
       │           │
┌──────▼───┐  ┌────▼─────────────────┐
│PostgreSQL│  │  Redis (кэш, очереди, │
│лиды,     │  │  WS-сессии, трейсы)  │
│задачи    │  └──────────────────────┘
└──────────┘
       │
┌──────▼──────────────────────────────┐
│  LangGraph — Стратег + workers      │
└──────┬───────────┬──────────────────┘
       │           │
┌──────▼───┐  ┌────▼─────────────────┐
│  Groq    │  │  Ollama / Qwen       │
└──────────┘  └──────────────────────┘
       │
┌──────▼──────────────────────────────┐
│  Chroma — RAG (коллекции на агента) │
└─────────────────────────────────────┘
```

### Frontend (SvelteKit)

| Что | Детали |
|-----|--------|
| Роутинг | `/leads/*`, `/email`, `/agents`, `/rag`, `/ops` |
| Голос | WebSocket → Whisper → Hermes |
| Стор | `leadsStorage.js`, `crmStages.js` |
| Конфиг воронки | `loadCrmConfig()` → `GET /api/crm/config` |

### Backend (FastAPI)

| Что | Детали |
|-----|--------|
| ORM | SQLAlchemy async, `init_db` при старте |
| Пул | `pool_pre_ping=True`, `pool_recycle=280s` |
| WebSocket | `/ws/voice` |

Основные API:

```
/api/leads              — CRUD
/api/leads/{id}         — карточка + scoreAdvisory
/api/crm/config         — конфиг воронки
/api/ops/crm-settings   — настройки Ops
/api/tenders            — тендеры
/api/search             — поиск (режимы)
/api/rag                — база знаний
/ws/voice               — голос
```

### PostgreSQL — основные таблицы

```
leads, tasks, lead_comments, lead_field_audits, lead_communication_logs
```

Ключевые поля лида: `score`, `stage`, `amount_rub`, `paid_amount_rub`, `approvals` (JSON), `priority`.

### LangGraph

Паттерн: **supervisor + workers**. Сейчас агенты часто отвечают по отдельности; **Фаза 2** — полный fanout через Стратега. См. `docs/agents/langgraph.md`.

### Где настраивается

| Что | Где |
|-----|-----|
| LLM политика | `docs/stack/LLM.md`, `HERMES_ROUTING_POLICY` |
| Веса скоринга | Ops → CRM → JSON |
| Промпты агентов | Ops → Агенты |
| API ключи | `.env` + UI |
| Стадии воронки | Ops → CRM |
| RAG коллекции | `/rag` UI, `docs/stack/RAG.md` |

Ключи `.env`: `GROQ_API_KEY`, `BRAVE_SEARCH_API_KEY`, `TAVILY_API_KEY`, `SERPER_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `OLLAMA_HOST`, `HERMES_ROUTING_POLICY`.

---

## Статус документа (2026-06)

| Раздел | Статус |
|--------|--------|
| Домен лидов P1–P3 | **В коде** — разделы as-is/to-be выше описывают план; фактическое состояние сверять с `PRD_MAP` |
| Матрица агентов | Не отражает fanout Фазы 2 — см. `langgraph.md` |
| Порядок внедрения P1–P3 | Закрыт по MAP; новые инкременты — **Фаза 2** в `PRD_MAP.md` |

---

## Ключевые решения (сводка)

| Решение | Выбор | Почему |
|---------|-------|--------|
| Балл | Менеджер вручную | Предсказуемость |
| Подсказка | `suggestedScore` без записи в БД | Менеджер главный |
| Агенты и score | `agents_may_update_score=false` | Нет тихой перезаписи |
| Деньги | `amount_rub` NUMERIC | Точность |
| Аудит | Append-only | История не удаляется |
| Стадии | Из конфига | Без хардкода |
| Fallback LLM | Groq → Ollama | Независимость от провайдера |

---

## Приложение — Версионирование документа

| Дата | Изменение |
|------|-----------|
| 2026-06-08 | Справочник стека, статус документа, сводка решений (из PRD_NOTES). |
| 2026-05-04 | Добавлен раздел домена лидов, план данных/API/модулей, решения по умолчанию, traceability к Rails-референсу. |
