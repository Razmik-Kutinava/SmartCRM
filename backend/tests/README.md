# Tests — автотесты backend

```bash
cd backend
python -m venv .venv && .\.venv\Scripts\Activate.ps1   # или source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q                    # регрессия (без live_eval)
python -m pytest --cov=. --cov-config=.coveragerc --cov-report=term-missing   # coverage
python -m pytest -m live_eval tests/core/test_hermes_eval.py   # live LLM eval
python scripts/ci_smoke.py             # smoke ops/leads/voice
```

Конфиг: `pytest.ini`, `.coveragerc`, фикстуры: `conftest.py`. Baseline %: `docs/operations/COVERAGE_BASELINE.md`. CI: `.github/workflows/ci.yml`, `docs/operations/CI_BASELINE.md`.

## Правило: тест на фичу

Каждый PR с новым/изменённым backend-кодом → **≥1 pytest** в зеркальной папке `tests/` (happy path, моки). Чеклист: `docs/dev/PR_CHECKLIST.md`. Регрессия в CI без `--cov-fail-under`.

**По умолчанию:** `14 deselected` = маркер `live_eval` (live Groq) — не баг. Запуск: `python -m pytest -m live_eval tests/core/test_hermes_eval.py`.

---

## Подпапки (зеркало кода)

| Папка | Что тестирует |
|-------|----------------|
| `api/` | `test_leads_api.py`, `test_search_providers_api.py`, `test_eval_scenarios_api.py` |
| `core/` | `test_hermes_eval.py`, `test_qa_agent.py` |
| `agents/` | `test_analyst.py` |
| `rag/` | `test_search_providers.py`, `test_search_pkg.py`, `test_rag_chunks.py`, `test_search_modes.py` |
| `api/` | `test_rag_api.py`, `test_rag_upload_api.py`, `test_rag_ingest_batch_api.py`, `test_search_enrich_lead_api.py` |
| `rag/` | + `test_rag_upload.py`, `test_rag_ingest_batch.py` — ingest_bytes, metadata batch |
| `integration/` | `test_email_integration.py` — смоук почты |

---

## Файлы в корне `tests/`

| Файл | За что |
|------|--------|
| `leadgen/test_inn_constants.py` | Канон ИНН мок vs live (Хохланд) |
| `test_leadgen.py` | Пайплайн, Checko, портрет, интеграция |
| `api/test_leadgen_analyze_api.py` | POST `/api/leadgen/analyze` (ИНН, название, 400) |
| `api/test_leadgen_portrait_api.py` | POST `/api/leadgen/portrait` (эталон ИНН, текст, deep) |
| `api/test_leadgen_cluster_api.py` | POST `/api/leadgen/cluster` (ИНН якоря, 400) |
| `leadgen/test_cluster.py` | `run_cluster` mock: дочка + материнская |
| `test_voice_pipeline.py` | Hermes интенты, orchestrator, голос |
| `voice/test_voice_action.py` | Сборка пакета voice_action |
| `api/test_voice_action_ws.py` | WS события intent + voice_action |
| `core/test_hermes_lead_extended.py` | analyze_lead, lead_history, stage-фильтры |
| `core/test_lead_list_view.py` | Маппинг list_leads → UI |
| `voice/test_lead_context.py` | Загрузка истории лида |
| `smoke/test_voice_lead_scenarios.py` | Матрица S01–S09 голосовых сценариев лидов |
| `test_tender_sources.py` | Источники тендеров |
| `smoke/test_tenders_baseline_smoke.py` | Смоук `/api/tenders/search`, save, web |
| `api/test_tenders_saved_api.py` | Мои/Архив, analyze, POST /save |
| `api/test_tenders_web_search.py` | Маппинг Serper/Tavily → карточки |
| `api/test_tenders_document_extract.py` | PDF extract + document_text в analyze |
| `test_stage_transition.py` | Переходы стадий CRM |
| `lib/test_funnel_dnd.py` | Воронка Kanban DnD (зеркало funnelDnD.js) |
| `lib/test_lead_list_filter.py` | Фильтры и сортировка списка лидов |
| `lib/test_lead_card_money.py` | Суммы ₽ на карточке лида |
| `api/test_lead_engagement.py` | Комментарии, касания, апрувы |
| `core/test_task_dates.py` | Даты и SLA задач |
| `api/test_tasks_api.py` | CRUD задач, lead_id, overdue |
| `api/test_lead_comments_api.py` | Комментарии: 404, пустой body, порядок, x-actor-name |
| `core/test_lead_field_audit_util.py` | Запись аудита только изменённых полей |
| `api/test_lead_field_audit_api.py` | GET audit, PATCH→строки, порядок, amountRub |
| `test_stage_transition.py` | Валидация правил стадий (unit) |
| `api/test_stage_transition_api.py` | CRM config rules, PATCH+поля, ops save |
| `core/test_crm_settings_stage_rules.py` | normalize_stage_transition_rules |
| `lib/test_stage_transition_lib.py` | Зеркало stageTransition.js |
| `api/test_lead_communications_api.py` | Касания: типы call/meeting/email, audit, 404 |
| `lib/test_crm_redirect_map.py` | Зеркало crmRedirectMap.js (308 /crm→/leads) |
| `lib/test_leads_route_manifest.py` | Зеркало leadsRouteManifest.js |
| `smoke/test_leads_block_smoke.py` | E2E смоук API блока Лиды |
| `smoke/test_leads_block_acceptance.py` | Acceptance PRD_MAP п.1–12 (API) |
| `test_lead_score_advisory.py` | Скор-советы |
| `core/test_lead_priority_tier.py` | Приоритет лида (зеркало crmStages.js) |
| `smoke/test_scoring_funnel_smoke.py` | Смоук балльной воронки (API + формула) |
| `voice/test_whisper_stt.py` | Groq Whisper STT, preprocess, pipeline audio |
| `smoke/test_whisper_stt_smoke.py` | HTTP transcribe + ops whisper settings + WS |
| `smoke/test_voice_mic_ws_e2e.py` | WS audio bytes → STT → Hermes (mic E2E) |
| `smoke/test_leadgen_voice_ws.py` | WS → generate_lead → /leadgen (Ф2 §8 slice) |
| `lib/test_ops_route_manifest.py` | Зеркало навигации Ops + список API smoke |
| `api/test_ops_baseline_api.py` | Ops Ф1: read API + prompt/CRM roundtrip |
| `smoke/test_ops_baseline_smoke.py` | Смоук Ops manifest + sample API |
| `smoke/test_tenders_baseline_smoke.py` | Тендеры Ф1: search/plans/usage mocked |
| `test_tender_sources.py` | Юниты провайдеров и хелперов tenders |
| `test_review_fixes.py` | Регрессии по code review |
| `test_agents.py` | Агенты |
| `test_search.py` | Поиск |
| `api/test_email_sync_api.py` | POST `/api/email/sync`, `/accounts/{id}/sync` |
| `email_sync/test_fetch_imap_mock.py` | IMAP fetch + SINCE с моком (CI) |
| `test_email_sync.py` | Live IMAP только при `EMAIL_SYNC_LIVE=1` |
| `test_bitrix_integration.py` | Битрикс live (REST вебхук) |
| `integrations/test_bitrix_row_map.py` | Маппинг полей Битрикс → Lead |
| `integrations/test_bitrix_sync_state.py` | sync state + poll skip + upsert mock |
| `integrations/test_bitrix_webhook.py` | Исходящий вебхук ONCRMLEADADD |
| `leadgen/test_checko_http_client.py` | Checko HTTP без live API |
| `leadgen/test_crm_threshold.py` | Порог автосохранения в CRM |
| `email_sync/test_sync_helpers.py` | classify/normalize/to_text |
| `lib/test_pr_checklist_policy.py` | Политика «тест на фичу» в доках |

---

## `fixtures/leadgen/`

JSON и txt для моков Checko, BuiltWith, пайплайна — не менять без обновления тестов.
