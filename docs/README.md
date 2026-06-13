# Документация SmartCRM

Карта всех документов проекта. Начинайте отсюда.

---

## С чего начать

| Задача | Файл |
|--------|------|
| Чеклисты фаз (проходим по порядку) | [product/PRD_MAP.md](product/PRD_MAP.md) — сценарии Ф1 → техтаблицы; **⚠️**=хвост BACKLOG |
| Полный PRD | [product/PRD.md](product/PRD.md) |
| Черновики и детали модулей | [product/PRD_NOTES.md](product/PRD_NOTES.md) |
| Понять устройство системы | [product/ARCHITECTURE.md](product/ARCHITECTURE.md) |
| Запустить локально | [start/SETUP.md](start/SETUP.md) |
| Как идёт запрос, LLM, пути данных | [start/RUNBOOK.md](start/RUNBOOK.md) |

---

## Какой документ когда открывать

| Ситуация | Документ |
|----------|----------|
| Новая сессия агента | **`operations/session/PHASE2_ENTRY.md`** (Ф2) → `HANDOFF.md` → `SESSION_STATE.md` → `ISSUES.md` 🔴 |
| Что строим | `product/PRD_MAP.md` → `product/PRD.md` |
| Как устроено технически | `product/ARCHITECTURE.md` |
| Стек, API, БД | `product/ARCHITECTURE.md#справочник-стека` |
| Что сломалось | `operations/session/ISSUES.md` |
| Хвост / отложено | `operations/session/BACKLOG.md` |
| Как запустить | `start/RUNBOOK.md` |
| Агенты / Hermes | `agents/langgraph.md` |
| LLM политика | `stack/LLM.md` |
| История изменений | `operations/session/CHANGELOG.md` |

**Три канона:** `PRD.md` (продукт) · `ARCHITECTURE.md` (техника) · `CHANGELOG.md` (история).

**Агент:** HANDOFF → PRD_MAP → модульный doc → код → commit + ops (`smartcrm-commit-ops.mdc`).

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
| **[operations/](operations/)** | [`operations/README.md`](operations/README.md) — session, baselines, phase1/, phase2/, debt |
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

Структура: [`operations/README.md`](operations/README.md).

Обновляется агентами в процессе работы:

- [CHANGELOG.md](operations/session/CHANGELOG.md) — **история** (формат записи, хронология, статус продукта)
- [PHASE2_ENTRY.md](operations/session/PHASE2_ENTRY.md) — **вход в Ф2** (2026-06-13): git, хвосты Ф1, gate, порядок очереди
- [HANDOFF.md](operations/session/HANDOFF.md) — статус задачи, следующий шаг
- [SESSION_STATE.md](operations/session/SESSION_STATE.md) — краткий прогресс сессии
- [ISSUES.md](operations/session/ISSUES.md) — баги и инциденты
- [BACKLOG.md](operations/session/BACKLOG.md) — отложено по PRD_MAP

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
