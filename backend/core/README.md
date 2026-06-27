# Core — ядро бэкенда

Бизнес-логика, LLM, голосовой разбор (Hermes), auth, CRM-правила, ops. **Не HTTP** — роуты только вызывают отсюда.

---

## Пакет `hermes/` — голос → интент

Разбирает фразу пользователя в `{ intent, agents, slots }`.

| Файл | За что |
|------|--------|
| `__init__.py` | Публичный API: `parse_intent`, `SYSTEM_PROMPT` |
| `parse.py` | Главный разбор: Groq → Ollama → rescue |
| `config.py` | Модели, таймауты, rollout-флаги |
| `prompts.py` / `prompts_data.py` | Системный промпт Hermes |
| `providers.py` | Вызов Groq / Ollama |
| `rescue.py` | Подстраховка при битом JSON |
| `cache.py` | Кэш интентов |
| `json_parse.py` | Парсинг JSON из ответа LLM |
| `text_utils.py` | Нормализация текста |

Импорт снаружи: `from core.hermes import parse_intent`.

| `slot_normalize.py` | Нормализация слотов/агентов после LLM и rescue |
| `module_contract.py` | Ф2: module + intent + ui_action |

---

## Пакет `qa/` — QA-агент для тендеров

Эксперименты и статистика по источникам закупок.

| Файл | За что |
|------|--------|
| `agent.py` | Запуск QA-агента |
| `config.py` | Настройки |
| `experiments.py` | A/B и прогоны |
| `registry.py` | Реестр источников |
| `stats.py` | Метрики |
| `tools.py` | Инструменты агента |
| `prompts_data.py` | Промпты |

Shim: `qa_agent.py` — re-export для старых импортов.

---

## Файлы в корне `core/`

| Файл | За что |
|------|--------|
| `lead_close_forecast.py` | Прогноз закрытия сделки по стадии и баллу (Экономист) |
| `agent_trace_analytics.py` | Эффективность агентов по трейсам (👍/👎, интенты) |
| `analytics_metrics.py` | KPI воронки, когорты, воронка по источнику, CSV |
| `export_reports.py` | Excel/PDF: воронка, карточка лида, тендеры, баллы+воронка |
| `llm.py` | Общий чат с LLM (Groq/Ollama), json_mode |
| `auth.py` | API-ключ, `require_api_key` |
| `crypto.py` | Шифрование секретов (почта и т.п.) |
| `email_config.py` | IMAP/SMTP аккаунты из env (`EMAIL_APP_PASSWORD`, `EMAIL_ACCOUNT_*`) |
| `traces.py` | Логирование трейсов Hermes |
| `stats.py` | Счётчики вызовов внешних API |
| `eval_runner.py` | Прогон eval-сценариев; опц. `system_prompt` |
| `prompt_ab_traces.py` | A/B промптов на 👎 трейсах |
| `strategist_suggester.py` | Авто-суфлёр: слабые ответы → правки промптов |
| `agent_eval/` | Gate Ollama, загрузка кейсов, скоринг, sync acceptance-таблицы |
| `training_import.py` | Импорт training-датасетов |
| `ops_store.py` | Снимки ops-очереди |
| `ops_log_buffer.py` | Буфер логов для `/api/ops/logs` |
| `agent_memory.py` | Память агента (sqlite) |
| `voice_settings.py` | Настройки Whisper |
| `hermes_prompt_store.py` | Хранилище промптов Hermes |
| `agent_prompt_versions.py` | Git-like версии override промптов (агенты + Hermes) |
| `hermes_prompt_store.py` | Override Hermes + автоснимки в версии |
| `hermes_prompt_profiles.py` | Профили промптов |
| `crm_settings_store.py` | Настройки CRM (стадии, воронка, SLA-протоколы) |
| `sla_protocols.py` | Пресеты и нормализация SLA-протоколов, маркеры `sla_step:` в note задач |
| `scoring_funnel_report.py` | Отчёт по баллам лидов + воронка для экспорта P3 |
| `lead_approvals.py` | Согласования смены стадии лида |
| `lead_score_advisory.py` | Подсказки по скору лида |
| `lead_deal_path.py` | Цепочка квалификации и документов (путь сделки) |
| `lead_contacts.py` | Контакты лида, роли, ЛПР, `merge_bitrix_contacts` (ручные не затираются) |
| `lead_stage_hints.py` | Мульти-подсказки по этапу, срокам, докам |
| `lead_card_context.py` | Даты этапа и касаний для карточки |
| `lead_score_list_flags.py` | Флаги advisory для списка лидов (`hasScoreWarnings`, `scoreDivergent`) |
| `lead_task_list_flags.py` | Флаги задач в списке лидов (`taskDueToday`, `taskDueTomorrow`, `nextTaskTitle`) |
| `lead_day_priority.py` | Ранжирование «Мой день»: `dayRank`, этап+dealPath, intent задачи, затухание |
| `lead_day_priority_attach.py` | Прикрепление dayRank к списку лидов |
| `day_priority_config.py` | Дефолты и merge весов `crm_settings.day_priority` |
| `task_intent_note.py` | Маркер `intent:xxx` в note задачи (без миграции БД) |
| `lead_task_intents.py` | Классификация типа дела (intent → tier), каталог для dropdown |
| `lead_activities_query.py` | Список «дела по лидам» для `GET /api/leads/activities` |
| `lead_coverage.py` | Сегменты полноты карточки (B24, паспорт, пустые, проигран, без дел) |
| `lead_coverage_attach.py` | Прикрепление coverage-флагов к списку лидов |
| `lead_manager.py` | Менеджер лида: bitrix_extra.manager + responsible |
| `lead_manager_attach.py` | Поле `managerName` в списке лидов |
| `okved_industry_map.py` | Маппинг секции ОКВЭД → `industry_bucket` (укрупнённая отрасль) |
| `lead_products.py` | Нормализация `lead_products` (статус, цена, merge) |
| `lead_bitrix_extra.py` | UF Битрикс (подписка, поставка, лицензия…) → `lead.bitrix_extra` |
| `bitrix_lead_fields_sync.py` | Patch `bitrix_extra`/contacts/deal_amount при mass-resync |
| `bitrix_resync_guard.py` | Пауза auto-sync пока `resync_bitrix_lead_fields` status=running |
| `lead_deal_amount.py` | OPPORTUNITY + CURRENCY_ID → `deal_amount` / `deal_currency`, API `amount`/`currency` |
| `bitrix_webhook_scopes.py` | Scope вебхука (crm/user/task); activity-синк без task; `resolve_include_tasks_module` |
| `lead_priority_tier.py` | Приоритет лида по порогам CRM (зеркало `crmStages.js`) |
| `lead_profile.py` | Нормализация ОКВЭД, размер компании (`employees_band`), `portrait_score`, sync полей портрета |
| `lead_field_audit_util.py` | Аудит изменений полей лида |
| `stage_transition.py` | Правила перехода между стадиями |
| `task_dates.py` | Парсинг дат задач и статус SLA |
| `task_list_filter.py` | Фильтры списка задач: статус, срок, эскалация |
