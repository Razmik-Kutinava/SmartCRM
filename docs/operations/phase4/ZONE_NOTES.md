# ZONE_NOTES — Фаза 4 (межзадачные контракты)

> Читать **только раздел зоны**, которую трогает задача.  
> `Grep` `^## ` → `Read` offset/limit. **Целиком не читать.**  
> Пишет агент на GREEN/REVIEW; устаревшее → `/ctx-trim` или архив фазы.

## leads

- Поиск списка: exact/includes → fallback fuzzy топ-5 (`lead_company_fuzzy` / `leadCompanyFuzzy.js`); бейдж «похоже»; fuzzy **не** в `rememberVoiceLeads` (без silent open).
- Overlay голоса: `LeadVoiceOverlay` blur+iframe `?embed=1`; «открой её» после `list_leads`.
- 🔍: суфлёр gaps → ИНН/Checko → веб; BuiltWith/WhoIs в том же шаге; тендеры — плитка без LLM (`llm_tokens=0`).

## voice

- Hot-path: `voice/pipeline.py` → Hermes → `agents/orchestrator.py` — порядок не ломать.
- Интенты open_lead / list_leads: rescue в Hermes; фокус матчей в UI.

## hermes

- Parse/интенты: `core/hermes/parse.py`. Eval: `tests/core/test_hermes_eval.py` (может нужен LLM).
- Context hygiene runtime ≠ Cursor `/ctx-trim` — см. `docs/stack/LLM.md` (`HERMES_ENABLE_CONTEXT_HYGIENE`).

## agents

- Слоты с карточки: сначала разбор на имеющемся; `missing_data` в конце.
- Стратег видит выжимки других агентов; email digest ужат (токены).
- Runtime `agent_prompt_*.txt` + A/B на 10 лидах — BACKLOG.

## leadgen

- Публичный API: `leadgen/pipeline/__init__.py`; раннер `run_pipeline.py` — hot-path.
- Дебаг: skill `leadgen-debug`.

## rag

- После 🔍/сырья — куски в inbox/RAG; лимиты длины brief/RAG в коде сырья.

## email

- FAQ-автоответ зависит от env — тест должен monkeypatch (ISSUES).
- Ящики в UI — см. phase4/email.

## tenders

- Плитка на лиде: веб+TG+DN+Checko; win rate/Контур — BACKLOG.
