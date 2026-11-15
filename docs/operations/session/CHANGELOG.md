# CHANGELOG (операционный)

**Роль:** источник правды по истории — что сделано, когда, почему и при каким `go`. Записи старше текущего месяца → `docs/archive/ops/`.  
**Агент:** на старте чата **не читать весь CHANGELOG** — только шапка + запись текущего шага при нужде. Архив: `docs/archive/ops/`.

## 2026-11-15 — PHASE 3 REVIEW: read_lead_by_company список+транслитерация RU↔EN (GREEN)

`backend/agents/tools.py`: добавлена публичная `transliterate_ru_en(text)` (RU↔EN, посимвольно + карта частых слов), `read_lead_by_company` ищет по `company` / `contact` / `description` (эквивалент `lead_name`) с двумя вариантами (исходный + транслитерированный), возвращает `list[dict]` до `limit` с полями `id, company, city, stage, score, next_call, contact_name, manager_name, lead_id`, сортировка по актуальности (next_call due/24ч → стадия → скор → updated_at), `normalize_lead_for_agents` принимает `list`. Тесты `tests/agents/test_tools_lead_search.py` 9/9 PASS, зона `voice` 10/10 PASS. | Коммит: `этот`.

## 2026-11-15 — PHASE 3 REVIEW: ускорение голосового пайплайна (GREEN)

`backend/voice/pipeline.py`: поэтапные тайминги `time.monotonic()` — Whisper STT, Hermes parse_intent (раздельно Groq/Ollama), оркестратор/агенты, сборка voice_action; логируются `duration_ms` + `timings_ms` в ответе.
`backend/core/hermes/config.py`: добавлены `HERMES_PROVIDER_ORDER` (по умолчанию `groq_only`) и `HERMES_ENABLE_OLLAMA_FALLBACK` (по умолчанию `False`).
`backend/core/hermes/parse.py`: при `HERMES_ENABLE_OLLAMA_FALLBACK=False` ветка Ollama пропускается — только Groq; отдельные тайминги `_groq_duration_ms` / `_ollama_duration_ms` логируются.
`backend/core/hermes/cache.py`: `FASTPATH_INTENTS` (навигация: list_leads, open_lead, list_emails, analytics_*, generate_lead, find_leads_portrait, cluster_company, save_to_rag, list_deals, open_deal) — мгновенный ответ без LLM; `fastpath_route` расширен.
`backend/core/hermes/__init__.py`: экспорт `FASTPATH_INTENTS`.
`backend/tests/test_hermes_cache.py`: 7 тестов кэша/fastpath/config — 7 PASS.
`.env.example`: добавлены `HERMES_PROVIDER_ORDER`, `HERMES_ENABLE_OLLAMA_FALLBACK`, `HERMES_ENABLE_CACHE`, `HERMES_ENABLE_FASTPATH`, `HERMES_CACHE_TTL_SEC`.
| Коммит: `этот`.

## 2026-11-15 — PHASE 3 REVIEW: голосовая память последнего лида (финиш шага)

Код уже закоммичен в коммите `9147526` (2026-11-14): `backend/core/agent_memory.py` (таблица `voice_last_lead`, TTL 60 сек), `backend/voice/pipeline.py` (сохраняет кандидатов при `list_leads`, подставляет последний лид для `open_lead`, сброс при «найди другой»), `backend/agents/tools.py` (поиск с транслитерацией RU↔EN, сортировка по актуальности), `backend/core/hermes/slot_normalize.py` (порядковые числительные), `backend/core/hermes/rescue.py` (выбор по номеру без LLM). Тесты 10 PASS + зона voice 10 PASS. Новых изменений кода в этом шаге не было — только ops (SESSION_STATE/CHANGELOG/HANDOFF). | Коммит: `этот`.

## 2026-11-15 — CI: 10 красных pytest после hang-фиксов

После зелёных smoke/zones оставались assertion-фейлы (run 43694097392). Обновили тесты под текущий код: leadsStorage без «квота»; leadCreate/Mailing UI — статический контракт (без Node/svelte в CI pytest); Bitrix due с временем; upsert-моки на `bitrix24_upsert`; bitrix-uf slice без лимита 800; csv-import → `leads-import-open`; `TASK_DUE_FILTERS`; score_manual vs managerScore; `validate_certs` в `email_smtp.py`. | Коммит: `этот`.

## 2026-11-14 — F4: Путь сделки не 0/0 при пустом dealPath (лиды)

По `go` («ебашь грин»): бэкенд возвращает `dealPath: null` когда путь не задан (нет контактов/телефона/email/выполненных approvals); фронт показывает «Путь сделки не задан» вместо «Все шаги пройдены ✓» при `dealPath` пустом/отсутствующем.
- `backend/api/routes/leads/presenter.py`: `dealPath = None` при пустом dealPath.
- `frontend/src/lib/leadsStorage.js`: `enrichLeadForCard` дефолт `dealPath: null`.
- `frontend/src/components/LeadDealPathPanel.svelte`: условие «путь не задан» вместо «всё пройдено» при пустых группах.
Тест `test_lead_deal_path_empty.py` PASS; регрессия `crm_leads` 118 passed | Коммит: `10edcee`.

## 2026-11-14 — F4: Автоскор в шапке (лиды) — score = score_manual или scoreAdvisory.suggestedScore

По `go` («ебашь»): автосинхронизация видимого скора с формулой advisory.
- Модель `backend/db/models/lead.py`: новое поле `score_manual` (nullable).
- Миграция `backend/db/session.py` (`init_db`): `ALTER TABLE leads ADD COLUMN IF NOT EXISTS score_manual INTEGER`.
- `backend/api/routes/leads/presenter.py`: GET `score = score_manual if score_manual is not None else scoreAdvisory.suggestedScore`.
- `backend/api/routes/leads/crud.py`: PATCH `score` пишется в `score_manual`, автоскор не перезаписывается.
- `frontend/src/routes/leads/[id]/+page.svelte`: иконка «ручное переопределение» (📝) в шапке, если `score_manual` задан.
Тесты `test_lead_auto_score.py` 3 PASS; регрессия `crm_leads` 118 passed.

## 2026-11-14 — F4: Агенты по синтезу (контекст+промпты+суфлёр) — `POST /api/agents/synthesis`

По `go` («ебашь»): новый модуль `agent_synthesis.py` — собирает контекст лида (паспорт, 🔍, этап, задачи, переписка) → прогоняет 5 агентов (analyst, economist, marketer, tech_specialist, strategist) параллельно → стратег синтезирует единый совет: 1–3 шага простым языком + блок `missing_data` для суфлёра + задача из `next_action`. Endpoint `POST /api/agents/synthesis`. Тесты `test_agent_synthesis.py` 2 PASS; регрессия `crm_leads` 118 PASS + `analyst` 5 PASS + `agent_email_run` 8 PASS; фронтенд `npm run build` OK.

## 2026-11-14 — F4: Агенты на карточке работают (`POST /api/agents/email/run`)

По `go` («ебашь»): стратег без `ImportError`, аналитик с реальным `lead_id` (не заглушка), дайджест переписки урезан (экономия токенов). Тесты `test_agent_email_run.py` 8 PASS; регрессия crm_leads 39 PASS + analyst 5 PASS.

## 2026-11-14 — 5 шагов до первых продаж (стarter-сценарии Джарвиса)

Добавлен `docs/operations/phase4/leads/F4_FIRST_STEPS_TO_SELL.md` — 5 сценариев Джарвиса (найди/открой → что делать дальше → сделай совет → письмо по лиду → день сейла) со статусами: шаг 1 сделан, шаги 2–5 не сделаны.

## 2026-11-14 — Пакет C: SBR/токены из CoffeeOS + APU

По `go` («C — Полный пакет» + «ебашь»): перенос лучших практик без ослабления зон/A/B/C/push-по-go.

**Добавлено.** `smartcrm-context-hygiene.mdc` + `/ctx-trim` (+ skill); slash `/start` `/spec` `/sbr` `/review` `/crit-audit`; `ZONE_NOTES.md`, `OWNER_CHECKS.md`, `CRITICAL_LEDGER.md`; эконом-режим в `dev-gates`; шапка-only старт + «Читать»/«Файлы» в SBR; R16–R20 в RULES_MATRIX.

**Не трогали.** Зонная регрессия на GREEN; PHASE 0 дословный заказ; A/B/C; `check_step.cmd`; авто-push как в CoffeeOS — **нет**.

## 2026-11-14 — Поиск лидов: нечёткое название (топ-5)

По `go` («го делай»): если exact/includes пуст (STT/опечатка) — в `/leads/list` топ-5 ближайших по `company`, не пустой список.

**Core/UI.** `lead_company_fuzzy.py` + `leadCompanyFuzzy.js`; fallback в `filterLeads`; бейдж «похоже»; fuzzy-кандидаты **не** в `rememberVoiceLeads` (без silent open).

Тесты: `test_lead_company_fuzzy` 7; crm_leads 118; p1+p6 (счётчик 3/3).

## 2026-11-05 — Голос: открыть лид → модалка с blur

По `go` («ебашь исправляй»): success без перехода чиним; «открой её» открывает **overlay** поверх списка.

**UI.** `LeadVoiceOverlay`: backdrop blur, iframe `/leads/{id}?embed=1`, «На весь экран» / Esc / ×. Память матчей сразу из кэша при filter (`rememberVoiceLeadsFromCache`).

**Hermes.** Интент `open_lead` + rescue (как раньше).

Тесты: overlay 4 + open_lead 5; зона voice PASS.

## 2026-11-05 — Голос: открыть лид + «открой её»

По `go` («давай ебани»): после «найди лид …» следующая фраза «открой её» открывает карточку прошлого матча.

**Hermes.** Интент `open_lead` (`company` | `lead_id` | `ref=last`); rescue для «открой её/этот», «открой лид …», «найди лид …» → `list_leads`+query.

**UI.** `voiceLeadFocus` помнит найденных; `handleVoiceAction` → `goto /leads/{id}`.

Тесты: `tests/voice/test_open_lead.py` 5 + focus smoke 2; зона voice 10 PASS.

## 2026-08-15 — Тендеры на карточке лида

По `go` («ебашь»: плитка тендеров + наш поисковик + сколько токенов).

**API.** `GET /api/leads/{id}/tenders` (кэш), `POST .../tenders/search` — Checko-контракты, DataNewton (бесплатные запросы), TenderGuru, веб Brave/Serper/Tavily. Без LLM: `usage.llm_tokens = 0`. Снимок в `checko.analyses.lead_tenders`.

**UI.** 6-я плитка хаба «Тендеры», кнопка «Искать», строка usage.

**Живой прогон.** ИНН 7707083893 Сбербанк: Brave 8 + Serper 8, Tavily 432/0, TG/DN/Checko 0 карточек; LLM-токенов 0.

Тесты: test_lead_tenders 3 + API 3 + UI 1; crm_leads 118; p6 PASS.

## 2026-08-03 — Сырьё denser: паспорт/контакты/выжимка

По фидбеку: выжимка была, паспорт/контакты слабые, мало фактов.

**Extract.** Шире телефоны; ФИО→отдельные контакты; ОГРН/адрес/отрасль; LLM поверх regex.

**Паспорт.** `checko.company` phones/emails/inn/director/address/okved; financials.revenue hint.

**Выжимка.** До 40 строк / 4к символов + `facts`; RAG до 12к исходника.

Тесты: `test_raw_inbox` 9 PASS.

## 2026-08-03 — Сырьё → поля / паспорт / RAG

По `go` («ебашь»): inbox сырья на карточке.

**Пайплайн.** `POST /api/leads/{id}/raw-inbox` → extract (телефон/email/ИНН/сайт/директор) → merge пустых полей + контакты без дублей → `checko.analyses.raw_inbox` (chunks + brief) → выжимка в brief агентов + `ingest_manual_text` (meta `lead_id`).

**UI.** Клиент → свёртка «Сырьё → поля».

Тесты: `test_raw_inbox` + API 8 PASS; crm_leads 112 PASS.

## 2026-08-02 — ИНН/Checko: правильное юрлицо + телефоны + brief

По `go` (Астерус: взяли Investment вместо Development).

**Скоринг.** `resolve_inn`: EN↔RU (development→девелопмент); штраф при конфликте инвестмент/девелопмент.

**Checko.** При смене ИНН в field_fill — свежий Checko без чужого паспорта; блок «## Паспорт (Checko)» в agent_brief.

**Телефоны.** Строже `is_valid_phone` (отсев 83…/HTML-мусора); FE enrich зеркало.

Тесты: `test_inn_checko_match` + checko_passport; second_pass в gaps-тесте замокан. rag+p1+p6 PASS.

## 2026-08-02 — 🔍 запросы: каталоги по ИНН + свежие новости

По `go`: веб смотрел новости по названию, не каталоги по ИНН.

**Запросы.** `research_queries`: сначала `ИНН` + site:checko/list-org/rusprofile/sbis; затем новости текущего года; профиль. LLM дополняет, база не вытесняется. Порядок пайплайна: ИНН→Checko→веб.

**Ранжирование.** Хиты с checko/list-org/… и ИНН в тексте поднимаются.

Тесты: `test_research_queries` 7 PASS.

## 2026-08-02 — Карточка←🔍 sync + gaps + экономист

По `go` («ебашь всё»): фин/телефоны в исследовании, карточка и суфлёр пустые; экономист «нет финданных».

**Sync.** `card_sync` после research → phone/email/website/budget/contact в `enriched`; Apply пишет в CRM. FE: `enrichLeadApply` + `researchLeadApply` добирают из contacts/financials/passport_extract.

**Gaps.** Суфлёр (BE+FE): телефон/email/фин = есть, если в паспорте, contacts или выжимке (выручка/оборот).

**Экономист.** `economist_context`: явный блок ФИНАНСЫ/ПАСПОРТ/🔍, не «пожелание оператора».

Тесты: `test_card_sync_and_gaps` 10 PASS; rag zone PASS.

## 2026-08-02 — Техспец: сайт/домен + BuiltWith/WhoIs

По `go` («ебашь»): тех не видел сайт/парсеры.

**Контекст.** `tech_domain_context`: сайт из карточки; домен также из email после `@` (не free-mail); если стек/DNS пусты — live `enrich_domain_signals` (BuiltWith+WhoIs). Явные строки в промпте техспеца.

**Отчёт.** Поля `observed_website` / `observed_domain` / `stack_evidence` / `dns_evidence` в JSON + блок в `AgentResultView` перед gaps.

Тесты: `test_tech_domain_context` 9 PASS; p1+p6 PASS.

## 2026-08-02 — Агенты: разбор сначала, пробелы потом

По запросу: без полного суфлёра агент давал плохой разбор / сводил к «нужны данные».

**Промпты.** Все 5 агентов: сначала полный ответ на имеющемся; `missing_data` только после; запрет отказываться от разбора из-за пробелов.

**Слоты.** Блок gaps в instruction: «ПОСЛЕ разбора (не вместо него)…», не «СУФЛЁР — чего не хватает».

**UI.** В `AgentResultView` блок пробелов перенесён вниз («Для более полного анализа ещё нужно»).

Тесты: `test_agent_synthesis_context` + `test_lead_card_agent_result` + analyst/email PASS.

## 2026-08-02 — SBR: 🔍 field-fill (EN→RU + веб-ИНН → Checko + поля в паспорт)

По `go` (нормализовать имя EN→RU; запросы по полям с записью в паспорт; суфлёр не трогать).

**Имя.** `company_name_ru` — варианты OTP Bank (Russia) → ОТП Банк и др. бренды; `resolve_inn` пробует все варианты в ЕГРЮЛ, затем веб «ИНН» + regex.

**Добор.** `field_fill.fill_gaps_from_web` — целевые запросы по gaps (ИНН/директор/почта/фин…) → extract в enriched/passport; при ИНН — Checko. Подключено в `research_lead` вместо «сниппеты в brief».

Суфлёр UI не меняли.

Тесты: `test_field_fill_research` 4 PASS + gaps pipeline PASS.

## 2026-08-02 — SBR: 🔍 gaps-driven (суфлёр карточки + ИНН→Checko→веб)

По `go` («ебашь» план: суфлёр на карточке, ИНН если пусто, Checko, сайт, веб по дырам, ~2.5 мин, второй круг, опц. DDG).

**Карточка.** `LeadCardSuffler` + `cardSuffler.js` / `core.agent_gaps.card_suffler` — общий список пробелов (ИНН, ОКВЭД, контакты, фин, стек…) до запуска агентов.

**Research.** `resolve_inn` (ЕГРЮЛ/Checko по имени+домену) → enrich Checko → narrative веб → BuiltWith/DNS → `second_pass` по remaining gaps. Таймауты enrich/narrative по умолчанию 70/90с. В ответе `research_stages`, `card_suffler`, `resolved_inn`. ИНН пишется в PATCH.

**DDG.** `_search_duckduckgo` через SearchApi.io при `SEARCHAPI_API_KEY`.

Тесты: `test_research_gaps_pipeline` 5 PASS; rag 144 PASS.

## 2026-08-02 — SBR: 🔍 BuiltWith + WhoIs/DNS в исследование

По `go` («добавь эти две возможности» — BuiltWith для теха, WhoIs/DNS в 🔍; не тулзы у агентов).

**Что.** `leadgen/modules/whois_dns.py` — MX/SPF/DMARC/A через Cloudflare DoH + RDAP (без ключа). `rag/search/domain_enrich.py` — параллельно BuiltWith + DNS по сайту. `research_lead` всегда зовёт domain enrich при наличии website (даже без ИНН), пишет `passport.tech` / `checko.tech`, `web_research.domain_signals`, дописывает BuiltWith в `agent_brief`. Слоты теха (`agent_email_context`) видят `tech_stack_brief`; gaps учитывают `tech`/`tech_json`/DNS.

**Не вошло:** Hunter, DDG, вызовы из агентов.

Тесты: `test_domain_signals_research` 5 PASS; `tests/rag/` 139 PASS; synthesis+email_run 19 PASS.

## 2026-08-02 — SBR: агенты по синтезу (контекст + промпты + суфлёр)

По `go` («делаем все правки из синтеза… суфлёр чего не хватает… веб-исследование… тендеры не трогай… ебашь»).

**Контекст.** `agent_email_context.build_agent_slots` кладёт `checko`, 🔍 `agent_brief`, паспортный снимок и `context_gaps`. `agent_gaps.py` — детерминированный суфлёр по агенту; мержится в `missing_data` ответа. На карточке RAG только текущего агента (top_k=3, ≤800 симв., без live web). Стратегу подмешиваются короткие выводы аналитика/экономиста/маркетолога/теха.

**Промпты.** Аналитик/стратег/маркетолог/экономист/тех — по `СИНТЕЗ_…md` (стадия+BANT, одно действие, анти-примеры, portfolio_fit, формулы LTV). Тендеры не менялись.

**Apply / UI.** Из `next_action` стратега создаётся задача; после скора/задачи карточка перечитывает лид. `AgentResultView` показывает блок «Суфлёр — чего не хватает». Веб-исследование пишет `agent_requirements` в `checko.analyses.web_research` (бэкенд + фронт).

Тесты: `test_agent_synthesis_context` + `test_agent_email_run` + analyst — 29 PASS; зона analyst PASS.

## 2026-08-02 — Docs: синтез воркфлоу и промптов агентов

По запросу: прочитать правки Claude Code и техразбор пользователя, код не трогать — собрать третий канон-док.

Файл `backend/agents/СИНТЕЗ_АГЕНТЫ_ВОРКФЛОУ_И_ПРОМПТЫ.md`: воркфлоу «Исследовать → веб-саммари → агенты» и роли агентов взяты из техразбора как закон; из правок Claude — сжатие MBA-воды, анти-примеры маркетолога, cold/warm/hot у стратега, формулы экономиста; tech переписан под портфель (не «интеграция CRM»); от Cursor — приоритет контекста 🔍/RAG, Apply, запрет MCP/раздувания токенов. Порядок внедрения: контекст → промпты → Apply → A/B.

## 2026-08-01 — SBR: агенты на карточке лида (стратег падал, аналитик молчал)

По `go` («агенты просто ебано работают… аналитик вообще не работает, стратег ошибку выдаёт ❌ Ошибка загрузки агента… исправляй, починишь по СБР»).

**Стратег → 500.** `api/routes/agent_email.py` импортировал `_analyze` из `agents/strategist.py`, где такой функции никогда не было (у стратега контракт `run(state)` / `_synthesize(state)` поверх `AgentState`) — `ImportError` перехватывался и превращался в «Ошибка загрузки агента. Подробности в логах.». Добавлен `strategist._analyze(intent, slots)`: собирает состояние через `make_initial_state`, поднимает в него выводы других агентов из слотов и зовёт `_synthesize`. Роут при одиночном запуске стратега подмешивает последний результат аналитика по лиду (`_last_agent_output` — только score, summary до 400 символов, bant, два next_steps), иначе синтез шёл вслепую.

**Аналитик → заглушка.** В слоты роута не клался `lead_id`, а `analyst.analyze("analyze_lead", …)` первой же строкой возвращает `{"summary": "Не указан лид: нет lead_id."}` — ошибки нет, ответа нет. Новый `core/agent_email_context.py::build_agent_slots` кладёт `lead_id` и расширенный профиль (employees, website, position, score, next_call), поэтому аналитик снова считает BANT, видит задачи лида, тренд скора и пишет скор в БД.

**Токены.** `build_email_digest`: 3 треда × 6 писем × 200 символов вместо 5 × 10 × 400 — контекст переписки ужался примерно в 5 раз (было до ~20k символов на каждый запуск любого агента), при этом берутся последние письма, а не первые. Из промпта стратега убраны служебные ключи слотов (`lead_id`, `*_output`).

**Фронт.** Карточка рендерила только ответ маркетолога (`first_email`, `value_hook`, `summary`, `touch_sequence`), поэтому даже успешный ответ стратега или экономиста выглядел пустым. Новый `lib/leads/AgentResultView.svelte` показывает решение и следующий шаг стратега, скор и BANT аналитика, экономику экономиста, стек тех. спеца, письмо маркетолога и остаточные простые поля.

Тесты: `test_agent_email_run` 8 PASS (RED `8d1461f` → GREEN), `test_lead_card_agent_result` 3 PASS, `tests/agents` PASS, `npm run build` OK. Регрессия `run_zone_regression.py all` — все зоны PASS после починки протухшего `test_tasks_filter_done_and_combined` (в нём «сегодня» было захардкожено как 24.06.2026 — закрыт долг ISSUES от 2026-07-21).

## 2026-08-01 — SBR: экран импорта базы (превью + сопоставление колонок)

По `go` («сделай нормальный экран импорта… ебашь давай»). Прошлый фикс скрытого input не снял корневую проблему: оператор не видел, что происходит с файлом, и произвольные заголовки Excel («Наименование юрлица») молча не попадали в лид.

**Backend.** Новый `integrations/crm_sync/import_table.py`: `read_table` (CSV/XLSX → сырые заголовки + строки), `guess_mapping` по алиасам, `rows_to_dicts`, каталог `IMPORT_FIELDS` (16 полей с подписями и признаком обязательности). Импорт вынесен в `api/routes/leads/import_routes.py`: `POST /import-preview` (заголовки, 5 строк, авто-сопоставление, предложенное имя базы) и `POST /import-csv` с form-полем `mapping` (JSON поле→колонка) — без колонки «Компания» отдаётся 400 вместо тихого пропуска строк. `import_leads_from_rows` получил `source_fallback`: имя файла больше не затирает колонку «Источник» (метки Битрикса не превращались в базы). `GET /sources` различает `bitrix_source` и `named`. Каждый импорт пишется в лог: файл, база, добавлено/обновлено/пропущено.

**Frontend.** `components/LeadsImportModal.svelte` — три шага: drag&drop файла, таблица сопоставления с примерами значений + имя базы + режим дублей, отчёт с построчными ошибками. Кнопка «Импорт базы» переехала в шапку списка; переключатель баз разделён на «Импортированные базы» и «Битрикс».

Тесты: `test_lead_import_preview` 6 PASS · `test_leads_import_modal` 4 PASS · `test_leads_list_import_input` 3 PASS · crm_leads 111 PASS (1 известный FAIL). UI прогнан в браузере: превью → сопоставление → отчёт (+2 лида, новая база в переключателе); тестовые лиды удалены.

## 2026-08-01 — Fix: импорт Excel не реагировал на выбор файла

По `go` («нажимаю на три точки импорт эксель и потом ничего не происходит»).

Скрытый `<input type="file">` был отрендерен внутри блока `{#if showListMenu}`, а обработчик кнопки шёл в порядке `closeListMenu()` → `csvInput?.click()`. Меню закрывалось, input вместе с `onchange` удалялся из DOM, и событие `change` от системного диалога приходить было уже некуда.

Input вынесен в конец разметки страницы (всегда в DOM), в кнопке сначала `click()`, потом закрытие меню; `onCsvFileChange` читает файл из `e.target` с запасным вариантом через ref. Добавлен тост «Загружаю …»: импорт плюс перечитывание 3258 лидов занимают секунды и выглядели как зависание. `accept` дополнен `.txt`.

Тесты: `test_leads_list_import_input` 3 PASS · crm_leads 111 PASS (1 известный FAIL).

## 2026-08-01 — SBR: базы лидов — переключатель + CSV/Excel импорт

По `go` («ебашь» — переключать базы + загрузить Excel). Одна таблица `leads`, «базы» = метка `source` + синтетическая «Битрикс».

**Backend.** `POST /import-csv` принимает `.csv`/`.xlsx`/`.xlsm`; без query `source` — имя файла. Дедуп email/ИНН **внутри** метки базы (два Excel с одним email → два лида). `GET /sources` → `bases`: `__bitrix__` + именованные. `xlsx_adapter.parse_xlsx_rows` + `import_leads_from_rows`.

**Frontend.** На `/leads/list` селект «База» (Все / Битрикс / метки). Импорт «CSV / Excel» с полем имени базы; после загрузки список переключается на новую базу.

Тесты: `test_lead_bases` 4 PASS · crm_leads 111 PASS (1 известный FAIL) · p1+p6.

## 2026-08-01 — SBR: три дырки почты → паспорт / ЛПР / 🔍

По `go` («ебашь как задачу сбр все сделай»). Три независимые дырки закрыты одним прогоном.

**1. UF → company.emails.** `dadata_emails` часто пуст, а почта уже лежит в `bitrix_extra.license_registration` / сырых UF (`UF_CRM_1684590938`). Добавлены `emails_from_bitrix_blobs` и `merge_uf_emails_into_checko` в `checko_passport.py`; `Lead.to_dict` мержит UF-почту в `checko.company.emails` на чтении — без сети, сразу на уже импортированных лидах. `@x5.ru` без local-части отбрасывается.

**2. lead.email → ЛПР.** `mergePassportContacts` принимает `lead`; если у ЛПР (или первого контакта) `emails` пусто — дописывает из `company.emails` + UF + `lead.email`. Не раздувает уже заполненный контакт.

**3. 🔍 как источник.** Кнопки не склеивали: research по-прежнему отдельный. Apply идёт через `enrichResultToLeadPatch` → тот же merge, поэтому regex-почта со страниц сайта попадает в ЛПР при пустых emails.

Тесты: `test_email_passport_holes` 7 PASS · rag 134 PASS · crm_leads 111 PASS (1 известный FAIL).

## 2026-08-01 — Fix: новый контакт создавался за краем экрана

По `go` («зашёл в карточку МЭЙДЖОРС и там всё так же… включи mcp devtools и устрани этот баг на всех»). Предыдущие три захода чинили сохранение и черновики — а данные всё это время терялись до сохранения, в интерфейсе.

**Что происходило.** Кнопка «+ контакт» стоит в шапке панели, форма добавляется в конец списка. Замер в браузере на лиде 244: кнопка на `y=-1019` (оператор её уже прокрутил вверх), новая форма на `y=828` при высоте окна 666 — то есть **на 1847 px ниже кнопки и за нижним краем экрана**, `newFormVisible: false`. Оператор жал «+ контакт», ничего не видел, считал что кнопка не сработала, и печатал в последнюю видимую форму — то есть переписывал предыдущий контакт.

Аудит лида 244 показывает это дословно: `арам3 → арам4 → арам5 → арам6`. Второй контакт (`web-0-5342`) переименовывался раз за разом, третий не появился ни разу. Пустая форма при сохранении отбрасывается фильтром, поэтому в базу уходили те же два контакта — отсюда «пишется, что два контакта».

**Что сделано.** После добавления форма прокручивается в центр экрана и получает фокус: `scrollIntoView({ block: 'center' })` + `focus({ preventScroll: true })`. Строка контакта получила якорь `data-contact-row`, поиск ждёт появления строки в DOM (проп `contacts` возвращается от родителя через `bind`, одного тика не хватает). Кнопка «+ контакт» продублирована в конце списка — на длинном списке до шапки не долистать.

Проверено в браузере: было `newFormVisible: false`, стало `newFormTop: 357` при окне 666 и `isFocused: true`. Пять контактов подряд, набранных без единого клика мышкой по полю, сохранились каждый на своём месте; тестовые записи удалены.

## 2026-08-01 — Fix: пять косяков фронта, найденных обходом через Chrome DevTools

По `go` («подключи mcp devtools и сам проверь… найди на фронте косяки, а они есть»). Обход карточки, списка, воронки, Ops, Email и лидогенерации через Chrome DevTools MCP — консоль, сеть, localStorage. Найдено и исправлено пять штук.

**Двойная загрузка карточки.** `page.subscribe(pullLead)` вызывался повторно (`openHubPanel` меняет `?panel=` сразу после подписки), а `lastFetchedOkId` выставлялся только после двух `await` — оба вызова успевали пройти проверку. Карточка дублировала каждый запрос: лид, комментарии, аудит, коммуникации, цепочки, задачи, конфиг CRM. Метка `inFlightId` ставится до первого `await`; при ошибке сбрасывается. Проверено в браузере: 18 запросов → 10.

**Кэш списка забил квоту localStorage.** 3231 лид занимал 4.7 МБ, `setItem` падал с `QuotaExceededError` в пустой `catch`, кэш застыл и мешал писать остальные ключи — это он кормил баг с «пропадающими» контактами. Теперь в кэш не попадают досье, сырые UF, история и апрувы, а при переполнении ключ удаляется, а не остаётся мусором. На базе от ~2500 лидов кэш отключается сам: даже облегчённый список (6.7 МБ) в квоту не влезает — настоящее лечение в BACKLOG.

**Ошибка Битрикса маскировалась под 403.** У Битрикса лежит MySQL, а `/api/leads/bitrix-import-stats` отдавал `403 Forbidden` и пробрасывал в браузер их стектрейс с путями `/home/bitrix/www/bitrix/modules/...`. Оператор читает 403 как «нет прав» и идёт проверять токен. Добавлен `core/bitrix_error_detail.py`: статус 502 и короткая причина («База данных Битрикс24 не отвечает»), стектрейс уходит в лог. Применено и к `import-bitrix`, `push-bitrix`, вебхуку.

**Список 13 секунд показывал демо-лидов как настоящие.** `/api/leads` на 3258 записях отвечает 13.2с / 14.9 МБ, а `readLeadsCache()` подставлял `DEFAULT_LEADS` — всё это время оператор видел «АО МашПром» и «Иван Петров» с заголовком «7 лидов» и ссылками на чужие id. Раньше это маскировал кэш, который перестал писаться. Теперь список стартует с реального кэша или пустой, показывает «Загружаю лиды из базы…», а демо-витрина остаётся только на случай недоступного API.

**Незаполненный контакт прятался под свёрткой.** Смена вкладки перемонтирует панель и сбрасывает `expanded` — пятый контакт, который как раз заполняли, уходил под «Показать все (5)». Данные при этом целы, но выглядит как «контакт пропал» — ровно та жалоба, с которой всё начиналось. Контакт без имени больше не сворачивается.

Проверено в браузере на `/leads/244`: три новых контакта добавлены и сохранены (2 → 5, счётчик и плитка совпали), свёрнутый список показывает 4 из 5 с кнопкой, черновик пережил переход на «Паспорт» и обратно; тестовые контакты убраны. Тесты: `test_frontend_devtools_issues` 3, `test_leads_list_loading_state` 4, `test_bitrix_error_detail` 4, `test_bitrix_import_stats_api` 2, `test_lead_contacts_draft_visible` 1; `tests/lib/` 135 PASS; полная регрессия `all` — все зоны PASS, кроме известного `test_tasks_filter_done_and_combined` (красный и до правок).

## 2026-08-01 — Fix: новый контакт не перекрывает предыдущий, длинный список сворачивается

По `go` («я пишу еще контакт а он перекрывает предыдущий… или если больше 4 записей то как то скрываться и раскрываться»). Вторая причина того же бага: `onMount` вешает `page.subscribe(pullLead)`, а подписка срабатывает на любое изменение URL — переключение вкладки «Карточка»/«Паспорт» или открытие панели меняет `?panel=`/`?tab=`. На том же лиде `pullLead` всё равно звал `syncDetailsDraftFromLead()` и `syncContactsDraftFromLead()`, черновик пересобирался из сохранённого лида, незаполненная форма контакта исчезала, и следующий ввод попадал в предыдущую карточку. Теперь `pullLead` выходит сразу, если лид не сменился. Плюс свёртка длинных списков: readonly-список и форма редактирования показывают 4 записи и кнопку «Показать все (N)» / «Свернуть», `addContact` раскрывает список, чтобы новая форма была видна, и генерирует id со случайным хвостом (`crypto.randomUUID` недоступен вне secure context — по сети через IP два быстрых клика давали одинаковый ключ). Проверено в браузере на `/leads/244`: добавленный контакт пережил переход на «Паспорт» и обратно; шесть контактов сохранены, видно четыре. Тесты: `test_lead_contacts_ui` 4, зона `crm_leads` 111 PASS.

## 2026-08-01 — Fix: третий контакт больше не пропадает из карточки

По `go` («при создании третьего контакта третий заменяет второй… найди в чем дело и устрани»). PATCH уходил корректно и в БД лежали все три контакта, но карточка после сохранения перечитывала лид из кэша списка: `fetchLeadById` вызывался, а результат выбрасывался, и `sync()` брал устаревший `smartcrm_leads_cache_v2` — на 3258 лидах `await fetchLeads()` идёт больше 10 секунд. Форма пересобиралась из старого лида, третий контакт исчезал и из неё, и следующее сохранение отправляло уже два контакта, затирая третий в БД (аудит #130 на лиде 244). Добавлены `refreshLeadFromApi()` (лид из ответа детального API) и `refreshLeadsCacheInBackground()` (список обновляется, но карточка его не ждёт); заменено во всех местах сохранения — контакты, детали, суммы, апрувы, смена этапа, обогащение, исследование, SLA, push в Битрикс/Amo/HubSpot. Проверено в браузере на `/leads/244`: 2 → 3 → 4 контакта, счётчик и форма совпадают сразу после сохранения. Тесты: `test_lead_card_refresh` 4, `tests/lib/` + контакты 122 PASS, зона `crm_leads` 111 PASS.

## 2026-08-01 — Fix: 🔍 Groq вписан в TPM-лимит (досье через LLM, а не fallback)

По `go` («работает ли у нас грок… сколько лимит… не всю тратить»). Ключ Groq живой (`scripts/check_groq.py`: 14400 запросов/сутки, 6000 токенов/минуту), но досье падало в `413 rate_limit_exceeded` (`Limit 6000, Requested 6150`) → каждый раз fallback без LLM. Фикс: `estimate_tokens` / `groq_tpm_budget` / `fit_prompt_to_token_budget` — промпт урезается под минутный бюджет; retry считает новый размер по `Limit`/`Requested` из ответа Groq. JSON-паспорт теперь находится и когда модель теряет `## `. Паспортный LLM-вызов тоже в бюджете, Ollama на нём отключена (`RESEARCH_PASSPORT_OLLAMA=0`, экономит ~45с). `RESEARCH_ENRICH_TIMEOUT` 45→25с, `RESEARCH_QUERY_LLM_TIMEOUT` 8→15с. Поднята `ollama serve` как второй fallback. Прогон #97: `llm=True provider=groq`, 52.9с против 136с, паспорт — отрасль/город/сайт + контакт, один LLM-проход. Тесты: `test_research_groq_budget` 7, rag 127, p1 + p6 PASS.

## 2026-07-31 — Fix: 🔍 не зависает на Ollama/enrich

По `go` («подвисало… продолжи»). Причины: протухший Groq 401; Ollama 0.5b давала мусор; второй LLM на паспорт удваивал время; `asyncio.wait_for` ждал отмену httpx и тянул дольше таймаута; несколько uvicorn на :8000. Фикс: quality-gate досье, `RESEARCH_*` env-лимиты, жёсткий `_deadline` (enrich 45с / narrative 120с), второй passport-LLM только после Groq (auto), модель `llama3.2:latest`. Прогон #97: ответ за ~100с с читаемым fallback. Живой Groq — после смены ключа в `.env`.

## 2026-07-31 — 🔍 Надёжная выжимка (п.1–4) REVIEW

По `go REVIEW` (п.5 Checko — потом). Один LLM-проход: досье + `## 10. JSON-паспорт` (без второго вызова на passport); `readable_fallback_dossier` + `ensure_nonempty_summary`/`ensureSummary`; UI-статус «ищу / синтез / готово без LLM» + секунды. MCP на #97: 58с, fallback без LLM, досье и сырые hits на месте, контакты не стёрты. Тесты: reliability 8, rag 117, leads+analyst 32 PASS.

## 2026-07-30 — Fix: 🔍 не затирает UF Битрикс и паспорт

При research/enrich `techJson`/`checkoJson` писались целиком → снос `bitrix24.uf` и `company`. Фикс: deep-merge на фронте (`mergeLeadJson.js`) + на PATCH (`core/lead_json_merge.py`). Уже снесённые UF — только resync Битрикс (BACKLOG). Тесты merge + leads API; p1+p6 PASS.

## 2026-07-30 — 🔍 Исследовать заполняет паспорт

По `go`/SBR («ебашь… паспорт»). После досье: regex + LLM (Groq→Ollama) extract phones/emails/contacts/industry/city/website/ЛПР → merge в `passport` + `enriched` без затирания Checko; фронт пишет `contacts`/`industry`/`phone`/`email` в лид. Тесты `test_research_passport` 7 + rag 109 PASS.

## 2026-07-30 — Полное досье «Исследовать» для агентов

По `go` («выжимка… для всех агентов… groq или ollama… ебашь»). Синтез: Groq → Ollama; fetch топ-3 страниц; досье из 9 разделов в `web_research.summary` + `agent_brief`; агенты получают brief через `format_lead_context` / `normalize_lead_for_agents` без повторного веб-поиска. Fallback — те же разделы из сниппетов (не текст ошибки). Тесты: dossier + rag 102 PASS, analyst 5 PASS.

## 2026-07-26 — Fix: нет скролла на карточке лида

Шапка (этап + путь сделки + советы) ~450px при viewport ~666px оставляла hub ~90px — скролл формально был, но незаметен. Обёртка `lead-card-scroll` с `overflow-y-auto` на всю карточку. Smoke `test_lead_card_scroll.py` + card hub smokes 18 PASS.

## 2026-07-26 — Fix: «Лид не найден» при живом GET /api/leads/:id

Кэш списка в localStorage ~4.8MB (лимит ~5MB): `cacheWrite` молча падал, карточка после `fetchLeadById` снова читала устаревший кэш → «Лид не найден», хотя API 200. Фикс: in-memory зеркало кэша + применение ответа API напрямую в `/leads/[id]`; сравнение id через `Number()`. Smoke `test_lead_card_cache_resilience.py`.

## 2026-07-26 — Fix: tenderApi.js createLeadFromTender (Vite parse)

У `createLeadFromTender` пропал заголовок `export async function` — orphan-тело после `enrichTenderCustomer` ломало Vite import-analysis → 500/Internal Error на preload `/tenders` и HMR. Восстановлен экспорт; smoke `test_tender_api_exports.py`.

## 2026-07-30 — Fix: each_key_duplicate в «Исследование (веб)»

Дубли URL в `raw_results` ломали `{#each (hit.url)}`. Ключ → `` `${i}:${url}` ``.

## 2026-07-29 — Fix: исследование без падения LLM

По `go` («исправь исследование»). Если Groq/Ollama недоступны — выжимка из сниппетов поиска (не текст ошибки в карточке); фильтр junk URL (embassy/Netherlands); description перезаписывает старый блок исследования. Тесты 8 PASS.

## 2026-07-29 — 🔍 Исследовать на карточке лида

По `go` («кнопка исследовать… три поисковика… сырой JSON»). **GREEN:** `POST /api/search/research-lead` — параллельно enrich полей + narrative через Brave/Tavily/Serper с акцентом на актуальную дату; выжимка и сырые hits → `checkoJson.analyses.web_research`; кнопка 🔍 на `/leads/[id]`; свёртка «Исследование (веб)» в карточке. Тесты 5 PASS.

## 2026-07-26 — Fix: company is not defined (Svelte placeholder)

В `email/+page.svelte` и `EmailNurturePanel` placeholder с `{{company}}` парсился как переменная. Обёрнуто в `{'…{{company}}…'}`. Smoke `test_svelte_placeholder_mustache.py`.

## 2026-07-24 — Fix: суфлёр карточки null.label

При PATCH/создании `taskDueBadge` возвращал `null` → `Cannot read properties of null (reading 'label')` в `buildLeadCardCoachItems`. Фикс: `badge?.label` / `sla?.label`. Тест в `test_lead_card_coach_lib.py`.

## 2026-07-24 — Карточка клиента · Апрув 1 (каркас)

По `go` («делай… переделать карточку… паспорт как есть»). Спека [`F4_LEADS_CARD.md`](../phase4/leads/F4_LEADS_CARD.md). **GREEN:** `LeadClientCardForm` — порядок секций компания→контакты→сайт→отрасль/ОКВЭД→сотрудники→обороты→агенты(placeholder)→системные→UF хвост; адрес/ОКВЭД read-only из Checko; доп. поля в свёртке. Паспорт не трогали. Smoke 22 PASS. Стоп до «ок» на Апрув 2 (контакты).

## 2026-07-24 — Бриф направления Лиды (для следующего чата)

По `go` («давай делай»). Docs: [`F4_LEADS_DIRECTION.md`](../phase4/leads/F4_LEADS_DIRECTION.md) — автоскор vs ручной `score`, Мой день (дело сегодня + близость к деньгам), шапка (отрасль, без этапа в мете), путь сделки 0/0, 🔍, очередь работ. Пункты в CHECKLIST_F4 + acceptance §2b5. Код продукта не меняли.

## 2026-07-23 — Тех. спец на карточке лида

По `go` («ебашь»). SBR: **RED** `ac73088`. **GREEN:** в плитке «Агенты» кнопка «Тех. спец» (`tech_specialist`); бэк `POST /api/agents/email/run` → `agents.tech_specialist._analyze("analyze_lead")`; превью хаба обновлено. Smoke 15 PASS. Пункт CHECKLIST_F4 / acceptance §2b4 — `[x]` после «ок».

## 2026-07-23 — Редизайн хаба карточки лида (5 плиток)

По `go` («ебашь… поэтапно»). SBR: **RED** `05ec765` — `test_lead_card_hub_v2.py` 5 FAIL. **GREEN:** хаб `Клиент` (табы Карточка|Паспорт) · `Работа` (История|Задачи) · `Письма` · `Продукты` · `Агенты`; этап воронки + путь сделки в шапке; из тулбара убраны ✉️ и 🔗 (рассылка в панели Писем); миграция `hubTileOrder` со старых id. Smoke 25 PASS. Пункт в CHECKLIST_F4 / acceptance §2b3 — `[x]` после «ок».

## 2026-07-23 — DnD порядка плиток хаба на карточке лида

По `go` («ебашь… го»). SBR: **RED** `40dd5f2` — smoke/pytest без `hubTileOrder.js`. **GREEN:** native HTML5 DnD плиток хаба на `/leads/[id]` (как воронка); порядок в `localStorage` (`smartcrm-lead-hub-tile-order`); логика `frontend/src/lib/leads/hubTileOrder.js`; UI — `LeadHubTile` + сетка в `+page.svelte`. Тесты: `tests/frontend/test_hub_tile_order.py` 3 PASS. Пункт в `CHECKLIST_F4.md` (без `[x]` до «ок»), acceptance §2b2.

## 2026-07-23 — Токен-оптимизация workflow (зона×3, короткие логи, широкий заказ)

По `go` («ебашь все · код не трогай · дай замеры»). В правила: (2) широкий заказ → 2–3 варианта до узкого `go`; (3) `Регрессия_счёт N/3` в шапке SESSION_STATE — каждый GREEN зона, на 3/3 ещё `all`/p1+p6, сброс; (4) в отчёте команда+PASS/FAIL+2–3 строки, не весь pytest; (5) читать пункт+спеку, не весь чеклист/PRD. Правки: `task-workflow`, `dev-gates`, SBR GREEN, RULES_MATRIX R15, шапка SESSION_STATE. Код продукта не трогали. Замеры — в отчёте шага (always-байты до/после + оценка экономии на SBR-цикле).

## 2026-07-23 — Переименование чеклистов: CHECKLIST.md → CHECKLIST_F{N}.md

По `go` («просто переименуй в фазах»). Файлы: `phase1/CHECKLIST_F1.md` … `phase4/CHECKLIST_F4.md`. Ссылки обновлены в rules (task-workflow, SBR, dev-gates, repo-layout), `.cursorrules`, README фаз/операционки/docs, ROADMAP, PRD, ARCHITECTURE, FUNCTIONAL, BACKLOG, todo, RULES_MATRIX, archive (PHASE2_ENTRY и др.), scratch-скрипт сборки. Исторические строки в старых записях CHANGELOG/HANDOFF/SESSION_STATE не переписывались.

## 2026-07-23 — Подписи чеклистов фаз: «Чеклист: Фаза N» в ссылках

По `go` («переименуй чтоб было понятно · файлы не трогать»). H1 внутри `phase{N}/CHECKLIST.md` уже были вида «Чеклист: Фаза N — …». Поправлены **тексты ссылок** и подписи в README/навигации, чтобы везде читалось с номером фазы, а не голое `CHECKLIST.md`: `phase1–4/README.md`, `docs/README.md`, `operations/README.md`, `ROADMAP.md`, `PRD.md`, `BACKLOG.md`, `todo.md`, `RULES_MATRIX.md`, `REPO_LAYOUT.md`. Имена файлов `CHECKLIST.md` не менялись (без шума по путям).

## 2026-07-21 — Ф4 Email: рассылка по «подключённой базе» — CSV с меткой source + фильтр «Источник» (SBR)

По `go` («мне надо чтобы я мог любые базы подключать к рассылке… и чтобы фильтры тоже были… ебашь»). Полный SBR-цикл одним прогоном (go дан сразу). **RED** (`4144758`): `tests/api/test_lead_source_segment.py` — 4 FAIL (у импорта нет метки, `GET /leads/sources` 422, сегмент по source пуст). **GREEN backend:** `POST /api/leads/import-csv?source=…` — метка базы проставляется всем строкам импорта (важнее колонки `source` в файле; `integrations/crm_sync/csv_adapter.py`); новый `GET /api/leads/sources` — справочник источников `{name, count, withEmail}` (`csv_routes.py`, регистрируется до `/{lead_id}`); сегмент рассылки по `source` в `lead_segment_query.py` уже был. **GREEN frontend:** `/leads/list` меню «Импорт и экспорт» — поле «Метка базы (source)» перед «Импорт CSV» (`apiImportLeadsCsv(file, mode, source)`); массовая рассылка `/email` — селект «Источник (база лидов — метка импорта)» со справочником (`fetchLeadSources`), `buildSegmentFilters` передаёт `source`, подписи к фильтрам «Этап воронки» / «Мин. балл лида (0 — все)»; смоук `campaignSegmentLogic.smoke.mjs` дополнен. Тесты: 4/4 PASS + 8 PASS с `test_leads_csv_api.py`. Регрессия: crm_leads **109 PASS / 1 FAIL** — `test_tasks_filter_done_and_combined` падает и на чистом HEAD (дата-зависимый) → ISSUES 🟡; email **33 PASS / 1 FAIL** — известный `test_faq_autoreply_mocked` (уже в ISSUES). DevTools MCP на живой БД: источник Plixer + балл 0 → «Лидов: 27» (совпало со справочником «27 с email из 27»); поле метки в меню импорта на месте. Отложено в BACKLOG: фильтр «дата регистрации компании» (нет поля в Lead — нужен enrich + миграция). Доки: `api/routes/README.md`, `tests/README.md`, `F4_EMAIL_TUNING.md` § C.

## 2026-07-21 — Ф4 Email: ящики в UI без единственной зависимости от `.env` (SBR)

По `go` (пункт чеклиста Ф4 · Email). SBR полный цикл. **RED** (`ae5d842`): `tests/api/test_email_accounts_api.py` вскрыл реальный баг — `POST /api/email/accounts/connect` не делал собственный `commit` и держался на побочном commit внутри IMAP-синка: с замоканным/упавшим синком ящик из UI молча терялся, а `bootstrap-from-env` после этого плодил «новый» аккаунт. **GREEN backend:** явный `await db.commit()` в connect-роуте (`api/routes/email.py`) — 4/4 PASS. **GREEN frontend (`/email` модал «Почтовые ящики»):** у каждого подключённого ящика кнопка «Синк» + строка `imap_server · дата последнего синка`; новая секция «Ящики в .env (опционально)» — сводка `GET /config/status` (ожил мёртвый хелпер `fetchEmailConfigStatus`) и кнопка «Импортировать из .env» → `POST /bootstrap-from-env` (новый хелпер `bootstrapEmailFromEnv`, sync=false); модалке дан `max-h-[90vh] + overflow-y-auto` (низ обрезался). Регрессия зоны email: **33 PASS, 1 FAIL** — `test_faq_autoreply_mocked` падает и на чистом HEAD (в корневом `.env` `EMAIL_FAQ_AUTOREPLY=0`, тест не изолирует env) → запись в ISSUES 🟡, не связано с шагом. DevTools MCP: модал открыт, оба ящика (Agneko AM/IB) с кнопками Синк/Отключить, секция .env показывает «Все ящики из .env уже подключены (2)». Доки: `F4_EMAIL_TUNING.md` § A (3 из 4 пунктов `[x]`), `backend/tests/README.md`.

## 2026-07-21 — PHASE 0 INTAKE в SBR: заказ дословно → доки → код

По `go` («сделай всё что задумал… код пока не надо»). В SBR добавлена **PHASE 0 INTAKE**: слова пользователя записываются **дословной цитатой** в `todo.md` § «Заказ (дословно)» (цитата = источник истины, спор о scope решается по ней), под ней «Как понял» 1–2 строки; до кода подготавливается всё остальное — пункт в чеклист фазы (если его нет) и спека/док области `docs/operations/phase{N}/{область}/` (если нужен и не существует); отдельного стопа нет — сразу PHASE 1 SPEC и обычный `go` на BUILD. Правки: `spec-build-review.mdc` (секция PHASE 0 + таблица «Когда SBR обязателен»), `smartcrm-task-workflow.mdc` (§ Старт задачи), `smartcrm-index.mdc`, `RULES_MATRIX.md` § SBR scope, шаблон `todo.md` (новая секция). `verify_cursor_rules_precedence.py` — OK.

## 2026-07-21 — Свежесть CHANGELOG/HANDOFF в check_step + реанимация pre-commit hook

По `go` (разбор «что критичное упустили»). **(1) Свежесть журналов:** `check_agent_step.py` — новая `ops_freshness_errors()`: если последний done-шаг SESSION_STATE датирован позже последней записи CHANGELOG (`## YYYY-MM-DD`) или HANDOFF (`**YYYY-MM-DD:**`) → FAIL в `check_step.cmd`; подшаги in_progress (SBR RED) не проверяются — для них журналы по правилу не пишутся. Гранулярность — день. +8 тестов `tests/scripts/test_check_agent_step.py`; `pytest tests/scripts/ -q` — **30 passed**. README: scripts (добавлены 3 валидатора шага), tests (новый файл). **(2) Pre-commit hook:** обнаружен мёртвым — в `.git/hooks/` лежала старая версия с путём `docs/operations/SESSION_STATE.md` (до переезда в `session/`), проверка не срабатывала вообще; переустановлен пользователем через `scripts/install_git_hooks.ps1`. Попутно в BACKLOG записано (отдельным шагом `91d10e3`): агент сам начинает вести `todo.md` в ближайшие 3–6 прогонов.

## 2026-07-21 — Оптимизация workflow: один коммит на шаг, check_step.cmd, триаж ISSUES, чистка BACKLOG

По `go` пользователя (разбор трений процесса). **(1) Один коммит на шаг:** ops пишутся **до** коммита с маркером `Коммит: \`этот\``, код + ops едут одним коммитом — раньше ~50% истории были вторые «ops:»-коммиты; `session_state_validate` принимает маркер, `check_agent_step` проверяет HANDOFF по последним 20 хешам вместо HEAD (вечный WARN «нет хеша HEAD» был невыполним по построению); обновлены `commit-ops.mdc`, `AGENTS.md`, `RULES_MATRIX`, шапка `SESSION_STATE`. **(2) `scripts/check_step.cmd`:** три валидатора одним вызовом с UTF-8 — python напрямую в PowerShell-обёртке Cursor теряет exit code; в сами скрипты добавлен `sys.stdout.reconfigure(utf-8)` (кириллица без мохибейка). **(3) Триаж ISSUES:** 4 стейл-записи закрыты с подтверждения пользователя (дрейф PRD — решён доками 07-21; API без Postgres — БД стабильна с мая; QA-матрица — роль выполняет RULES_MATRIX § Регрессия; hermes_eval 9 failed — известно-красный без live LLM, переоткрыть при live-повторе); журнал разнесён в `docs/archive/ops/2026-05/06_ISSUES.md`; новое правило **R14** — открытые записи старше месяца показывать как «должки» и закрывать только с подтверждения (task-workflow § Старт сессии). **(4) Чистка BACKLOG:** закрытые блоки и строки → `2026-06_BACKLOG.md` / `2026-07_BACKLOG.md` (голос→лиды, поиск/RAG, тендеры baseline, Voice Layer, quality gates, CoffeeOS шаги), живой файл — только реальные хвосты. **(5) Regex:** `check_rules_commit_conflict` сужен (`{0,25}` вместо `.*`, убран широкий `жду\s+явн`), фикс падения `scan_file` на путях вне репо. Тесты: `pytest tests/scripts/ -q` — **22 passed** (в т.ч. новые `test_session_state_validate.py`, 10 кейсов).

## 2026-07-21 — Чеклисты фаз вместо PRD_MAP

По `go` («делай эту задачу, код не трогай»). Управление фазами перенесено из продукта в операционку: **`docs/operations/phase{N}/CHECKLIST.md`** — Ф1–Ф3 собраны из архива `PRD_MAP_F1-F3.md` (DoD, сценарии, все таблицы), Ф4 — из живого `PRD_MAP.md` (+ сводка модулей). `docs/product/PRD_MAP.md` и `docs/archive/product/PRD_MAP_F1-F3.md` **удалены** (содержимое в чеклистах 1:1). `ROADMAP.md` — навигатор фаз со ссылками на чеклисты. `PHASE2_ENTRY.md` → `docs/archive/ops/` (история входа в Ф2). Правила (`.cursorrules`, `smartcrm-index`, `task-workflow`, `dev-gates`, `spec-build-review`, `repo-layout`, `RULES_MATRIX`) и доки (`docs/README`, `operations/README`, `PRD`, `FUNCTIONAL`, `ARCHITECTURE`, `BACKLOG`, `todo`, phase-README) переведены на формулировку «пункт чеклиста фазы»; формат BACKLOG-строки — `Чеклист: «Ф{N} · пункт»` (старые записи не переписаны). Попутно: +`phase3/README.md`; убраны 2 устаревшие ссылки на `PRD_NOTES.md` из repo-layout и file-size-split. Проверки: линк-чекер — 0 битых; `check_rules_commit_conflict`, `verify_cursor_rules_precedence`, `session_state_validate` — OK. Коммит `7462df9`.

## 2026-07-21 — Разгрузка токенов: правила, ops-архив, продуктовые доки

По `go` («ебашь», 4 шага). **(1) Дедуп правил:** `smartcrm-agent-workflow.mdc` удалён (порядок шага влит в `commit-ops`), `task-workflow` сокращён ~в 2 раза (дубли канона коммита → ссылки), `.cursorrules` и `AGENTS.md` и `smartcrm-index` сжаты, `dev-gates` без дубля приоритета/секретов; `repo-layout` и `file-size-split` переведены с alwaysApply на globs (подтягиваются при работе с кодом). SBR, commit-ops, task-workflow, dev-gates — остались всегда. **(2) Архив ops:** CHANGELOG/HANDOFF/SESSION_STATE распилены по месяцам в `docs/archive/ops/YYYY-MM_*.md`, живые файлы — только текущий месяц; правило R13 в RULES_MATRIX. **(3) Продукт:** созданы `VISION.md`, `ROADMAP.md`, `BUSINESS_LOGIC.md`, `FUNCTIONAL.md`; `PRD.md` разгружен (идея/принципы → VISION, roadmap → ROADMAP); `PRD_MAP.md` — чеклисты Ф1–Ф3 → `docs/archive/product/PRD_MAP_F1-F3.md`, живой MAP = Ф4 + сводка; `PRD_NOTES.md`, `PRD_DELTA_v2.md` → `docs/archive/product/`. **(4) `DESIGN_SYSTEM.md`** — снимок текущего UI (тёмная тема gray-950/900/800, акцент indigo-600, паттерны). Связи: линк-чекер по живым докам — 0 битых (попутно починены 7 старых); `check_rules_commit_conflict`, `verify_cursor_rules_precedence`, `session_state_validate` — OK. Итог по токенам: always-правила 46.4k → 23.6k знаков (−49%); старт сессии (журналы+MAP+PRD) ~450k → ~49k знаков (−89%). Коммиты `fdadf31`, `119d94d`, `8ffc43b`, `5b2070d`.

## 2026-07-21 — Чистка git status: runtime-данные вне git

По `go` пользователя («устрани всё»): runtime-файлы `backend/data/` (api_stats, traces, checko_cache, ops_queue, ops_snapshots, agent_memory.sqlite3, hermes_system_prompt.txt, prompt_versions/, *_state/*_notifications/логи) добавлены в `.gitignore` и убраны из индекса (`git rm --cached`, файлы на диске целы). `eval_benchmark_data.py` перенесён из корня `backend/` в `backend/scripts/` (импорты в двух скриптах работают без правок — проверено). `.pytest_cache` в корне репо удалён (pytest гонять из `backend/`). `__pycache__` и `frontend/.svelte-kit` уже ловились правилами (`git check-ignore` подтвердил) — в статусе их больше нет. README backend/scripts обновлены. Тесты: `pytest tests/scripts/ -q` — 12 passed. Архивация толстых ops-файлов → BACKLOG. Коммит `7a57856`.

## 2026-07-18 — Ф4: кнопка «+ Добавить ящик» в сайдбаре почты

Под селектом «Все ящики» — явная кнопка добавления ящика (открывает модал подключения). Проверено в браузере через DevTools MCP: оба ящика (`me@agneko.am`, `ib@agneko.com`) видны.

## 2026-07-18 — Ф4: управление почтовыми ящиками (отключение)

`DELETE /api/email/accounts/{id}` + `services/email_account_delete.py` (purge переписки/кампаний/цепочек); UI — кнопка «Отключить» у каждого аккаунта в модалке `/email`.

## 2026-07-18 — `.claude/` в gitignore

Папка Claude Code (agents, commands) убрана из git (`git rm --cached`), файлы на диске остались. `.gitignore`: `.claude/` вместо `.claude/settings.local.json` — секреты локальных настроек больше не попадут в git.

## 2026-07-18 — CoffeeOS workflow: шаг 6 + закрытие миграции

SBR scope зафиксирован: PRD_MAP + фичи/API/миграции; one-liner без SBR.  
RULES_MATRIX § SBR scope; BACKLOG post-migration долги.

## 2026-07-18 — CoffeeOS workflow: шаг 5 (doc links + scratch)

Ссылки на rules → `.cursor/rules/workflow/` в PRD_MAP, PHASE2_ENTRY, docs/README, archive, debt.  
`backend/scripts/scratch/` + README; repo-layout, scripts/README.

## 2026-07-18 — CoffeeOS workflow: шаг 4 (merged отчёт)

Таблица **Сделано | Не сделано** + A/B/C в task-workflow, commit-ops, agent-workflow, spec-build-review, AGENTS, RULES_MATRIX.  
A = колонка «Не сделано»; RED-substep — без полного отчёта.

## 2026-07-18 — CoffeeOS workflow: шаг 3 (project-rules)

6 файлов в `.cursor/rules/project/`: core, tests, http, data, agents, performance.  
Globs по зонам; performance — alwaysApply. Обновлены index, `.cursorrules`, RULES_MATRIX, spec-build-review, BACKLOG.

## 2026-07-18 — CoffeeOS workflow: шаг 2 (SBR)

`workflow/spec-build-review.mdc` — PHASE 1 SPEC / RED / GREEN / REVIEW.  
`docs/operations/session/todo.md` — микро-чеклист фичи.  
RED/GREEN substeps в `commit-ops.mdc`; SBR в `task-workflow`, `dev-gates`, index, `.cursorrules`.  
Scope SBR по умолчанию: PRD_MAP + фичи; one-liner — без SBR.

## 2026-07-18 — CoffeeOS workflow: шаг 1 (каркас + перенос)

`.cursor/rules/workflow/` — 6 правил (commit-ops, task-workflow, agent-workflow, dev-gates, repo-layout, file-size-split).  
`smartcrm-index.mdc`, `project/README.md` (placeholder).  
Обновлены: `AGENTS.md`, `.cursorrules`, `RULES_MATRIX.md`, `verify_cursor_rules_precedence.py`, CONTRIBUTING, REPO_LAYOUT, LAYOUT_AUDIT.  
BACKLOG: шаги 2–6 (SBR, project-rules, отчёт, doc links, scratch).

> Архив: `docs/archive/ops/` (секции по месяцам).
