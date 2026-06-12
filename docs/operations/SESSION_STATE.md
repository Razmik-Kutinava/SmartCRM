# SESSION_STATE

Краткий прогресс сессии — **обязательно** после каждого действия (1–2 строки). Шаг с изменениями файлов → `git commit` **до** отчёта. Канон: `smartcrm-commit-ops.mdc`.

**По завершении задачи:** сначала `git commit`, затем в строке `Коммит: \`hash\`` — хеш из этого коммита (не прочерк, не «потом»).

Шаблон строки:

`[дата] | Действие:[…] | Коммит:`хеш` | Хвост A:[план не сделано — нет/список] | Хвост B:[BACKLOG в прогоне — нет/список] | Хвост C:[доп. починки — нет/список] | Следующий шаг:[…] | Статус:done`

**Хвост A/B/C обязателен** в каждой новой записи (`check_agent_step.py`).

**Правило:** в строке только реальный `Коммит: \`hash\`` — иначе FAIL (`check_agent_step` + **pre-commit hook**).


2026-06-12 | Действие: push+CI green run #3 + branch protection main (pytest+smoke required). | Коммит: `7346885` | Хвост A: MAP п.3–5 milestones | Хвост B: me@agneko.am | Хвост C: нет | Следующий шаг: go Ф2. | Статус: done

2026-06-12 | Действие: CI green path — fix rescue create_task до list_leads (eval-007); HERMES_ENABLE_FASTPATH=0 в ci.yml. | Коммит: `6fca8ca` | Хвост A: push+branch protection | Хвост B: MAP п.3–5 | Хвост C: нет | Следующий шаг: push. | Статус: done

2026-06-11 | Действие: pytest clean — email assert, filterwarnings starlette, live_eval в доках; 500 passed 0 warnings, ci_smoke OK. | Коммит: `f3974c2` | Хвост A: push+branch protection GitHub | Хвост B: MAP п.3–5 milestones | Хвост C: me@agneko.am | Следующий шаг: push. | Статус: done

2026-06-11 | Действие: fix venv — cryptography в requirements.txt; доки python -m pytest+venv; CI python -m pytest; тест deps. | Коммит: `58d7a2d` | Хвост A: (.venv) pip install -r requirements.txt заново | Хвост B: push+branch protection | Хвост C: me@agneko.am | Следующий шаг: в venv `python -m pytest -q`. | Статус: done

2026-06-11 | Действие: CI — GitHub Actions ci.yml (pytest+smoke jobs), ci_smoke.py ops/leads/voice, CI_BASELINE.md; локально 498+132 pytest OK. | Коммит: `0477431` | Хвост A: branch protection в GitHub вручную | Хвост B: cov fail-under в CI — отдельно | Хвост C: me@agneko.am пароль | Следующий шаг: push + включить required checks. | Статус: done

2026-06-11 | Действие: Coverage — pytest-cov, requirements-dev.txt, .coveragerc, baseline 51.4%, live_eval marker, fix voice str(e)+RAG stubs+brave backoff; 498 pytest. | Коммит: `878e159` | Хвост A: CI cov gate — отдельный шаг | Хвост B: me@agneko.am пароль | Хвост C: нет | Следующий шаг: go Ф2 или CI cov. | Статус: done

2026-06-11 | Действие: Email fix — парсинг дат IMAP, repair 362 UID, inbox filter (support/pricing), DevTools=Yandex сегодня. | Коммит: `dae7f08` | Хвост A: me@agneko.am — пароль | Хвост B: EMAIL_IMAP_FETCH_LIMIT=500 в .env | Хвост C: нет | Следующий шаг: go Ф2 рассылки или Агенты. | Статус: done

2026-06-11 | Действие: Email Sync — POST /sync, IMAP SINCE, кнопка 🔄 на /email, smoke_email_sync, 7 pytest, live+DevTools ib@ OK. | Коммит: `b20b2d9` | Хвост A: me@agneko.am — пароль | Хвост B: автофон sync → Ф2 | Хвост C: нет | Следующий шаг: go Агенты MAP или Ф2 рассылки. | Статус: done

2026-06-11 | Действие: Email connect — `emailStorage.js` apiFetch, `EMAIL_IMAP_FETCH_LIMIT`, smoke+mock pytest, ib@agneko.com live (504 треда), DevTools /email OK; acceptance+MAP. | Коммит: `6d84234` | Хвост A: me@agneko.am — пароль mail.agneko.am | Хвост B: рассылки/UX почты → Ф2 | Хвост C: нет | Следующий шаг: go Агенты MAP или пароль me@. | Статус: done

2026-06-11 | Действие: Ops Ф1 — аудит 12 вкладок (реальные API), `smoke_ops_baseline.py` 33 pytest, DevTools /ops+/agents, acceptance+MAP. | Коммит: `d561372` | Хвост A: нет | Хвост B: версионирование промптов → Ф2 | Хвост C: нет | Следующий шаг: go Агенты MAP или Ф2. | Статус: done

2026-06-11 | Действие: PDF extract — `smoke_tender_pdf_extract.py`, curl/PowerShell в acceptance (корневой .env, пути cwd), в tenders baseline. | Коммит: `0350f79` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go Ops или Ф2. | Статус: done

2026-06-11 | Действие: аналитика Ф1 — KPI /leads/analytics, API summary/export, убран mock /analytics, 10 pytest, DevTools+Puppeteer (3184 лида, CSV 200). | Коммит: `5eeeff8` | Хвост A: нет | Хвост B: голос по метрикам → Ф2 | Хвост C: средний чек/цикл «—» пока нет выигранных | Следующий шаг: go Ops перепроход или Ф2. | Статус: done

2026-06-11 | Действие: apiFetch в tenderApi + DevTools UI PDF OK (23 симв, extract 200). | Коммит: `21c88fd` | Хвост A: frontend/.env локально (gitignore) | Хвост B: нет | Хвост C: нет | Следующий шаг: go Ф2. | Статус: done

2026-06-11 | Действие: PDF→текст — `/documents/extract`, UI upload→analyze, pytest+fixture, DevTools /tenders (uvicorn :8000 завис — перезапуск). | Коммит: `1f3eaeb` | Хвост A: нет | Хвост B: live UI upload после рестарта API | Хвост C: нет | Следующий шаг: go Ф2. | Статус: done

2026-06-11 | Действие: тендеры хвосты закрыты — Serper/Tavily, tender_saved, analyze LLM, Gosplan UI, 29 pytest. | Коммит: `21e9e1d` | Хвост A: PDF→analyze опц. | Хвост B: live spot-check ключей 🟢 | Хвост C: нет | Следующий шаг: go Ф2 §8 или §1 Voice. | Статус: done

2026-06-11 | Действие: тендеры Ф1 baseline — MAP таблица, smoke+pytest, acceptance, fix search 400, BACKLOG хвосты. | Коммит: `2acf0da` | Хвост A: нет | Хвост B: Мои/Архив UI, Gosplan tail 🟡 | Хвост C: Ф2 §7 агент MOCK | Следующий шаг: go Ф2 или тендеры п.4. | Статус: done

2026-06-11 | Действие: doc-sync — PRD навигация+Ф1✅; MAP TOC/DoD Ф2/сценарии Ф2/coverage/сводка; LEADGEN_VOICE_ACCEPTANCE.md; waitForWsOpen. | Коммит: `30f7460` | Хвост A: нет | Хвост B: spot-check approve/fanout 🟡 | Хвост C: Ф2 §8 live UI | Следующий шаг: Ф2 §8 live или §1 Voice Layer — ждём go. | Статус: done

2026-06-11 | Действие: mic E2E — WS audio tests, dev voice-simulate-mic, leadgen voice smoke; Ф1 DoD 6/6; MAP/BACKLOG/HANDOFF. | Коммит: `8d2d196` | Хвост A: нет | Хвост B: spot-check approve/fanout 🟡 | Хвост C: Ф2 §8 live UI pipeline | Следующий шаг: Ф2 §8 live или §1 Voice Layer. | Статус: done

2026-06-10 | Действие: MAP-doc финал — Поиск/RAG таблица, шапки Лиды/Баллы/Поиск; HANDOFF «MAP выровнен». | Коммит: `2890523` | Хвост A: нет (MAP-doc закрыт) | Хвост B: микрофон 🔴, DoD п.6 | Хвост C: go Ф2 оч.1/5 | Следующий шаг: продукт по `go`. | Статус: done

2026-06-10 | Действие: MAP п.7–10 — quality gates агентов, безопасность, инфра прод, coverage; langgraph.md; сводка MAP. | Коммит: `6a6c516` | Хвост A: MAP-doc дубль Поиск/RAG, шапки | Хвост B: микрофон 🔴, DoD п.6 | Хвост C: go Ф2 оч.1/5 | Следующий шаг: MAP-doc хвост или `go`. | Статус: done

2026-06-10 | Действие: MAP п.6 — порядок Ф2 очередь 1–9, фундамент/позже, §1≠лиды Ф1, go по номеру; HANDOFF+BACKLOG. | Коммит: `d76b604` | Хвост A: MAP-doc дубль Поиск/RAG, шапки | Хвост B: микрофон 🔴, DoD п.6 | Хвост C: go кандидаты оч.1 или оч.5 | Следующий шаг: MAP-doc или `go` Ф2. | Статус: done

2026-06-10 | Действие: MAP п.5 — 7 бизнес-сценариев Ф1, привязка к блокам, процесс «сценарий→таблица»; README. | Коммит: `55a888d` | Хвост A: MAP-doc дубль Поиск/RAG, шапки | Хвост B: микрофон 🔴, DoD п.6 | Хвост C: spot-check 🟡 | Следующий шаг: MAP-doc п.6 порядок Ф2 / `go`. | Статус: done

2026-06-10 | Действие: MAP п.4 DoD Ф1 — 6 критериев, dev-gates ссылка, п.5 голос код/E2E, п.6 «ок в Ф2»; BACKLOG sync. | Коммит: `418827f` | Хвост A: MAP-doc дубль Поиск/RAG, шапки | Хвост B: микрофон E2E 🔴, п.6 ждём | Хвост C: spot-check 🟡 | Следующий шаг: MAP-doc п.5 или `go` Ф2. | Статус: done

2026-06-10 | Действие: MAP п.3 — легенда [x] vs ⚠️, колонка Статус в «Голос», сводка «частично», BACKLOG как снять ⚠️; README. | Коммит: `0e7e0ff` | Хвост A: MAP-doc дубль Поиск/RAG, шапки таблиц | Хвост B: микрофон E2E 🔴 | Хвост C: п.3/5 spot-check 🟡 | Следующий шаг: MAP-doc или микрофон руками. | Статус: done

2026-06-10 | Действие: хвост Ф1 — указатель в MAP, канон BACKLOG; убраны ложные 🔴 Hermes/voice_action; HANDOFF без дубля таблицы; BACKLOG п.98+инфра. | Коммит: `c27517b` | Хвост A: MAP-doc: дубль Поиск/RAG, шапки таблиц | Хвост B: микрофон E2E 🔴 | Хвост C: нет | Следующий шаг: MAP-doc п.3 или `go` продукт. | Статус: done

2026-06-10 | Действие: PRD_MAP выровнен — легенда, DoD Ф1, сценарии, убраны дубли, голос ⚠️, хвост→BACKLOG, порядок Ф2, безопасность/инфра прод; HANDOFF+CHANGELOG. | Коммит: `59b0af7` | Хвост A: нет | Хвост B: микрофон E2E 🔴 | Хвост C: нет | Следующий шаг: `go` продукт (Ф2 §8 / §1 / микрофон руками). | Статус: done

2026-06-10 | Действие: leadgen автосейв портрет+кластер — `persist_autosave.py`, `save_to_crm` в API, UI `leadgen-autosave-crm`, `crm_saved[]`, 24 pytest autosave block. | Коммит: `5ef5b3f` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: голосовые Ф2. | Статус: done

2026-06-10 | Действие: leadgen dedup ИНН (вариант A) — `persist_card.py`, update по ИНН, `crm_lead_created`, UI «Обновлён», 14 pytest. | Коммит: `3dfa15d` | Хвост A: нет | Хвост B: autosave портрет/кластер — Ф2 | Хвост C: нет | Следующий шаг: голосовые Ф2. | Статус: done

2026-06-10 | Действие: leadgen автосейв CRM — `crm_threshold.py`, 10 pytest, smoke, DevTools E2E скор 84 → лид #3187; усилен commit-ops (override User Rules); удалены `CURSOR_USER_RULES_*.md`. | Коммит: `a8f4c6a` | Хвост A: нет | Хвост B: dedup по ИНН в CRM — BACKLOG | Хвост C: persist `_fmt_money` import | Следующий шаг: голосовые Ф2. | Статус: done

2026-06-10 | Действие: убран конфликт commit в HANDOFF; EN-паттерны в `check_rules_commit_conflict.py`; `CURSOR_USER_RULES_SNIPPET.md`. | Коммит: `8bc2554` | Хвост A: snippet в Cursor Settings — вручную у пользователя | Хвост B: нет | Хвост C: нет | Следующий шаг: `go` шаг 2 warnings. | Статус: done

2026-06-10 | Действие: leadgen кластер/холдинг — API+integration tests, smoke live 4 субъекта Хохланд, testid UI, DevTools MCP POST cluster 200; portrait Groq review → BACKLOG Ф2; `LEADGEN_CLUSTER_ACCEPTANCE.md`. | Коммит: `c291a32` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: автосохранение CRM или Ф2. | Статус: done

2026-06-10 | Действие: portrait progress UI (`portraitProgress.js`, testids) + DevTools E2E **user-chrome-devtools** MCP (progress «Загружаем эталон…», POST portrait 200, 3 кандидата). | Коммит: `3ebb811` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: следующий MAP. | Статус: done

2026-06-10 | Действие: хвост ИНН 1–6 — `leadgen/inn_constants.py`, импорты smoke/API, docs Хохланд, asyncio.run, DevTools portrait E2E (cursor-ide-browser POST 200, 3 кандидата), `test_inn_constants.py` 10 pytest. | Коммит: `1bb0645` | Хвост A: нет | Хвост B: нет | Хвост C: user-chrome-devtools MCP errored — cursor-ide-browser | Следующий шаг: следующий пункт MAP. | Статус: done

2026-06-10 | Действие: шаг 1 «странный эталон» — развод ИНН: мок `7707070010` ТехноСофт, live `5040048921` Хохланд; `inn_constants.py`, `LEADGEN_INN_FIX.md`; smoke portrait 9 pytest + live 3 кандидата (gaps=[]); hook utf-8 fix `session_state_validate.py`. | Коммит: `4de231d` | Хвост A: pytest warnings (asyncio/email) | Хвост B: нет | Хвост C: DevTools portrait (MCP недоступен) | Следующий шаг: шаг 2 warnings. | Статус: done

2026-06-09 | Действие: pre-commit hook (`29f5164`) + ops/UTF-8 fix (`26374f8`); hook установлен, validate OK. | Коммит: `b83940d` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: портрет leadgen в git. | Статус: done

2026-06-09 | Действие: commit-ops — явно: commit без согласования пользователя; зачистка SESSION_STATE портрет. | Коммит: `525fa19` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: `go` портрет в git. | Статус: done

2026-06-09 | Действие: PRD_MAP leadgen «Поиск по портрету» — API only reference_inn, fix re/_parse_json_safe, select лида CRM, smoke 9 pytest + live 3 кандидата, DevTools fetch 200; `LEADGEN_PORTRAIT_ACCEPTANCE.md`. | Хвост A: кластер MAP | Хвост B: нет | Хвост C: 3 бага portrait pipeline | Следующий шаг: портрет leadgen в git + `go` кластер. | Статус: in_progress

2026-06-09 | Действие: iron commit — усилены `commit-ops`, `check_agent_step`, `check_rules_commit_conflict`; зачистка SESSION_STATE; ответ только после commit. | Коммит: `7eba527` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: `go` портрет. | Статус: done

2026-06-08 | Действие: правило хвоста прогона A/B/C — `commit-ops`, `task-workflow`, `AGENTS.md`, `RULES_MATRIX`, `check_agent_step.py`; три сценария: план не сделано / BACKLOG в прогоне / доп. починки. | Коммит: `5c0b636` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: PRD_MAP. | Статус: done

2026-06-09 | Действие: PRD_MAP Ф2 — §4 кэш enrich, §9 кнопка на карточке лида; BACKLOG + SEARCH_ENRICH_LEAD_ACCEPTANCE синхрон. | Следующий шаг: по `go` следующий пункт. | Статус: done

2026-06-09 | Действие: enrich хвост — Brave cache/semaphore, Checko/ИНН, LinkedIn/ЛПР запросы, scrape сайта, CRM select+PATCH; 28 pytest; PRD_MAP §2 enrich ✅. | Следующий шаг: Ф2 авто-чанки. | Статус: done

2026-06-09 | Действие: enrich-lead smoke — Brave fix, API validation, 20 pytest, live Сбербанк phone/email/website; DevTools таб enrich OK; `SEARCH_ENRICH_LEAD_ACCEPTANCE.md`; PRD_MAP enrich ✅; блок RAG закрыт. | Следующий шаг: Ф2 авто-чанки или другой блок MAP. | Статус: done

2026-06-08 | Действие: RAG п.5 save из поиска — `source_url` в metadata, `test_rag_ingest_batch*.py` 6 pytest, `smoke_rag_save_from_search.py`; DevTools `/search` таб RAG → 1 чанк cbr.ru; `SEARCH_RAG_SAVE_ACCEPTANCE.md`; блок п.1–5 ✅. | Следующий шаг: enrich-lead smoke или Ф2. | Статус: done

2026-06-08 | Действие: RAG п.4 upload PDF/txt — `test_rag_upload.py`, `test_rag_upload_api.py`, `smoke_rag_upload.py` 8 pytest; DevTools `/rag` текст «В базу» 1 чанк + PDF в источниках; `SEARCH_RAG_UPLOAD_ACCEPTANCE.md`; PRD_MAP п.4 ✅. | Следующий шаг: `go` п.5 save из поиска. | Статус: done

2026-06-08 | Действие: RAG п.3 Chroma — `test_rag_api.py`, `smoke_rag_chroma.py` 11 pytest, live 1592 чанка (economist 960 / all 624 / marketer 8); `/rag` apiFetch; `SEARCH_CHROMA_ACCEPTANCE.md`; PRD_MAP п.3 ✅. DevTools: серверы не запущены — pytest + прямой count Chroma OK. | Коммит: `97778b2` | Следующий шаг: `go` п.4. | Статус: done

2026-06-08 | Действие: зачистка правил — только безусловный `git commit` при закрытии шага; убраны отложенные формулировки в `.mdc`, `AGENTS.md`, ops; усилен `check_rules_commit_conflict.py`. | Коммит: `02ef689` | Следующий шаг: PRD_MAP RAG п.3. | Статус: done

2026-06-08 | Действие: коммит+push RAG п.1 хвост + п.2 — `97778b2` (код/тесты/acceptance; ops CHANGELOG/HANDOFF уже были в HEAD). | Следующий шаг: `go` RAG п.3 Chroma. | Статус: done

2026-06-08 | Действие: RAG п.2 — 6 режимов перепроход: `test_search_modes_api.py` + `test_search_modes.py`, `smoke_search_modes.py` 19 pytest + live free; DevTools 6 табов + free live 10 результатов; `SEARCH_MODES_ACCEPTANCE.md` (сделано/НЕ сдали); PRD_MAP п.2 ✅; BACKLOG п.3–5. | Коммит: `97778b2` | Статус: done

2026-06-08 | Действие: RAG п.1 хвост — `/search` все API через `apiFetch`/`apiPost`; `smoke_search_providers.py` грузит `.env`; DevTools UI «Сбербанк»→«Найти»→7 результатов; `SEARCH_PROVIDERS_ACCEPTANCE.md` таблица; `BACKLOG.md`. | Коммит: `97778b2` | Статус: done

2026-06-08 | Действие: PRD_MAP RAG п.1 — перепроход Serper/Brave/Tavily: фикс cache в `company_search.py`, `test_search_providers.py` + API smoke, `smoke_search_providers.py` 11 pytest; DevTools `/search` — 3 ключа ✓, `/run` Сбербанк → 7 результатов; `SEARCH_PROVIDERS_ACCEPTANCE.md`. | Коммит: `eb138bd` | Следующий шаг: `go` RAG п.2 «6 режимов поиска». | Статус: done

2026-06-08 | Действие: BACKLOG § «Ручная работа (только ты)» — таблица Фаза/блок/пункт: 🔴 микрофон E2E (Ф1 п.1), 🟡 approve+fanout spot-check, 🟢 live Groq опционально, Ф2 Битрикс туннель; синхрон «Активный хвост». | Следующий шаг: пользователь — строка 🔴 в BACKLOG; после OK — строка в SESSION_STATE. | Коммит: `b4ca224` | Статус: done

2026-06-08 | Действие: хвост BACKLOG «Голос → лиды» #2–#11 (кроме #1 микрофон) — add_communication, fuzzy stage, чипы, fanout UI, health/whisper, email field_validator, eval-034–036, approve testids, smoke_hermes_leads_live; `VOICE_LEADS_TAIL_ACCEPTANCE.md`; pytest smoke зелёный. | Коммит: `352eed2` | Статус: done

2026-06-08 | Действие: п.5 смоук голоса — S01–S09 pytest 23 + chain 47; DevTools localhost:5174 API+WS OK; `VOICE_LEAD_SCENARIOS_ACCEPTANCE.md`; BACKLOG сводный хвост блока. | Следующий шаг: блок «Голос → лиды» закрыт → Фаза 2 или Битрикс. | Статус: done

2026-06-08 | Действие: п.4 полные интенты — analyze_lead, lead_history, фильтры stage/industry/city; smoke_hermes_leads_full 34 passed; BACKLOG хвост п.4. | Следующий шаг: `go` п.5 смоук голосовых. | Статус: done

2026-06-08 | Действие: voice_action п.3 — `voice_action.py`, WS событие, фронт VoiceActionHost + stores; 8 pytest + smoke; `VOICE_ACTION_ACCEPTANCE.md`, PRD_MAP [x]. | Следующий шаг: `go` п.4 полные интенты или п.5 смоук. | Статус: done

2026-06-08 | Действие: BACKLOG — отложены pgvector, LiveKit, Litestar (триггеры + фазы MAP). | Следующий шаг: `go` хвост Ф1 голос/Hermes. | Статус: done

2026-06-08 | Действие: PRD_NOTES §CHANGELOG → шапка `operations/CHANGELOG.md`; NOTES — ссылка на канон. | Следующий шаг: хвост Ф1 Hermes/voice или `go` Фаза 2. | Статус: done

2026-06-08 | Действие: BACKLOG — таблица «Осталось Голос→лиды» (п.3 voice_action, п.4 интенты, п.5 смоук); PRD_MAP порядок voice_action выше полных интентов. | Следующий шаг: `go` п.3 voice_action. | Статус: done

2026-06-08 | Действие: Hermes п.2 — slot_normalize, rescue, smoke_hermes_leads 40 passed; BACKLOG hermes eval закрыт; `HERMES_LEADS_ACCEPTANCE.md`. | Следующий шаг: voice_action или полные интенты. | Статус: done

2026-06-08 | Действие: BACKLOG — Pydantic `@validator` в `email.py` → `@field_validator` (🟢, шум в pytest). | Следующий шаг: п.2 Hermes / voice_action. | Статус: done

2026-06-08 | Действие: Whisper STT п.1 — `smoke_whisper_stt.py` 14+1 live Groq; фикс 503/WS error; `WHISPER_STT_ACCEPTANCE.md`; DevTools WS OK. | Следующий шаг: п.2 Hermes интенты или п.3 voice_action. | Статус: done

2026-06-08 | Действие: балльная воронка — `lead_priority_tier.py`, `smoke_scoring_funnel.py`, 21 pytest; PRD_MAP смоук ✅; `SCORING_FUNNEL_ACCEPTANCE.md`. | Следующий шаг: `go` голос → лиды или распределение PRD_NOTES. | Статус: done

2026-06-08 | Действие: PRD_NOTES → канон: стек в ARCHITECTURE, карта docs в README, gaps в BACKLOG, RAG коллекции; NOTES обрезан (~500 строк дублей). | Следующий шаг: ждём апрув блока Лиды / `go` п.3. | Статус: done

2026-06-08 | Действие: BACKLOG — туннель :8000/:5173 + исходящий вебхук Битрикса (отложено, Ф2/DevOps); ISSUES/PRD_MAP/HANDOFF обновлены. | Следующий шаг: `go` на п.3 Kanban DnD. | Статус: done

2026-06-08 | Действие: коммит п.2 — `f2727a3` feat: автосинк Битрикс (webhooks_bitrix, bitrix24_sync, amount_rub, опрос 5 мин); pytest integrations 4 passed. | Следующий шаг: `go` п.3 Kanban DnD. | Статус: done

2026-06-08 | Действие: п.3 Kanban DnD — `funnelDnD.js`, drag-drop на `/leads/funnel`, rollback при блоке стадии; pytest 16 passed (funnel_dnd + leads_api). | Следующий шаг: `go` п.4 список/фильтры. | Статус: done

2026-06-08 | Действие: п.4 список — `leadListFilter.js`: фильтр приоритета, сортировка балл/приоритет/компания; UI select + клик по заголовку; pytest 3 passed. | Следующий шаг: `go` п.5 карточка. | Статус: done

2026-06-08 | Действие: п.5 карточка — `leadCardActivity.js` (apiFetch), `leadCardMoney.js`, поле должность; `test_lead_engagement` + card tests 10 passed. | Следующий шаг: `go` п.6 задачи. | Статус: done

2026-06-08 | Действие: п.6 задачи/SLA — `task_dates.py`, `lead_id` фильтр, карточка лида задачи+создание; `taskApi`/`taskSla`; pytest 6 passed. | Следующий шаг: `go` п.7 комментарии. | Статус: done

2026-06-08 | Действие: п.7 комментарии — фикс shadow `postLeadComment`→`submitComment`; `leadComments.js`; API reject пустого body; pytest 7 passed. | Следующий шаг: `go` п.8 аудит полей. | Статус: done

2026-06-08 | Действие: п.8 аудит полей — `leadAudit.js`, RU-лейблы в карточке; тесты util+API 7 passed. | Следующий шаг: `go` п.9 правила стадий. | Статус: done

2026-06-08 | Действие: п.9 правила стадий — `stageTransition.js`, apiUpdateLead→apiPatch, подсказки на кнопках стадий; pytest 11 passed. | Следующий шаг: `go` п.10 лог касаний. | Статус: done

2026-06-08 | Действие: п.10 лог касаний — `leadCommunications.js`, RU-лейблы типов, валидация content; pytest 9 passed. | Следующий шаг: `go` п.11 /crm редиректы. | Статус: done

2026-06-08 | Действие: п.11 /crm редиректы — `crmRedirectMap.js`, +/crm/campaign/{id}; pytest 3 passed. | Следующий шаг: `go` п.12 смоук /leads/*. | Статус: done

2026-06-08 | Действие: п.12 смоук /leads/* — `smoke_leads_block.py`, `leadsRouteManifest.js`, E2E smoke; 71 pytest passed; блок Лиды закрыт. | Следующий шаг: Фаза 1 — следующий модуль PRD_MAP. | Статус: done

2026-06-08 | Действие: acceptance блока Лиды — 81 pytest + 14 HTTP + DevTools все экраны; фикс `/leads/tasks` createTask shadow; `test_leads_block_acceptance.py`, `LEADS_BLOCK_ACCEPTANCE.md`. | Следующий шаг: апрув пользователя → следующий модуль Фазы 1. | Статус: done

2026-06-08 | Действие: Единое правило `smartcrm-commit-ops.mdc` — всегда commit+ops, push по апруву; убраны дубли/конфликты в `.mdc`, `.cursorrules`, RULES_MATRIX, SESSION_STATE; `check_rules_commit_conflict.py`. | Следующий шаг: Фаза 1 PRD_MAP п.3 + `go`. | Статус: done

2026-06-08 | Действие: User Rules — проверка: в локальных файлах Cursor нет (облако); добавлены `AGENTS.md`, `verify_cursor_rules_precedence.py`, `CURSOR_USER_RULES_STATUS.md` — Project Rules перебивают User Rules. | Следующий шаг: PRD_MAP п.3 + `go`. | Статус: done

2026-06-08 | Действие: PRD_MAP Фаза 1 п.1 «CRUD лидов» — перепроход: pytest `test_leads_api` 12 passed (+ amountRub camelCase); live Postgres CRUD OK; код API `leads/crud.py` + UI list/card — review; UI смоук DevTools заблокирован (frontend rolldown). ISSUES: UI update неполный, rolldown. | Следующий шаг: апрув п.1 → п.2 «Поля уровня Битрикс» или фикс UI edit по go. | Вопросы: фиксить контакты в карточке в этом шаге? | Статус: ждём апрув

2026-06-08 | Действие: Вариант B п.1 CRUD — UI edit форма на `/leads/{id}` (`leadCardEdit.js`); frontend Vite 6 + rollup wasm + `ensure-native-deps.cjs`; убран `editingLead`; тесты 15 passed + `crm_leads` 22 passed; DevTools CRUD+карточка OK. | Следующий шаг: `go` на п.2 PRD_MAP. | QA: crm_leads PASS, DevTools contact/industry PATCH OK | Статус: done

2026-06-08 | Действие: PRD_MAP §Лиды — таблица перепрохода: п.1 CRUD ✅ OK (2026-06-08); указатель на п.2 «Поля Битрикс». | Следующий шаг: `go` на п.2. | Статус: done

2026-06-08 | Действие: п.2 «Поля Битрикс» — маппинг + `amount_rub`; автосинк: `POST /api/webhooks/bitrix/events` + фон `BITRIX_AUTO_SYNC_MINUTES=5`; `GET /api/leads/bitrix-sync-status`; pytest bitrix 7 passed (3 live). Файлы: `bitrix24_sync.py`, `webhooks_bitrix.py`, `bitrix.md`. | Следующий шаг: перезапуск uvicorn; вебхук ONCRMLEADADD; `go` на п.3 Kanban DnD. | Статус: done (код), ждёт настройку портала

2026-05-04 | Действие: ROOT CAUSE найден и устранён — база `smartcrm` и юзер `smartcrm` отсутствовали в Postgres; созданы через psql; uvicorn перезапущен → `init_db` применил схему; проверено: `/api/leads` → 200 OK, `/api/leads/1791` → 404 (база пустая). Ошибок 500 нет. | Следующий шаг: импорт/сид данных (Bitrix или `seed_eval_benchmark_leads.py`) при необходимости. | Вопросы: нет | Статус: done

2026-05-04 | Действие: Доп. фикс RST при connect — в `db/session.py`: нормализация `@localhost`→`127.0.0.1` (env `DATABASE_FORCE_IPV4`), дефолт URL на `127.0.0.1`, `connect_args` timeout + опционально `DATABASE_SSL=disable`; `.env.example` обновлён. | Следующий шаг: перезапуск uvicorn; при своём `.env` с localhost — перезагрузить без смены файла (нормализация сработает). | Вопросы: нет | Статус: done

2026-05-04 | Действие: 500 на `/api/leads` — по логам не ORM, а обрыв TCP к Postgres (`ConnectionResetError` 10054, `ConnectionDoesNotExistError`). В `db/session.py`: `pool_pre_ping=True`, `pool_recycle` (+ опция в `.env.example`). | Следующий шаг: перезапуск uvicorn; проверить что Postgres стабилен (Docker/VPN). | Вопросы: нет | Статус: done

2026-05-04 | Действие: Дожат операционка под hotfix — строка в `CHANGELOG`, уточнён `HANDOFF` (след. шаг + voice WS). | Следующий шаг: смоук по HANDOFF. | Вопросы: нет | Статус: done

2026-05-04 | Действие: Фикс старта API — в `LeadFieldAudit` не был импортирован `Optional` для `audit_metadata`; добавлены `typing.Any`/`Optional` и аннотация `dict[str, Any]`; у `Lead.approvals` — то же для JSON. Импорт `main:app` проверен. | Следующий шаг: перезагрузить uvicorn; повторить запросы к `/api/leads/...`. | Вопросы: нет | Статус: done

2026-05-04 | Действие: P3 CRM points — UI чеклиста `approvals`, блок касаний и `eventType` в истории на `/leads/[id]`; merge апрувов в `enrichLeadForCard`; тесты бонуса/cap в `test_lead_score_advisory.py`; `docs/modules/leads.md` + батч `CHANGELOG`/`HANDOFF`. | Следующий шаг: смоук UI + перезапуск бэка/`init_db` для DDL; при необходимости — интеграционные тесты PATCH апрувов и POST communications. | Вопросы: нет | Статус: done

2026-05-03 | Действие: Аудит всех основных `docs/*.md`, сводка в `CHANGELOG`; заведены записи в `ISSUES` (🟡×2, 🟢×1); обновлены `HANDOFF`, `SESSION_STATE`. Файлы: `docs/operations/*.md`. | Следующий шаг: по приоритету пользователя — BA/PM дельта PRD или Backend политика БД (только с `go` на код). | Вопросы: нет | Статус: done

2026-05-04 | Действие: Architect Pre-Feature Gate — фича «балльные лиды как в CRM points»: осмотр `Lead`, `Task` (есть `lead_id`, `sla_due`), `crm_settings_store` (stages/thresholds, нет весов формулы). | Следующий шаг: ждать `go` — либо дельта `docs/product/PRD.md`+`docs/product/ARCHITECTURE.md`, либо сразу P1-код (веса+пересчёт) после явного go на миграции/контракт. | Вопросы: нет | Статус: in_progress

2026-05-04 | Действие: PM + Architect по `go` — расширены `docs/product/PRD.md` (роли, P1–P3, метрики, риски, приложения) и `docs/product/ARCHITECTURE.md` (домен лидов, API/DDL план, агенты); батч `CHANGELOG` + `HANDOFF`. | Следующий шаг: пользователь отвечает на приложение C PRD или подтверждает defaults из ARCH; затем `go` на P1 backend. | Вопросы: см. PRD приложение C | Статус: done (документный шаг)

2026-05-04 | Действие: P1 по `go` — суммы `amount_rub`/`paid_amount_rub`, `lead_score_advisory`, флаги CRM, `scoreAdvisory` в GET/PATCH лида, гейт `update_lead_score`, UI карточки, тесты `test_lead_score_advisory.py`; PRD/ARCH синхронизированы с решением «балл = менеджер». | Следующий шаг: смоук UI + при желании P2. | Вопросы: нет | Статус: done

2026-05-04 | Действие: Завершение итерации (`go` «добей») — оптимизация `page.subscribe` на карточке лида (fetch только при смене `id`); обновлён `docs/agents/langgraph.md` (гейт `update_lead_score`, `scoreAdvisory`); pytest `test_lead_score_advisory` + выборочные тесты зелёные; полный `tests/` падает на несвязанном `test_email_sync`. | Следующий шаг: P2 по отдельному `go`. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Техдельта v3 в доки — `voice_action`, email режимы, Search-to-Q&A, gate тендеров, lookalike, fanout; файлы: PRD, ARCHITECTURE, PRD_MAP, PRD_NOTES (журнал), langgraph, RAG, leadgen, tenders; ops батч. | Следующий шаг: проход Фазы 1 по PRD_MAP (ждать `go`). | Вопросы: нет | Статус: done

2026-06-07 | Действие: Правила структуры репо и сплита кода — `.cursor/rules/smartcrm-repo-layout.mdc`, `smartcrm-code-split.mdc`; канон `docs/dev/REPO_LAYOUT.md`; аудит `LAYOUT_AUDIT.md` (пакеты P1–P6 без переносов); обновлены CONTRIBUTING, docs/README. | Следующий шаг: пользователь выбирает `go P1`… для переносов. | Вопросы: нет | Статус: done

2026-06-07 | Действие: P1 layout — корневой `tests/` → `backend/tests/{api,core,rag}/`; `conftest.py` с auth для pytest; удалён `/tests/`; pytest: 25 passed (api+rag+hermes unit). | Следующий шаг: `go P2` или Фаза 1 PRD_MAP. | QA: api 13, rag 7, hermes parser 5 green | Статус: done

2026-06-07 | Действие: P2 layout — корень очищен; openapi → `docs/api/openapi/`; артефакты → `backend/data/artifacts/`; `.gitignore`; правила анти-мусора в `smartcrm-repo-layout.mdc`, REPO_LAYOUT. | Следующий шаг: ждать апрув — P3/P4/P5 или Фаза 1. | Статус: done

2026-06-07 | Действие: P3 — `backend/backend/data/` удалён; `tender_sources_ab.json` → `backend/data/`; комментарий в `tender_sources_ab.py` (cwd backend/). | Следующий шаг: апрув P4/P5 или Фаза 1. | Статус: done

2026-06-07 | Действие: P4 — `test_email_integration.py` → `backend/tests/integration/`; обновлён `docs/email/setup.md`. | Следующий шаг: апрув P5 или Фаза 1. | Статус: done

2026-06-07 | Действие: P5 — git-коммит миграции docs: удалены плоские `docs/*.md`, добавлены `start/`, `modules/`, `email/`, `voice/`, `archive/`, `ISSUES.md`; таблица в README. CRM-points-system не в git. | Следующий шаг: P6 или Фаза 1. | Статус: done

2026-06-07 | Действие: P6 (шаг 1) — сплит `api/routes/leads.py` → пакет `leads/` (6 файлов); pytest leads 21 passed. | Следующий шаг: P6 следующий файл по апруву или Фаза 1. | QA: 21 passed | Статус: done

2026-05-04 | Действие: P2 по явному `go` пользователя — `LeadComment`/`LeadFieldAudit`, `GET/POST /api/leads/{id}/comments`, `GET .../audit`, валидация `stage_transition_rules` при PATCH, аудит полей; `crm_settings` + Ops + публичный config; UI карточки лида (комментарии, история) и Ops JSON для правил; `core/stage_transition.py`, тесты `test_stage_transition.py`; правка `docs/product/ARCHITECTURE.md`. | Следующий шаг: P3/доки по сделке или смоук; референс Rails без кода в репо — уточнять по экранам при необходимости. | Вопросы: нет | Статус: done

2026-05-04 | Действие: Разбор референса `https://github.com/Razmik-Kutinava/CRM---points-system` — shallow clone в `docs/reference/CRM-points-system`; прочитаны `Lead`, `ScoreCalculator`, `LeadStateMachine`, `db/schema.rb` (булевы «апрувы»/доки на `leads`, `lead_histories`, `communication_logs`, авто-`score` после save). | Следующий шаг: по `go` — матрица переноса в PRD/ARCH или очередь фич (булевы флаги, communication log, формула как опция поверх advisory). | Вопросы: нет | Статус: done

2026-06-07 | Действие: Реорганизация `docs/` — папки product, start, api, modules, email, voice, agents, stack, operations, dev, archive, reference; `docs/README.md` карта; обновлены README, `.cursorrules`. | Следующий шаг: пользователь — полировка лидов по экранам. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Удалён устаревший alwaysApply-процесс; канон перенесён в `smartcrm-*.mdc`; ссылки в `.cursorrules` и operations. | Следующий шаг: вехи/доки по апруву пользователя. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Добавлено правило агента `.cursor/rules/smartcrm-agent-workflow.mdc` (коммиты, операционка, стоп до `go`); ссылка в `.cursorrules`. | Следующий шаг: ждать go пользователя (вехи/доки). | Вопросы: нет | Статус: done

2026-06-07 | Действие: Создан `docs/product/PRD_DELTA_v2.md` — дельта PRD v2 (Voice Layer, Email-агент, Self-improvement, Оркестрация, Тендеры, Аналитика v2). | Следующий шаг: по go — ревью/слияние в основной PRD или вехи. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Слияние PRD Delta v2 в `docs/product/PRD.md` — roadmap Фаза 1–3, дубли убраны, дельта помечена архивом. | Следующий шаг: по go — раскидать задачи по спринтам / полировка лидов. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Карта CRM из дельты вынесена в `docs/product/PRD_MAP.md`; дубль убран из `PRD.md` и `PRD_DELTA_v2.md`; ссылки в `docs/README.md`, `.cursorrules`. | Следующий шаг: по go — спринты по фазам из PRD_MAP. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Создан инбокс `docs/product/PRD_NOTES.md` — пользователь вставляет отрывки по модулям/фазам/навигации для последующего разбора. | Следующий шаг: пользователь загружает тексты в PRD_NOTES. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Из PRD_NOTES собраны чеклисты Фаза 1–3 в `PRD_MAP.md` ([x] сдано + хвосты); NOTES: навигация, роуты, стек-placeholder, журнал. | Следующий шаг: проход Фазы 1 по PRD_MAP (баги в ISSUES). | Вопросы: нет | Статус: done

2026-06-07 | Действие: Оглавление в начале `PRD_NOTES.md` (модули, агенты, фазы, строки). | Следующий шаг: по go — проход Фазы 1. | Вопросы: нет | Статус: done

2026-06-07 | Действие: P6 hermes — `core/hermes.py` → пакет `core/hermes/` (config, prompts, parse, rescue, cache, providers); rollout → `config`; тесты Parser 5 passed + voice prompt 1 passed; `LAYOUT_AUDIT` обновлён. | Следующий шаг: `go P6 ops` или Фаза 1. | Вопросы: нет | Статус: done

2026-06-07 | Действие: P6 ops — `api/routes/ops.py` → пакет `api/routes/ops/` (10 модулей, 34 роута); тест review_fixes + hermes Parser 6 passed; коммит P6 hermes+ops. | Следующий шаг: P6 pipeline/search/tenders или Фаза 1 PRD_MAP. | Вопросы: нет | Статус: done

2026-06-07 | Действие: P6 остаток — `qa/`, `tenders/`, `analyst/`, `rag/search/`, `leadgen/pipeline/`, `checko/`; фикс cross-imports + `_resplit_leadgen_pkgs.py`; тесты leadgen+voice+tenders+qa+analyst+rag: **114 passed**. | Следующий шаг: Фаза 1 PRD_MAP. | Вопросы: нет | Статус: done

2026-06-07 | Действие: коммит `725b284` (P6+CRM+tenders+leads UI) + push `main` → origin (25 коммитов). | Следующий шаг: **Фаза 1 PRD_MAP** — баги/чеклист в ISSUES. | Вопросы: нет | Статус: done

2026-06-07 | Действие: 15× `backend/**/README.md` (карта бэкенда); ссылка в REPO_LAYOUT; черновик правила README-sync — ждёт апрув. | Следующий шаг: апрув правила → push. | Вопросы: нет | Статус: in_progress

2026-06-07 | Действие: push `351fc23` — backend README pack + BACKEND_README_SYNC_DRAFT. | Следующий шаг: апрув правила → влить в smartcrm-repo-layout.mdc. | Вопросы: нет | Статус: done

2026-06-07 | Действие: правило §5 Backend README Sync в `smartcrm-repo-layout.mdc`; DRAFT → применено; CHANGELOG+HANDOFF. | Следующий шаг: push; ждём задачу пользователя (Фаза 1 PRD_MAP). | Вопросы: нет | Статус: done

2026-06-07 | Действие: `smartcrm-task-workflow.mdc` (go, тесты, авто commit/ops, push/deploy по апруву); ссылка в repo-layout §6. | Следующий шаг: ждём пункт PRD_MAP от пользователя. | Вопросы: нет | Статус: done

2026-06-07 | Действие: § anti-hallucination в task-workflow (честный отчёт «Не сделано / не проверено»). | Следующий шаг: ждём пункт PRD_MAP. | Вопросы: нет | Статус: done

2026-06-07 | Действие: BACKLOG.md + § бэклог в task-workflow (связь с пунктами PRD_MAP, фаза опционально). | Следующий шаг: ждём пункт PRD_MAP. | Вопросы: нет | Статус: done

2026-06-07 | Действие: smartcrm-dev-gates.mdc (DoD, регрессия, миграции, API, hot-path); .cursorrules→индекс; agent-workflow+BACKLOG. | Следующий шаг: ждём пункт PRD_MAP. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Аудит правил — канон в `smartcrm-*.mdc`; п.0 коммит+ops; honest report; `run_zone_regression.py`; CURSOR_USER_RULES_SNIPPET. | Следующий шаг: Фаза 1 PRD_MAP + go. | Вопросы: нет | Статус: done

2026-06-07 | Действие: коммит `28ab125`; регрессия p1/p6 PASS, hermes_eval 9 FAIL → ISSUES+BACKLOG. | Следующий шаг: Фаза 1 PRD_MAP + go. | Вопросы: push по апруву | Статус: done

2026-06-08 | Действие: ops sync — RULES_MATRIX, check_agent_step.py, fix agent-workflow.mdc, BACKLOG/PRD_MAP, зачистка журналов, archive rename. | Следующий шаг: Фаза 1 PRD_MAP (интенты Hermes) + go. | Тесты: p6 PASS, check_agent_step | Статус: done

2026-06-08 | Действие: коммит `bcce33c` (ops sync). Регрессия p6: All zones passed (121 tests). | Следующий шаг: Фаза 1 PRD_MAP + go. | push по апруву | Статус: done

2026-06-08 | Действие: push `main` → origin (6 коммитов: rules + ops sync). | Следующий шаг: Фаза 1 PRD_MAP с начала — пункт + go. | Статус: done

2026-06-08 | Действие: правила — коммит+ops безусловно; check_agent_step FAIL на незакоммиченное. | Коммит: `86a8e7a` | Статус: done

2026-06-08 | Действие: коммит `86a8e7a`. | Следующий шаг: Фаза 1 PRD_MAP + go. | Статус: done

---
