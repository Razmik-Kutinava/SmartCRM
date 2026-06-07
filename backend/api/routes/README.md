# API Routes

Все HTTP/WebSocket эндпоинты SmartCRM. Собираются в [`main.py`](../../main.py).

---

## Пакеты (подпапки)

### `leads/` — `/api/leads`

CRUD лидов, вовлечённость, Битрикс.

| Файл | За что |
|------|--------|
| `__init__.py` | Сборка роутера |
| `crud.py` | Список, создать, прочитать, обновить, удалить лид |
| `engagement.py` | Комментарии, логи связи, аудит полей, стадии |
| `bitrix_routes.py` | Импорт лидов из Битрикс24 |
| `presenter.py` | Как отдать лид в JSON для API |
| `schemas.py` | Pydantic-схемы запросов/ответов |

### `ops/` — `/api/ops`

Панель оператора: качество голоса, eval, трейсы, логи.

| Файл | За что |
|------|--------|
| `__init__.py` | Сборка роутера |
| `dashboard_routes.py` | Сводка дашборда ops |
| `traces_routes.py` | История запросов Hermes |
| `hermes_routes.py` | Настройки и тюнинг Hermes |
| `voice_routes.py` | Голосовые настройки и смоук |
| `eval_routes.py` | Прогон eval-сценариев |
| `eval_cases.py` | CRUD eval-кейсов |
| `agents_routes.py` | Запуск и логи агентов |
| `logs_routes.py` | Буфер логов для UI |
| `crm_routes.py` | CRM-настройки в ops |
| `schemas.py` | Общие схемы ops |

### `tenders/` — `/api/tenders`

Поиск и карточки госзакупок.

| Файл | За что |
|------|--------|
| `__init__.py` | Сборка роутера |
| `search_routes.py` | Поиск тендеров |
| `detail_routes.py` | Карточка тендера |
| `plans_routes.py` | Планы закупок |
| `classifiers_routes.py` | Классификаторы ОКПД/ОКВЭД |
| `helpers.py` | Фильтры, релевантность, нормализация для UI |
| `config.py` | Конфиг источников тендеров |

---

## Отдельные файлы (в корне `routes/`)

| Файл | URL-префикс | За что |
|------|-------------|--------|
| `voice.py` | `/api/voice` | Голос: текст/аудио → Hermes → агенты |
| `leadgen.py` | `/api/leadgen` | Запуск пайплайна, кластер, портрет |
| `crm.py` | `/api/crm` | Публичные CRM: стадии, настройки |
| `leads/` | `/api/leads` | См. пакет выше |
| `tasks.py` | `/api/tasks` | Задачи по лидам |
| `email.py` | `/api/email` | Настройки IMAP/SMTP, синхронизация |
| `agent_email.py` | `/api/agent-email` | AI-черновики писем по лиду |
| `search.py` | `/api/search` | Поиск компаний (RAG + веб) |
| `rag.py` | `/api/rag` | Загрузка документов, поиск в Chroma |
| `news.py` | `/api/news` | Новости по компании |
| `usage.py` | `/api/usage` | Лимиты внешних API (Checko и др.) |
| `eval_scenarios.py` | `/api/eval-scenarios` | Сценарии для eval |
| `training_datasets.py` | `/api/training-datasets` | Датасеты для дообучения |
| `ops/` | `/api/ops` | См. пакет выше |
| `tenders/` | `/api/tenders` | См. пакет выше |
