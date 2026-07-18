# BACKLOG — отложенная работа (хвост)

> **Баги и поломки** → [`ISSUES.md`](ISSUES.md).  
> Здесь только «сделать позже»: техдолг, не вошло в текущий шаг, scope отложен по решению.

**Связь с продуктом:** каждая запись **обязательно** привязана к **пункту [`PRD_MAP.md`](../product/PRD_MAP.md)**.

---

## Легенда приоритетов

| Метка | Смысл |
|-------|--------|
| 🔴 | Блокирует закрытие пункта MAP или следующий шаг по нему |
| 🟡 | Важно, можно идти дальше по MAP |
| 🟢 | Улучшение, не блокер |

---

## 👤 Ручная работа (только ты) — не забыть

> Агент закрыл автомат и код. Ниже — что **нельзя** закрыть без тебя: микрофон, живой браузер, ключи, туннель.

| Приоритет | Фаза MAP | Блок PRD_MAP | Пункт блока | Что сделать руками | Как проверить / док |
|-----------|----------|--------------|-------------|-------------------|---------------------|
| ✅ закрыто | **Фаза 1** | **Голос → лиды** | **п.1** Whisper STT | E2E audio WS + dev `voice-simulate-mic` — `smoke_voice_mic_e2e.py`, `VOICE_MIC_E2E_ACCEPTANCE.md` (2026-06-11) |
| 🟡 желательно | **Фаза 1** | **Голос → лиды** | **п.3** voice_action | Spot-check: **удаление лида** — модалка approve → «Подтвердить» → лид исчез из списка (S04) | `VOICE_LEAD_SCENARIOS_ACCEPTANCE.md` S04; кнопки `data-testid=voice-approve-confirm` |
| 🟡 желательно | **Фаза 1** | **Голос → лиды** | **п.5** смоук | Spot-check: **fanout** — фраза «проанализируй лид …» / «создай лид …» — индикатор «Агенты анализируют…», модалка/ответ 15–30 с (S02, S06) | Голосовая панель в layout; live Groq |
| 🟢 опционально | **Фаза 1** | **Голос → лиды** | **п.2** Hermes live | Прогон **live LLM** (не CPU rescue): `GROQ_API_KEY=… python scripts/smoke_hermes_leads_live.py` | Артефакт `backend/data/artifacts/voice/hermes_leads_live.json` |
| 🟢 опционально | **Фаза 1** | **Голос → лиды** | **п.1** health | `curl "http://127.0.0.1:8000/health/whisper?ping=1"` — reachable с твоим ключом | `VOICE_LEADS_TAIL_ACCEPTANCE.md` |
| 🟡 отложено | **Фаза 2** / DevOps | **Лиды** | **п.2** Битрикс синк | Туннель **:8000** (ngrok/cloudflared) + исходящий вебхук в портале Битрикс | Инструкция: [`docs/start/BITRIX_OUTBOUND_WEBHOOK.md`](../../start/BITRIX_OUTBOUND_WEBHOOK.md); сейчас импорт + опрос 5 мин |

**Критерий «Фаза 1 / Голос → лиды закрыт»:** ✅ mic E2E (WS bytes + dev sim). Опц. spot-check 🟡 ниже.

**Снять ⚠️ в MAP (после ручного прогона):**

1. `SESSION_STATE.md` — строка «микрофон E2E OK / дата».
2. `PRD_MAP.md` — «Голос → лиды» п.1: колонка **Статус** → ✅, убрать ⚠️ из **Итог**; сводка «Голос лиды» → ✅.
3. Здесь — отметить 🔴 выполненным или перенести в § Записи.
4. `PRD_MAP.md` DoD Ф1 п.5 → ✅ (E2E); при полном закрытии голоса — п.6 «ок в Ф2» отдельно по решению владельца.

---

## Записи

[2026-06-22] | PRD_MAP: «Карточка — enrich, паспорт» | Отложено: разделы паспорта «Вакансии», «Налоги и сборы», «История изменений» | Причина: Checko API не подключены в enrich (нет fetch в endpoints) | Нужна фаза MAP: 4 | Из шага: enrich→полный checko_json

### Фаза 4 — авто-суфлёр Стратега (тюнинг, не блокер Ф3)

Чеклист: [`F4_STRATEGIST_SUGGESTER_TUNING.md`](../phase4/agents/F4_STRATEGIST_SUGGESTER_TUNING.md)

| Приоритет | Пункт | Отложено |
|-----------|-------|----------|
| 🔴 | Runtime → override промптов | Apply в Ops не меняет ответы агентов |
| 🟡 | 👎 с ожидаемым ответом | Мало контекста для суфлёра |
| 🟡 | Apply → gate / A/B | Регрессия вслепую |
| 🟡 | Больше сигналов / агрегация | Пустой отчёт без массы 👎 |
| 🟢 | История суфлёра | Нет «было / стало» |
| 🟢 | Периодический запуск | Только ручная кнопка |
| 🟢 | Hermes: suggest→A/B→apply | Разрозненные страницы |
| 🟢 | Суфлёр по одному агенту | Сейчас общий прогон |

`[2026-06-17] | PRD_MAP: Ф4 · суфлёр Стратега тюнинг | Отложено: 8 пунктов выше | Причина: Ф4 polish до MVP, после апрува Ф3 суфлёр | Нужна фаза MAP: 4 | Из шага: обсуждение улучшений`

### Фаза 4 — A/B промптов по трейсам (тюнинг, не блокер Ф3)

Чеклист: [`F4_PROMPT_AB_TUNING.md`](../phase4/agents/F4_PROMPT_AB_TUNING.md)

| Приоритет | Пункт | Отложено |
|-----------|-------|----------|
| 🟡 | Эталон intent при 👎 | Без него accuracy в A/B почти пустая |
| 🟡 | Больше кейсов + good-регрессия | n<30, нет защиты от поломки рабочих фраз |
| 🟡 | Модель groq/hermes3 в UI | Сейчас только hermes3 в кнопке |
| 🟡 | A/B промптов агентов | Только Hermes на improve |
| 🟢 | Suggest → сразу A/B | Лишний ручной шаг |
| 🟢 | История отчётов A/B | Нет сравнения версий во времени |
| 🟢 | Dr. QA в UI | Сейчас CLI/скрипты |

`[2026-06-17] | PRD_MAP: Ф4 · A/B промптов тюнинг | Отложено: 7 пунктов выше | Причина: Ф4 polish до MVP, после базового Ф3 A/B | Нужна фаза MAP: 4 | Из шага: обсуждение улучшений Ops UI`

### Фаза 4 — vendor crawl → tech_specialist (тюнинг, не блокер Ф3)

Чеклист: [`F4_VENDOR_CRAWL_TUNING.md`](../phase4/rag/F4_VENDOR_CRAWL_TUNING.md)

| Приоритет | Пункт | Отложено |
|-----------|-------|----------|
| 🟡 | Автокраул `auto_crawl_enabled` | База устаревает без ручного запуска |
| 🟡 | Глубже `doc_urls` (KB, datasheet, release notes) | Сейчас в основном лендинги |
| 🟡 | Метаданные чанков (продукт, тип дока) | Точнее retrieval |
| 🟡 | Eval retrieval 10–20 вопросов tech_specialist | Дыры не видны без метрик |

`[2026-06-17] | PRD_MAP: Ф4 · vendor crawl тюнинг | Отложено: 4 пункта выше | Причина: Ф4 тюнинг до MVP, после «ок» Ф3 crawl | Нужна фаза MAP: 4 | Из шага: обсуждение улучшений tech_specialist`

`[2026-06-17] | PRD_MAP: Ф3 Self-improvement · vendor crawl UI + cron | **✅ сделано** — `/ops/vendor-crawl` + `vendor_crawl_background.py` | Коммит: см. CHANGELOG`

`[2026-06-15] | PRD_MAP: Ф3 Email · этап B массовый сегмент | **✅ сделано** — `EmailCampaignPanel`, preview-llm, send_now | Коммит: см. CHANGELOG`

`[2026-06-15] | PRD_MAP: Ф3 Email · этап B массовый сегмент | ~~Отложено~~ → закрыто в коммите этапа B`

`[2026-06-16] | PRD_MAP: Ф3 Email · лимит писем/день | Отложено: счётчик отправок/день, warn/block перед send_now | Причина: после этапа C | Нужна фаза MAP: 3 | Из шага: этап C`

`[2026-06-15] | PRD_MAP: Ф3 Email · лимит писем/день | Отложено: антиспам лимит nurture+campaigns | Причина: после этапа B | BACKLOG`

`[2026-06-15] | PRD_MAP: Ф3 Email · LLM nurture под продукт | **ПИЛОТ ✅ 3 письма** MaxPatrol VM; расширение до 20 — после апрув | `docs/modules/email_nurture.md` | Из шага: start-llm live`

`[2026-06-15] | PRD_MAP: Ф3 Email · 20 касаний | Отложено: LLM-генерация текстов nurture (Маркетолог) вместо детерминированных шаблонов | Причина: ждём апрув пользователя на текущий nurture (шаблоны + персонализация OK) | Нужна фаза MAP: 3 | Из шага: nurture хвост A закрыт`

`[2026-06-13] | PRD_MAP: переход Ф1→Ф2 | DoD Ф1 6/6; хвосты L306–318 не блокируют; PHASE2_ENTRY.md | **Push:** ждём go | **Ф2 код:** ждём go + номер очереди | gate live — параллельно`

`[2026-06-14] | PRD_MAP: «§4 факты диалога» | **ЗАКРЫТО ✅** | `RAG_DIALOGUE_LLM=0/1` + `collect_deal_facts`; pytest | Коммит: см. CHANGELOG RAG tail`

`[2026-06-14] | PRD_MAP: «§4 Авто-чанки» | **ЗАКРЫТО ✅** | `RAG_AUTO_STRUCTURE_LLM=0/1` + `qa_structure.py`; pytest | Коммит: см. CHANGELOG RAG tail`

`[2026-06-14] | PRD_MAP: «Quality gates Ф3 тюнинг» | Отложено: довести всех агентов ≥85%; baseline `AGENTS_GATE_TUNING_BASELINE.md` | Причина: **Ф3**, не блокер Ф2; нужен live Ollama/Groq + go | Нужна фаза MAP: **3** | Действие: Hermes/Tech/Economist промпты → re-gate` | Коммит 7be7bdb: tuning import failed, delta was→became % | **Не вышло:** live gate MAP 🔲 | Действие: EVAL_OLLAMA_TIMEOUT=1200`

`[2026-06-13] | PRD_MAP: Агенты quality gates UI финал | Коммит 596d2e1: вкладки Hermes/gate, download, режимы, bulk→eval-failed-gate, insights pass rate | **Не вышло:** live gate MAP 🔲; agents-only оборван analyst | Действие: EVAL_OLLAMA_TIMEOUT=1200 --write-acceptance`


`[2026-06-11] | PRD_MAP: инфра email me@agneko.am | **ЗАКРЫТО ✅ 2026-06-14** | Пароль в `.env`; ib@ + me@ через `EMAIL_ACCOUNT_*` | Коммит: см. CHANGELOG cleanup`

`[2026-06-11] | PRD_MAP: «Ops /ops» п.10 версионирование промптов | **ЗАКРЫТО ✅ 2026-06-14** | `agent_prompt_versions.py` + API + UI `/ops/agents` | `OPS_PROMPT_VERSIONING_ACCEPTANCE.md`

`[2026-06-11] | PRD_MAP: «Аналитика (базовая)» п.7 голос | Отложено: голосовые запросы к воронке/KPI | Причина: scope Ф2 (`PRD_MAP` п.188) | Сейчас: UI+API baseline на `/leads/analytics` | Действие: Voice Layer + intent «покажи воронку»`

`[2026-06-08] | PRD_MAP: п.2 «Поля Битрикс + синк» | Отложено: туннель (ngrok/cloudflared) + исходящий вебхук в портале | Причина: dev на localhost — Битрикс не достучится; мгновенный синк не проверить без публичного URL | Нужна фаза MAP: 2 / DevOps | Сейчас работает: полный импорт (кнопка) + опрос BITRIX_AUTO_SYNC_MINUTES=5 | Действие: туннель :8000 → URL в Битриксе ONCRMLEADADD → /api/webhooks/bitrix/events?token=...; опционально :5173 для UI`

`[2026-06-08] | PRD_MAP: «Голос → лиды» п.2 Hermes — ЗАКРЫТО ✅ | Scope: CRUD, стадия, задача (`create_lead`, `update_lead`, `delete_lead`, `list_leads`, `create_task`) | Сделано: `slot_normalize`, rescue/fastpath, `smoke_hermes_leads.py` 40 passed, `HERMES_LEADS_ACCEPTANCE.md` | Коммит: `be70615` | Хвост п.2 (не блокер): 3 LLM eval Groq — см. таблицу ниже 🟢`

`[2026-06-08] | PRD_MAP: стек / Email API | ЗАКРЫТО ✅ | `@field_validator` в `email.py` | Коммит: см. CHANGELOG 2026-06-08 хвост голос`

---

## Блок «Голос → лиды» — статус PRD_MAP п.1–5 (2026-06-08)

| # | Пункт | Статус | Acceptance |
|---|--------|--------|------------|
| 1 | Whisper STT | ✅ | `WHISPER_STT_ACCEPTANCE.md` |
| 2 | Hermes CRUD/стадия/задача | ✅ | `HERMES_LEADS_ACCEPTANCE.md` |
| 3 | voice_action UI | ✅ | `VOICE_ACTION_ACCEPTANCE.md` |
| 4 | Полные интенты | ✅ | `HERMES_LEADS_FULL_ACCEPTANCE.md` |
| 5 | Смоук сценариев | ✅ автомат | `VOICE_LEAD_SCENARIOS_ACCEPTANCE.md` |

**Команда полного прогона:** `cd backend && python scripts/smoke_voice_lead_scenarios.py`

### Сводный хвост блока «Голос → лиды»

| Приоритет | Источник | Что | Статус |
|-----------|----------|-----|--------|
| 🔴 | п.1 | E2E микрофон | 👤 **см. § «Ручная работа»** |
| 🟡 | п.3, п.5 | Spot-check approve + fanout | 👤 **см. § «Ручная работа»** |
| ✅ | хвост #2–#11 | код + pytest | `VOICE_LEADS_TAIL_ACCEPTANCE.md` |
| 🟢 | Ф2 | LiveKit вместо WS | см. инфра ниже |

---

## Блок «Поиск и RAG» — хвост на потом (п.1–5 закрыты ✅)

| Приоритет | PRD_MAP | Что | Фаза MAP | Кто |
|-----------|---------|-----|----------|-----|
| ✅ | enrich-lead | Смоук `enrich-lead` live E2E | **1** | `SEARCH_ENRICH_LEAD_ACCEPTANCE.md` |
| 🟢 | prospect/agent | Spot-check live Groq в UI (prospect, enrich, agent) | **1** | 👤 опционально |
| ✅ | Ф2 §4 | Кэш результата enrich (company+ИНН+industry, TTL ~24 ч) | **2** | `SEARCH_ENRICH_CACHE_ACCEPTANCE.md` |
| ✅ | Ф2 §9 | Кнопка «Обогатить» на `/leads/{id}` | **2** | `LEADS_CARD_ENRICH_ACCEPTANCE.md` |
| ✅ | RAG tail | LLM flags + page_fetch + smoke cache | **2** | `RAG_BACKLOG_TAIL_CLOSED.md` |
| ✅ | Ф2 §4 | Авто-чанки «поиск → RAG» | **2** | `SEARCH_RAG_AUTO_CHUNKS_ACCEPTANCE.md` |

**Ф1 enrich** — `phase1/search/SEARCH_ENRICH_LEAD_ACCEPTANCE.md` ✅. **п.1–5 RAG** — `docs/operations/phase1/search/`.

---

## Блок «Тендеры» — закрыто baseline (2026-06-11)

П.2–5, п.7 — код + pytest. Осталось опционально:

| Приоритет | PRD_MAP | Что | Фаза |
|-----------|---------|-----|------|
| 🟢 | Тендеры | Live spot-check поиска с `SERPER_API_KEY` / `TAVILY_API_KEY` | **1** |
| 🔲 | Тендеры | Контур.Закупки API — **Ф4** после 1-й сделки · `F4_KONTUR_GATE.md` | **4** |

---

## Фаза 4 — «Мой день» (лиды)

| Шаг | PRD_MAP | Статус | Док |
|-----|---------|--------|-----|
| Спека | «Мой день» | ✅ 2026-06-27 | [`F4_DAY_PRIORITY.md`](../phase4/leads/F4_DAY_PRIORITY.md) |
| 1–7 код | те же пункты MAP | ✅ код 2026-06-27; 👤 приёмка §11 | §10 плана в спеке |

`[2026-06-27] | PRD_MAP: «Мой день (приоритет очереди)» | Отложено: имплементация lead_day_priority + UI | Причина: сначала спека и согласование с оператором | Нужна фаза MAP: 4 | Из шага: docs prep`

---

## Фаза 4 — X5-gap прогон (шаги 1–6)

| Шаг | PRD_MAP | Отложено | Приоритет |
|-----|---------|----------|-----------|
| 1 | UF → `bitrix_extra` | Mass backfill: **~960/3228** (~30%); resync running ETA ~3.7ч | 🔴 |
| 2 | Мультиконтакты | тот же resync — **952** contacts json, **441** multi | 🔴 |
| 3 | Сумма + валюта | **~987/3228** deal_amount (~31%); DevTools ✅ `15 780 $`; 👤 → [`F4_X5_DEAL_AMOUNT_ACCEPTANCE.md`](../phase4/leads/F4_X5_DEAL_AMOUNT_ACCEPTANCE.md) | 🟡 |
| 4 | Встречи/дела (crm.activity) | ✅ без scope task; mass resync в фоне; tasks.task — опционально (портал) | 🟡 |
| 5 | UI карточки X5-gap | ✅ **апрув оператора 2026-06-24** | 🟢 |
| 6 | Mass-resync полей | **in_progress** ~1205/3228 + watcher `--only-missing` | 🔴 |
| 7 | Список: подписка / поставка | ✅ **апрув оператора 2026-06-24** | 🟢 |

`[2026-06-24] | PRD_MAP: Ф4 · X5-gap mass-resync bitrix_extra | Отложено: дождаться прогона 3225 (50/3225 на 2026-06-24) | Причина: Access denied при workers=3 — снижен до 1 | Из шага: F4_BITRIX_FIELDS_RESYNC.md`

`[2026-06-19] | PRD_MAP: Ф4 · X5-gap шаг 6 mass-resync | Отложено: дождаться полного прогона + scope task п.4 + browser апрув | Причина: скрипт готов, прогон долгий | Нужна фаза MAP: 4 | Из шага: resync_bitrix_lead_fields.py`

`[2026-06-19] | PRD_MAP: Ф4 · X5-gap шаги 1–5 | Отложено: mass backfills 1–3, scope task п.4, browser апрув 3+5 | Причина: код закрыт, нужен webhook + оператор | Нужна фаза MAP: 4 | Из шага: сводка прогона шаг 5` **→ шаг 6 закрывает backfill 1–3 одним скриптом**

---

`[2026-06-14] | PRD_MAP: «Ф2 §1 Voice Layer» — ЗАКРЫТО ✅ | Scope: Hermes modules + UI voice_action (modal/navigate/filter/approve) + rescue eval | Сделано: frontend voiceAction/VoiceActionHost, minScore, send_email/save_to_rag approve, `smoke_voice_layer.py` 72 passed, `VOICE_LAYER_ACCEPTANCE.md` | Хвост 🟢: live LLM eval всех модулей (не rescue) — опционально | Коммит: `f2b618e`

| Приоритет | PRD_MAP | Что | Фаза MAP | Кто |
|-----------|---------|-----|----------|-----|
| 🟢 | Ф2 §1 Voice Layer | Live LLM eval analytics/RAG (не только rescue) — опционально при Groq/Ollama | **2** | агент |
| 🔴 | Агенты · quality gates | **Полный live Ollama** ≥ порогов — **не закрыто** (Hermes ReadTimeout CPU; прогон 5 агентов оборвался/долгий) | **2** | `run_agents_quality_gate.py --write-acceptance` |
| 🟡 | Агенты · quality gates | Hermes: GPU / `EVAL_OLLAMA_TIMEOUT=1200` / ночной прогон 36 кейсов | **2** | 👤/агент |
| 🟡 | Агенты · quality gates | `[x]` в MAP — только после зелёного `overall_gate` | **2** | после live |
| 🟢 | Агенты · quality gates | Тюнинг `must_contain` под hermes3 JSON | **2** | агент |
| 🟡 | Голос → лиды п.3, п.5 | Spot-check approve / fanout | **1** | 👤 ты |
| 🟡 | Ф2 §9 | Кнопка «Обогатить» на карточке лида `/leads/{id}` | **2** | ✅ `LEADS_CARD_ENRICH_ACCEPTANCE.md` |
| 🟡 | Лиды п.2 Битрикс синк | Туннель :8000 + вебхук | **2** / DevOps | 👤 ты |
| 🟡 | Ф2 очередь 5 §8 leadgen голос | Голос `/leadgen` | **2** | агент по `go` |
| 🟢 | Layout кода (не ops) | Сплит монолитов, backend/data gitignore | **2+** | см. [`debt/REPO_LAYOUT_DEBT.md`](../debt/REPO_LAYOUT_DEBT.md) |
| 🟢 | Leadgen portrait | LLM review без Groq — graceful fallback | **2** | агент по `go` |

---

## Документация (Фаза 2)

Отсутствующие канонические доки — без них агент угадывает:

| Документ | Зачем | Фаза MAP |
|----------|-------|----------|
| `docs/agents/AGENTS/marketer.md` | промпт маркетолога | 2 |
| `docs/agents/AGENTS/analyst.md` | промпт аналитика | 2 |
| `docs/voice/VOICE.md` | полная схема Voice Layer | 2 |
| `docs/email/EMAIL.md` | архитектура email-агента (сводка → `email/overview.md`) | 2 |
| `docs/ops/SCORING.md` | формула скоринга подробно | 2 |

---

## Безопасность (сквозное — PRD_MAP §Безопасность)

> **Ф2** — перед выходом в интернет (очередь **10**). **Ф3** — роли и аудит. Сейчас dev: `.env` + опциональный `X-API-Key`.

| Приоритет | Фаза | Пункт | Что сделать | Когда |
|-----------|------|-------|-------------|-------|
| 🔴 | **Ф2** | HTTPS / Nginx | TLS + reverse proxy перед uvicorn | Перед любым прод-деплоем |
| 🔴 | **Ф2** | Auth на проде | `SMARTCRM_REQUIRE_AUTH=1`, ротация `SMARTCRM_API_KEY` | Вместе с HTTPS |
| 🟡 | **Ф2** | Vault | Секреты в vault/secrets manager, не `.env` на сервере | Прод-окружение |
| 🟡 | **Ф2** | PII в логах | Маскировать email, телефон, ИНН в логах и `/ops/traces` | До внешних пользователей |
| 🟡 | **Ф2** | Rate limit | Лимиты на публичные и тяжёлые роуты (voice, search, webhooks) | До открытия API наружу |
| 🟡 | **Ф2** | Groq/Ollama policy | Код: не слать чувствительное в LLM; redact перед запросом | До реальных клиентских данных |
| 🟢 | **Ф3** | Роли пользователей | Не один ключ — логин, роли менеджер/админ | Мульти-пользователь |
| 🟢 | **Ф3** | Аудит действий | Кто отправил письмо, удалил лид, экспортировал CSV | Комплаенс / команда |

`[2026-06-11] | PRD_MAP: §Безопасность | Зафиксировано: Ф2 п.1–6 перед продом, Ф3 п.7–8 роли/аудит | Сейчас: dev-режим, X-API-Key опционально | Действие: go очередь 10 при подготовке деплоя`

---

## Инфраструктура (отложено — решить по триггеру)

> Не блокирует закрытие Ф1. Не трогать, пока не закрыт 🔴 E2E микрофон (`§ Ручная работа`). Hermes/voice_action — ✅. Триггер — когда боль станет реальной.

`[2026-06-08] | PRD_MAP: «Поиск и RAG» / Ф2 п.4 «Поиск → RAG авто» | Отложено: Chroma → pgvector в PostgreSQL | Причина: сейчас ~1.6k чанков, Chroma работает; миграция = риск регрессии без выигрыша по PRD | Триггер: массовые авто-чанки, нужен гибрид SQL (лид + семантика в одном запросе), один контейнер в проде | Нужна фаза MAP: конец 2 / начало 3 | Приоритет: 🟢`

`[2026-06-08] | PRD_MAP: «Голос → лиды» / Ф2 «Voice Layer» | Отложено: LiveKit (WebRTC) вместо сырого WS `/ws/voice` | Причина: сейчас batch STT (запись → Whisper → Hermes), не дуплекс-звонок | Триггер: живой аудиострим, эхо, мобильный интернет, удержание связи | Нужна фаза MAP: 3 (или поздняя 2) | Приоритет: 🟢`

`[2026-06-08] | PRD_MAP: стек (FastAPI) | Отложено: Litestar вместо FastAPI | Причина: полная переписка бэкенда, ноль фич для пользователя; FastAPI достаточен | Триггер: конкретный потолок FastAPI (маловероятно) или greenfield | Решение: скорее не делать | Приоритет: 🟢`

---

## Self-improvement (Ф3)

`[2026-06-17] | PRD_MAP: «Краулинг URL вендоров» | Отложено: Playwright для SPA без текста в HTML | Причина: v2 дал 80/80 страниц на ME+PT | Нужна фаза MAP: 3`

`[2026-06-17] | PRD_MAP: «Quality gate tuning» | Отложено: фикс кейса economist-005 (ключевое «финансов») | Причина: 93.3% ≥85%, gate pass | Нужна фаза MAP: 3 | Из шага: live agents C`

`[2026-06-19] | PRD_MAP: «Автономный поиск новых лидов агентами» | Отложено: Telegram-уведомления о новых кандидатах lead hunt | Причина: шаг 5 — in-app баннер + badge в Ops достаточно | Нужна фаза MAP: 3 | Из шага: lead hunt шаг 5`

`[2026-06-17] | PRD_MAP: «Telegram-бот» | Отложено: регистрация бота в BotFather + `TELEGRAM_BOT_TOKEN` / chat_id | Причина: username занят / блок создания; пользователь откладывает | Нужна фаза MAP: 3 Платформа | Из шага: экспорт Excel/PDF`

`[2026-06-17] | PRD_MAP: «Telegram-бот» | Отложено: inline-кнопки approve/reject кандидатов из чата | Причина: MVP — команды + push уведомления | Нужна фаза MAP: 3 | Из шага: Telegram MVP`

`[2026-06-17] | PRD_MAP: «Telegram-бот» | Отложено: Ops critical → Telegram (wiring в ops_store) | Причина: функция notify_ops_critical есть, hook отложен | Нужна фаза MAP: 3 | Из шага: Telegram MVP`

`[2026-06-17] | PRD_MAP: «Импорт/экспорт CRM» | Отложено: AmoCRM import (шаг 3), HubSpot import (шаг 4), push export Amo/HubSpot (шаг 5) | Причина: шаг 1 CSV + шаг 2 Битрикс push — по порядку MAP | Нужна фаза MAP: 3 | Из шага: CSV sync`

---

## CoffeeOS workflow migration (2026-07-18)

> Стандарт agent rules. Шаги 1–4 done.

| Приоритет | Шаг | Статус | Отложено |
|-----------|-----|--------|----------|
| ✅ | **1 каркас** | done | — |
| ✅ | **2 SBR** | done | — |
| ✅ | **3 project-rules** | done | — |
| ✅ | **4 отчёт** | done | таблица Сделано/Не сделано + A/B/C |
| 🟢 | **5 доки** | pending | mass doc links PRD_MAP, PHASE2_ENTRY |
| 🟢 | **5 scratch** | pending | `backend/scripts/scratch/` |
| 🟢 | **6 scope** | pending | уточнить SBR scope (сейчас: MAP+фичи) |

`[2026-07-18] | PRD_MAP: «Ops / agent workflow» | Отложено: шаги 5–6 CoffeeOS migration | Причина: шаг 4 закрыт | Нужна фаза MAP: — | Из шага: rules workflow step 4`

