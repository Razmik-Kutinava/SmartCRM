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

| `hermes/slot_normalize.py` | Нормализация слотов/агентов после LLM и rescue |

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
| `llm.py` | Общий чат с LLM (Groq/Ollama), json_mode |
| `auth.py` | API-ключ, `require_api_key` |
| `crypto.py` | Шифрование секретов (почта и т.п.) |
| `traces.py` | Логирование трейсов Hermes |
| `stats.py` | Счётчики вызовов внешних API |
| `eval_runner.py` | Прогон eval-сценариев |
| `training_import.py` | Импорт training-датасетов |
| `ops_store.py` | Снимки ops-очереди |
| `ops_log_buffer.py` | Буфер логов для `/api/ops/logs` |
| `agent_memory.py` | Память агента (sqlite) |
| `voice_settings.py` | Настройки Whisper |
| `hermes_prompt_store.py` | Хранилище промптов Hermes |
| `hermes_prompt_profiles.py` | Профили промптов |
| `crm_settings_store.py` | Настройки CRM (стадии, воронка) |
| `lead_approvals.py` | Согласования смены стадии лида |
| `lead_score_advisory.py` | Подсказки по скору лида |
| `lead_priority_tier.py` | Приоритет лида по порогам CRM (зеркало `crmStages.js`) |
| `lead_field_audit_util.py` | Аудит изменений полей лида |
| `stage_transition.py` | Правила перехода между стадиями |
| `task_dates.py` | Парсинг дат задач и статус SLA |
