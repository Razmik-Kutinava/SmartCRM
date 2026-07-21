# Документация SmartCRM

Карта всех документов проекта. Начинайте отсюда.

---

## С чего начать

| Задача | Файл |
|--------|------|
| Видение: что и зачем строим | [product/VISION.md](product/VISION.md) |
| План фаз и статусы | [product/ROADMAP.md](product/ROADMAP.md) |
| Чеклист активной фазы (Ф4) | [operations/phase4/CHECKLIST.md](operations/phase4/CHECKLIST.md); закрытые Ф1–Ф3 — `operations/phase{1,2,3}/CHECKLIST.md` |
| Полный PRD | [product/PRD.md](product/PRD.md) |
| Сквозные бизнес-процессы | [product/BUSINESS_LOGIC.md](product/BUSINESS_LOGIC.md) |
| Главные функции системы | [product/FUNCTIONAL.md](product/FUNCTIONAL.md) |
| Дизайн-система UI | [product/DESIGN_SYSTEM.md](product/DESIGN_SYSTEM.md) |
| Понять устройство системы | [product/ARCHITECTURE.md](product/ARCHITECTURE.md) |
| Запустить локально | [start/SETUP.md](start/SETUP.md) |
| Как идёт запрос, LLM, пути данных | [start/RUNBOOK.md](start/RUNBOOK.md) |
| Исходящий вебхук B24 + ngrok (когда настроим) | [start/BITRIX_OUTBOUND_WEBHOOK.md](start/BITRIX_OUTBOUND_WEBHOOK.md) |

---

## Какой документ когда открывать

| Ситуация | Документ |
|----------|----------|
| Новая сессия агента | `HANDOFF.md` → `SESSION_STATE.md` → `ISSUES.md` 🔴 |
| Что строим | `product/VISION.md` → `product/ROADMAP.md` → `operations/phase4/CHECKLIST.md` |
| Как устроено технически | `product/ARCHITECTURE.md` |
| Стек, API, БД | `product/ARCHITECTURE.md#справочник-стека` |
| Что сломалось | `operations/session/ISSUES.md` |
| Хвост / отложено | `operations/session/BACKLOG.md` |
| Как запустить | `start/RUNBOOK.md` |
| Агенты / Hermes | `agents/langgraph.md` |
| LLM политика | `stack/LLM.md` |
| История изменений | `operations/session/CHANGELOG.md` |

**Три канона:** `PRD.md` (продукт) · `ARCHITECTURE.md` (техника) · `CHANGELOG.md` (история).

**Агент:** HANDOFF → чеклист фазы → модульный doc → код → commit + ops ([`workflow/smartcrm-commit-ops.mdc`](../.cursor/rules/workflow/smartcrm-commit-ops.mdc)).

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
| **[operations/](operations/)** | [`operations/README.md`](operations/README.md) — session, baselines, phase1–4 (CHECKLIST + acceptance), debt |
| **[dev/](dev/)** | Для разработчиков: workflow, [REPO_LAYOUT](dev/REPO_LAYOUT.md), [LAYOUT_AUDIT](dev/LAYOUT_AUDIT.md), code review |
| **[archive/](archive/)** | Не актуальный канон: `ops/` — журналы по месяцам, `product/` — PRD_NOTES/DELTA/чеклисты Ф1–Ф3 |
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
- [HANDOFF.md](operations/session/HANDOFF.md) — статус задачи, следующий шаг
- [SESSION_STATE.md](operations/session/SESSION_STATE.md) — краткий прогресс сессии
- [ISSUES.md](operations/session/ISSUES.md) — баги и инциденты
- [BACKLOG.md](operations/session/BACKLOG.md) — отложено по пунктам чеклистов фаз

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
