# Scripts — CLI (не pytest)

Запускать из `backend/`: `python scripts/имя.py`.

## Hermes / eval

| Скрипт | За что |
|--------|--------|
| `run_hermes_parse_rollout.py` | Rollout парсера Hermes |
| `run_hermes_feature_rollout.py` | Rollout фич Hermes |
| `run_hermes_ab_check.py` | A/B проверка промптов |
| `hermes_kpi_gate.py` | KPI-гейт качества интентов |
| `hermeslab.py` | Лаборатория Hermes |
| `run_eval_modules_live.py` | Live LLM eval модулей (cases_modules.jsonl, Groq+Ollama) |
| `run_eval_hermes3_db.py` | Eval Hermes с БД |
| `run_eval_hermes3_inline.py` | Eval Hermes inline |
| `eval_compare_modes.py` | Сравнение режимов eval |
| `expand_eval_from_traces.py` | Расширение eval из трейсов |
| `ollama_latency_hard.py` | Замер латентности Ollama |

## Тендеры

| Скрипт | За что |
|--------|--------|
| `tender_sources_ab.py` | A/B источников тендеров |
| `tender_sources_benchmark.py` | Бенчмарк источников |
| `tender_sources_tests.py` | Тесты источников (CLI) |
| `moy_zakupki_smoke.py` | Смоук «Мои закупки» |
| `smoke_tender_pdf_extract.py` | Live POST `/api/tenders/documents/extract` (ключ из корневого `.env`) |

## Данные

| Скрипт | За что |
|--------|--------|
| `seed_eval_benchmark_leads.py` | Seed лидов для eval |
| `seed_agent_eval_cases.py` | Генерация `eval/agents/*.jsonl` (15 кейсов × 5 агентов) |
| `run_agents_quality_gate.py` | Live gate 6 агентов (Ollama); `GATE_CPU_PROFILE=1` → qwen2.5:3b + fast Hermes rescue; `--agents-only` / `--hermes-only`; `--log-file` |
| `run_gate_enrich_smoke.py` | Gate без Ollama: rescue Hermes + mock LLM + enrich; `--write-acceptance` |
| `check_hermes_rescue_coverage.py` | Покрытие eval/cases.jsonl правилами rescue (36/36) |

## Служебные

| Скрипт | За что |
|--------|--------|
| `ci_smoke.py` | CI smoke: ops + leads + voice (pytest, без live Groq) |
| `smoke_leads_block.py` | Смоук блока «Лиды»: pytest-регрессия + опц. GET фронта |
| `smoke_analytics_baseline.py` | Смоук Ф1 «Аналитика»: pytest метрик/API + опц. GET `/leads/analytics` |
| `smoke_ops_baseline.py` | Смоук Ф1 «Ops»: pytest API ops + whisper + scenarios + опц. GET `/ops` |
| `smoke_email_connect.py` | Live connect из `.env` (`core.email_config`); или `POST /api/email/bootstrap-from-env` |
| `smoke_email_sync.py` | Live POST `/api/email/sync` — обновить письма без пароля |
| `smoke_email_smtp_send.py` | Live POST `/api/email/send` — SMTP self-test (ib@) |
| `smoke_email_faq.py` | FAQ smoke: триггер «прайс» → `try_faq_autoreply` (SMTP mock) |
| `smoke_email_faq_live.py` | Live: me@ SMTP + ib@→me@ «прайс» + sync + faq_auto outbound |
| `smoke_email_nurture_live.py` | Live: тестовый лид-клиент → nurture start → process-due → 1-е письмо с `{{company}}` |
| `smoke_email_nurture_segment_live.py` | Live: узкий сегмент `Nurture Live` → `start-segment` batch (без mass send) |
| `smoke_email_nurture_llm_live.py` | Live: маркетолог LLM → 3 письма MaxPatrol VM → nurture start-llm |
| `smoke_campaign_mass_ui.py` | Live UI: `/email` → Массовая (сегмент) — Playwright, чекбоксы → счётчик → 3 LLM → test ib@ |
| `probe_email_host.py` | Диагностика IMAP/SMTP портов для кастомного хоста (me@) |
| `smoke_scoring_funnel.py` | Смоук балльной воронки: формула scoreAdvisory + приоритеты |
| `smoke_scoring_export.py` | Смоук экспорта баллов: pytest + live xlsx + frontend URL |
| `smoke_scoring_f4_ui.py` | Смоук Ф4 баллы: сортировка списка, флаги API, UI /leads/list + /ops/crm |
| `smoke_whisper_stt.py` | Смоук Groq Whisper STT + опц. live Groq |
| `smoke_hermes_leads.py` | Смоук Hermes интентов по лидам (CRUD, стадия, задача) |
| `smoke_voice_action.py` | Смоук сборки voice_action (approve/filter/navigate) |
| `smoke_hermes_leads_full.py` | Смоук полных интентов лидов (analyze, history, фильтры) |
| `smoke_voice_lead_scenarios.py` | Полный смоук блока «Голос → лиды» (п.1–5 chain) |
| `smoke_voice_mic_e2e.py` | E2E mic-путь: WS audio bytes + leadgen voice smoke |
| `smoke_tenders_baseline.py` | Ф1 тендеры: pytest sources + baseline smoke + опц. /tenders |
| `smoke_search_providers.py` | Смоук Serper/Brave/Tavily (PRD_MAP RAG п.1) |
| `smoke_search_modes.py` | Смоук 6 режимов поиска (PRD_MAP RAG п.2) |
| `smoke_rag_chroma.py` | Смоук Chroma RAG + агенты (PRD_MAP RAG п.3) |
| `smoke_rag_upload.py` | Смоук upload PDF/txt в /rag (PRD_MAP RAG п.4) |
| `smoke_rag_save_from_search.py` | Смоук «сохранить в базу» из /search ingest-batch (PRD_MAP RAG п.5) |
| `smoke_search_enrich_lead.py` | Смоук enrich-lead из /search (PRD_MAP RAG enrich) |
| `smoke_leadgen_inn_analysis.py` | Смоук анализа по ИНН/названию (PRD_MAP leadgen direct) |
| `smoke_leadgen_portrait.py` | Смоук поиска по портрету (PRD_MAP leadgen portrait) |
| `smoke_leadgen_cluster.py` | Смоук кластер / холдинг (PRD_MAP leadgen cluster) |
| `smoke_leadgen_autosave.py` | Смоук автосейв в CRM при скор ≥ порога (PRD_MAP leadgen autosave) |
| `run_zone_regression.py` | Регрессия по зонам (crm_leads, leadgen, …) |
| `backfill_lead_profile.py` | Backfill `okved_*`, `employees_band`, `portrait_score` у существующих лидов из `checko_json` |
| `resync_bitrix_lead_profiles.py` | Re-import Битрикс (ИНН/ОКВЭД UF) + backfill портрета без Checko |
| `resync_bitrix_lead_products.py` | Backfill `lead_products` из Битрикс API (UF, productrows, сделки, КП); `.env` → `BITRIX24_WEBHOOK_URL`; `--workers 6 --delay-ms 10` |
| `_resplit_leadgen_pkgs.py` | One-off: пересборка pipeline/checko пакетов |

Вывод скриптов → `data/artifacts/`, не в корень репо.
