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

## Данные

| Скрипт | За что |
|--------|--------|
| `seed_eval_benchmark_leads.py` | Seed лидов для eval |

## Служебные

| Скрипт | За что |
|--------|--------|
| `smoke_leads_block.py` | Смоук блока «Лиды»: pytest-регрессия + опц. GET фронта |
| `smoke_scoring_funnel.py` | Смоук балльной воронки: формула scoreAdvisory + приоритеты |
| `smoke_whisper_stt.py` | Смоук Groq Whisper STT + опц. live Groq |
| `smoke_hermes_leads.py` | Смоук Hermes интентов по лидам (CRUD, стадия, задача) |
| `smoke_voice_action.py` | Смоук сборки voice_action (approve/filter/navigate) |
| `smoke_hermes_leads_full.py` | Смоук полных интентов лидов (analyze, history, фильтры) |
| `smoke_voice_lead_scenarios.py` | Полный смоук блока «Голос → лиды» (п.1–5 chain) |
| `smoke_search_providers.py` | Смоук Serper/Brave/Tavily (PRD_MAP RAG п.1) |
| `smoke_search_modes.py` | Смоук 6 режимов поиска (PRD_MAP RAG п.2) |
| `smoke_rag_chroma.py` | Смоук Chroma RAG + агенты (PRD_MAP RAG п.3) |
| `smoke_rag_upload.py` | Смоук upload PDF/txt в /rag (PRD_MAP RAG п.4) |
| `smoke_rag_save_from_search.py` | Смоук «сохранить в базу» из /search ingest-batch (PRD_MAP RAG п.5) |
| `smoke_search_enrich_lead.py` | Смоук enrich-lead из /search (PRD_MAP RAG enrich) |
| `smoke_leadgen_inn_analysis.py` | Смоук анализа по ИНН/названию (PRD_MAP leadgen direct) |
| `smoke_leadgen_portrait.py` | Смоук поиска по портрету (PRD_MAP leadgen portrait) |
| `smoke_leadgen_cluster.py` | Смоук кластер / холдинг (PRD_MAP leadgen cluster) |
| `run_zone_regression.py` | Регрессия по зонам (crm_leads, leadgen, …) |
| `_resplit_leadgen_pkgs.py` | One-off: пересборка pipeline/checko пакетов |

Вывод скриптов → `data/artifacts/`, не в корень репо.
