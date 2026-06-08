# Tests — автотесты backend

```bash
cd backend
pytest                    # всё
pytest tests/test_leadgen.py -q
pytest tests/api/ -q
```

Конфиг: `pytest.ini`, фикстуры: `conftest.py`.

---

## Подпапки (зеркало кода)

| Папка | Что тестирует |
|-------|----------------|
| `api/` | `test_leads_api.py`, `test_eval_scenarios_api.py` |
| `core/` | `test_hermes_eval.py`, `test_qa_agent.py` |
| `agents/` | `test_analyst.py` |
| `rag/` | `test_search_pkg.py`, `test_rag_chunks.py` |
| `integration/` | `test_email_integration.py` — смоук почты |

---

## Файлы в корне `tests/`

| Файл | За что |
|------|--------|
| `test_leadgen.py` | Пайплайн, Checko, портрет, интеграция |
| `test_voice_pipeline.py` | Hermes интенты, orchestrator, голос |
| `test_tender_sources.py` | Источники тендеров |
| `test_stage_transition.py` | Переходы стадий CRM |
| `lib/test_funnel_dnd.py` | Воронка Kanban DnD (зеркало funnelDnD.js) |
| `lib/test_lead_list_filter.py` | Фильтры и сортировка списка лидов |
| `lib/test_lead_card_money.py` | Суммы ₽ на карточке лида |
| `api/test_lead_engagement.py` | Комментарии, касания, апрувы |
| `core/test_task_dates.py` | Даты и SLA задач |
| `api/test_tasks_api.py` | CRUD задач, lead_id, overdue |
| `api/test_lead_comments_api.py` | Комментарии: 404, пустой body, порядок, x-actor-name |
| `test_lead_score_advisory.py` | Скор-советы |
| `test_review_fixes.py` | Регрессии по code review |
| `test_agents.py` | Агенты |
| `test_search.py` | Поиск |
| `test_email_sync.py` | Синхронизация почты |
| `test_bitrix_integration.py` | Битрикс live (REST вебхук) |
| `integrations/test_bitrix_row_map.py` | Маппинг полей Битрикс → Lead |
| `integrations/test_bitrix_webhook.py` | Исходящий вебхук ONCRMLEADADD |

---

## `fixtures/leadgen/`

JSON и txt для моков Checko, BuiltWith, пайплайна — не менять без обновления тестов.
