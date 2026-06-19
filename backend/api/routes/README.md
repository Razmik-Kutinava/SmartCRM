# API Routes

Все HTTP/WebSocket эндпоинты SmartCRM. Собираются в [`main.py`](../../main.py).

---

## Пакеты (подпапки)

### `leads/` — `/api/leads`

CRUD лидов, вовлечённость, Битрикс.

| Файл | За что |
|------|--------|
| `__init__.py` | Сборка роутера |
| `crud.py` | Список, создать, lookalike-import, справочник отраслей `/industries`, прочитать, обновить (`products_owned`), удалить лид |
| `analytics_routes.py` | Сводка KPI и экспорт `/analytics/summary`, `/analytics/export` — query `period`, `source`, `format=csv|xlsx|pdf` |
| `export_routes.py` | PDF карточки лида `GET /{lead_id}/export?format=pdf` |
| `csv_routes.py` | CSV базы лидов `POST /import-csv`, `GET /export?format=csv` |
| `engagement.py` | Комментарии, логи связи, аудит полей, стадии |
| `bitrix_routes.py` | Импорт лидов из Битрикс24, статус синка |
| `presenter.py` | Как отдать лид в JSON для API |
| `schemas.py` | Pydantic-схемы запросов/ответов |

### `ops/` — `/api/ops`

Панель оператора: качество голоса, eval, трейсы, логи.

| Файл | За что |
|------|--------|
| `__init__.py` | Сборка роутера |
| `dashboard_routes.py` | Сводка дашборда ops |
| `traces_routes.py` | История запросов Hermes, `/stats`, фидбек |
| `analytics_routes.py` | `GET /analytics/agents` — эффективность агентов по трейсам |
| `hermes_routes.py` | Hermes: промпт, версии, few-shot, suggest-prompt, **ab-traces** |
| `voice_routes.py` | Голосовые настройки, история команд (`GET /voice/history`) |
| `eval_routes.py` | Прогон eval Hermes; статус Ollama |
| `eval_gate_routes.py` | Gate: latest+delta, download, run, ensure-dataset, failed→bulk |
| `eval_cases.py` | CRUD eval-кейсов |
| `strategist_routes.py` | Авто-суфлёр: suggest/apply правок промптов |
| `agents_routes.py` | Промпты агентов: CRUD, версии, откат, compare, тест-run |
| `logs_routes.py` | Буфер логов для UI |
| `crm_routes.py` | CRM-настройки в ops |
| `lead_hunt_routes.py` | Авто-поиск: status, config, run, queue, **approve-above**, notifications |
| `schemas.py` | Общие схемы ops |

### `tenders/` — `/api/tenders`

Поиск и карточки госзакупок.

| Файл | За что |
|------|--------|
| `__init__.py` | Сборка роутера |
| `search_routes.py` | Поиск тендеров (Gosplan, TenderGuru, Serper/Tavily) |
| `web_search.py` | Serper+Tavily → карточки тендеров в `/search` |
| `detail_routes.py` | Карточка тендера, `POST /save` в БД |
| `saved_routes.py` | Мои/Архив: `GET/POST/PATCH /saved`, экспорт `GET /saved/export?format=xlsx|pdf` |
| `analyze_routes.py` | `POST /analyze` — коммерческий/тех. агент |
| `evaluate_routes.py` | `POST /evaluate` — fanout tech∥economist→strategist; ответ `participation` (вердикт) |
| `lead_link_routes.py` | `link-lead` / `create-lead` — связь тендера с лидом CRM |
| `document_routes.py` | `POST /documents/extract` — текст из PDF/DOCX/XLSX |
| `doc_extract.py` | Парсинг документов для тендеров (pypdf и др.) |
| `plans_routes.py` | Планы закупок |
| `classifiers_routes.py` | Классификаторы ОКПД/ОКВЭД |
| `monitor_routes.py` | `GET/PUT /monitor/config`, `/status`, `POST /run` — фоновый мониторинг 24/7 |
| `calendar_routes.py` | `/notifications`, `/calendar/month`, scan-deadlines |
| `helpers.py` | Фильтры, релевантность, нормализация для UI |
| `config.py` | Конфиг источников тендеров |

---

## Отдельные файлы (в корне `routes/`)

| Файл | URL-префикс | За что |
|------|-------------|--------|
| `voice.py` | `/api/voice` | Голос: текст/аудио → Hermes → агенты |
| `leadgen.py` | `/api/leadgen` | Пайплайн, кластер, портрет; `/save` dedup; `GET /won-portrait` — портрет из won-сделок |
| `crm.py` | `/api/crm` | Публичные CRM: стадии, настройки |
| `webhooks_bitrix.py` | `/api/webhooks/bitrix` | Исходящие события Битрикс24 (ONCRMLEADADD) |
| `leads/` | `/api/leads` | См. пакет выше |
| `tasks.py` | `/api/tasks` | Задачи по лидам, SLA, фильтр `lead_id` |
| `email.py` | `/api/email` | IMAP/SMTP; nurture: `/nurture/preview-llm`, `/start-llm` (`chain_type`: new/cross/upsell), `/start`, `/start-segment`, `/process-due`, `GET /nurture/chains`; кампании: `/campaign/preview-llm`, `/test-send`, `send_now` (фильтр `industries[]`) |
| `agent_email.py` | `/api/agent-email` | AI-черновики писем по лиду |
| `search.py` | `/api/search` | Поиск компаний; `enrich-lead` + кэш enrich; `auto-ingest-rag` |
| `rag.py` | `/api/rag` | Загрузка документов, `ingest-dialogue`, **`/vendor-crawl`** (краулинг вендоров → tec) |
| `news.py` | `/api/news` | Новости по компании |
| `usage.py` | `/api/usage` | Лимиты внешних API (Checko и др.) |
| `eval_scenarios.py` | `/api/eval-scenarios` | Сценарии для eval |
| `training_datasets.py` | `/api/training-datasets` | Датасеты для дообучения |
| `ops/` | `/api/ops` | См. пакет выше |
| `tenders/` | `/api/tenders` | См. пакет выше |
