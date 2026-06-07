# Документация SmartCRM

Карта всех документов проекта. Начинайте отсюда.

---

## С чего начать

| Задача | Файл |
|--------|------|
| Чеклисты фаз (проходим по порядку) | [product/PRD_MAP.md](product/PRD_MAP.md) |
| Полный PRD | [product/PRD.md](product/PRD.md) |
| Черновики и детали модулей | [product/PRD_NOTES.md](product/PRD_NOTES.md) |
| Понять устройство системы | [product/ARCHITECTURE.md](product/ARCHITECTURE.md) |
| Запустить локально | [start/SETUP.md](start/SETUP.md) |
| Как идёт запрос, LLM, пути данных | [start/RUNBOOK.md](start/RUNBOOK.md) |

---

## Папки

| Папка | Что внутри |
|-------|------------|
| **[product/](product/)** | Продукт и архитектура (главный канон) |
| **[start/](start/)** | Установка и ежедневная работа с проектом |
| **[api/](api/)** | HTTP API, авторизация, [`openapi/`](api/openapi/) |
| **[modules/](modules/)** | Отдельные части продукта: лиды, лидоген, тендеры… |
| **[email/](email/)** | Почта: обзор, настройка, схема |
| **[voice/](voice/)** | Голосовые команды и фразы для лидов |
| **[agents/](agents/)** | AI-агенты LangGraph и Hermes |
| **[stack/](stack/)** | Технологии: LLM, RAG, SvelteKit, LangGraph |
| **[operations/](operations/)** | Журнал работы: HANDOFF, ISSUES, CHANGELOG |
| **[dev/](dev/)** | Для разработчиков: workflow, [REPO_LAYOUT](dev/REPO_LAYOUT.md), [LAYOUT_AUDIT](dev/LAYOUT_AUDIT.md), code review |
| **[archive/](archive/)** | Старые отчёты и тест-планы (не актуальный канон) |
| **[reference/](reference/)** | Клон референс-проекта CRM Points (только для сравнения) |

---

## Модули продукта (`modules/`)

| Файл | Тема |
|------|------|
| [leads.md](modules/leads.md) | Раздел «Лиды», URL `/leads`, скоринг, CRM-конфиг |
| [leadgen.md](modules/leadgen.md) | Лидогенерация |
| [tenders.md](modules/tenders.md) | Тендеры и закупки |
| [search.md](modules/search.md) | Поиск |
| [bitrix.md](modules/bitrix.md) | Импорт из Битрикс24 |

---

## Агенты (`agents/`)

| Файл | Тема |
|------|------|
| [langgraph.md](agents/langgraph.md) | Роли агентов, Hermes, оркестратор, API промптов |

---

## Операционка (`operations/`)

Обновляется агентами в процессе работы:

- [HANDOFF.md](operations/HANDOFF.md) — статус задачи, следующий шаг
- [SESSION_STATE.md](operations/SESSION_STATE.md) — краткий прогресс сессии
- [CHANGELOG.md](operations/CHANGELOG.md) — что сделано по шагам
- [ISSUES.md](operations/ISSUES.md) — баги и инциденты

---

## Старые пути (куда переехало)

| Было (плоский `docs/`) | Стало |
|------------------------|-------|
| `docs/PRD.md` | `docs/product/PRD.md` |
| `docs/ARCHITECTURE.md` | `docs/product/ARCHITECTURE.md` |
| `docs/SETUP.md` | `docs/start/SETUP.md` |
| `docs/API.md` | `docs/api/API.md` |
| `docs/LEADGEN.md` | `docs/modules/leadgen.md` |
| `docs/TENDERS.md` | `docs/modules/tenders.md` |
| `docs/SEARCH.md` | `docs/modules/search.md` |
| `docs/BITRIX24_IMPORT.md` | `docs/modules/bitrix.md` |
| `docs/CRM_ROUTES.md` | `docs/modules/leads.md` |
| `docs/EMAIL.md` | `docs/email/overview.md` |
| `docs/EMAIL_SETUP_GUIDE.md` | `docs/email/setup.md` |
| `docs/email_architecture.md` | `docs/email/architecture.md` |
| `docs/VOICE_COMMANDS.md` | `docs/voice/commands.md` |
| `docs/VOICE_LEAD_PHRASES.md` | `docs/voice/lead-phrases.md` |
| `docs/AGENTS.md` | `docs/agents/langgraph.md` |
| `docs/code-reviewer-agent.md` | `docs/dev/code-review.md` |
| `docs/AGENTS_TEST_RESULTS.md` | `docs/archive/` |
| `docs/EMAIL_TEST_PLAN.md` | `docs/archive/` |
