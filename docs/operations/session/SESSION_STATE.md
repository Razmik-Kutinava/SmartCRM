# SESSION_STATE

Краткий прогресс сессии — **обязательно** после каждого действия (1–2 строки). Шаг с изменениями файлов → запись сюда → `git commit` (код + ops **одним** коммитом) → отчёт. Канон: `workflow/smartcrm-commit-ops.mdc`.

**В строке журнала:** `Коммит: \`этот\`` — запись едет в том же коммите, что и код; реальный хеш агент называет в ответе пользователю. Хеши в старых записях — история, не переписывать. «Прочерк» / «потом» — запрещены.

**Регрессия_счёт:** `2/3` — после каждого GREEN +1; на `3/3` → ещё `run_zone_regression.py all` (или p1+p6), сброс в `0/3`. Docs/rules-only не трогает счётчик. Канон: `smartcrm-dev-gates.mdc` § Счётчик.

2026-08-01 | Действие: SBR RED — агенты с карточки лида: `strategist._analyze` (сейчас ImportError → 500 «Ошибка загрузки агента»), `lead_id` в слотах (аналитик отдавал заглушку «Не указан лид»), урезанный дайджест переписки (экономия токенов); test_agent_email_run 8 FAIL | Коммит: `этот` | Статус: in_progress

2026-08-01 | Действие: SBR GREEN+REVIEW — экран импорта базы: `import_table.py` (read_table/guess_mapping/rows_to_dicts/IMPORT_FIELDS) + `import_routes.py` (`POST /import-preview`, `/import-csv` с form `mapping`, лог импорта) + `source_fallback` в `import_leads_from_rows` (имя файла не перебивает колонку «Источник») + алиасы «наименование/организация/ФИО/тел» + `bases.kind=bitrix_source` + `LeadsImportModal.svelte` (3 шага: drag&drop → сопоставление колонок и имя базы → отчёт) + кнопка «Импорт базы» в шапке и optgroup баз. test_lead_import_preview 6 PASS, test_leads_import_modal 4 PASS, test_leads_list_import_input 3 PASS; UI-прогон в браузере: превью→маппинг→отчёт (+2 лида, база в списке), тестовые лиды удалены | Коммит: `этот` | Хвост A: нет | Хвост B: шаблоны сопоставления и старый `.xls` — BACKLOG | Хвост C: два фронт-смоука красные на чистом HEAD → ISSUES | Статус: done | Регрессия_счёт: 2/3 (crm_leads 111 PASS + 1 известный FAIL)

2026-08-01 | Действие: SBR RED — экран импорта базы: `/import-preview`, импорт по явному mapping колонок, kind `bitrix_source` vs `named`, модалка LeadsImportModal; test_lead_import_preview + test_leads_import_modal 8 FAIL / 1 PASS | Коммит: `этот` | Статус: in_progress

2026-08-01 | Действие: fix «импорт Excel не реагирует» — `<input type=file>` жил внутри `{#if showListMenu}`, кнопка сначала звала `closeListMenu()` → элемент с onchange удалялся из DOM раньше, чем оператор выбирал файл, и событие change терялось; input вынесен из меню в конец разметки, порядок в кнопке `csvInput?.click()` → `closeListMenu()`, `onCsvFileChange` читает `e.target ?? csvInput`, добавлен тост «Загружаю …» (импорт + перечитывание 3258 лидов идут секунды и выглядели как «ничего не происходит»); accept дополнен `.txt`. test_leads_list_import_input 3 PASS; crm_leads 111 PASS + 1 известный FAIL | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: pre-existing FAIL `test_leads_list_filters_labeled` (ищет `tasks_urgent` в +page.svelte, нет и на HEAD) → ISSUES | Статус: done | Регрессия_счёт: 1/3 (crm_leads)

2026-08-01 | Действие: SBR GREEN+REVIEW — базы лидов: xlsx/csv import + scoped dedup + GET sources.bases (__bitrix__) + filterBase UI; test_lead_bases 4 PASS; crm_leads 111 PASS + 1 известный FAIL; p1+p6 | Коммит: `этот` | Хвост A: нет | Хвост B: умный маппинг произвольных заголовков XLS + рабочий пул 360 — BACKLOG | Хвост C: нет | Статус: done | Регрессия_счёт: 0/3 (3/3→p1+p6, сброс)

2026-08-01 | Действие: SBR RED — базы лидов: xlsx import + scoped dedup + bases/Битрикс + filterBase; test_lead_bases 4 FAIL | Коммит: `6405ca4` | Статус: in_progress

2026-08-01 | Действие: SBR GREEN+REVIEW — 3 дырки почты: (1) `emails_from_bitrix_blobs` + `merge_uf_emails_into_checko` в `Lead.to_dict` — UF/tech → company.emails без сети; (2) `mergePassportContacts(..., lead)` дописывает lead.email/company/UF в ЛПР если emails пусто; (3) 🔍 через тот же enrich apply. test_email_passport_holes 7 PASS, rag 134 PASS | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 2/3 (rag PASS; crm_leads 111 PASS + 1 известный FAIL)

2026-08-01 | Действие: SBR RED — 3 дырки почты (UF→passport, lead.email→ЛПР, research→контакты): test_email_passport_holes 6 FAIL / 1 PASS | Коммит: `d0cc4fa` | Статус: in_progress

2026-08-01 | Действие: fix «новый контакт перекрывает предыдущий» — настоящая причина найдена через DevTools: кнопка «+ контакт» в шапке панели, форма встаёт в конец списка; замер на лиде 244 — кнопка y=-1019, новая форма y=828 при окне 666, `newFormVisible: false`, 1847 px ниже кнопки. Оператор форму не видел, считал что кнопка не сработала, и печатал в последнюю видимую — переписывал предыдущий контакт; аудит лида подтверждает: `арам3→арам4→арам5→арам6`, второй контакт переименовывался, третий не появился ни разу, пустая форма отбрасывалась фильтром → «два контакта». Фикс: `data-contact-row` на строке, после добавления `scrollIntoView({block:'center'})` + `focus({preventScroll:true})` с ожиданием строки в DOM (проп приходит от родителя через bind), дубль кнопки «+ контакт» в конце списка. Браузер /leads/244: стало `newFormTop: 357` при окне 666, `isFocused: true`; 5 контактов подряд без клика мышкой по полю сохранены каждый на своём месте, тестовые убраны | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 1/3 (crm_leads 111 PASS + 1 известный FAIL `test_tasks_filter_done_and_combined`; contacts-lib 9 PASS)

2026-08-01 | Действие: обход фронта через Chrome DevTools MCP — 5 косяков: (1) карточка грузила всё дважды (18→10 запросов): `pullLead` ставил `lastFetchedOkId` после двух `await`, `openHubPanel` менял URL и оба вызова подписки проходили проверку → метка `inFlightId` до первого await; (2) кэш списка 4.7 МБ забил квоту localStorage, `setItem` падал молча и кэш застыл (он же кормил баг с контактами) → облегчение записи + чистка ключа при переполнении; (3) `/api/leads/bitrix-import-stats` отдавал 403 «нет прав» со стектрейсом Битрикса и путями `/home/bitrix/...` → 502 + `bitrix_unavailable_detail` (ещё 2 места: import-bitrix, push-bitrix, webhook); (4) список 13с показывал 7 демо-лидов как настоящие → кэш-без-демо + «Загружаю лиды из базы…», демо только при ошибке API; (5) незаполненный контакт прятался под свёрткой после смены вкладки → не сворачиваем незавершённый ввод. Браузер /leads/244: 2→5 контактов сохранены, свёртка 4 из 5, черновик пережил смену вкладки; тестовые контакты убраны | Коммит: `этот` | Хвост A: нет | Хвост B: пагинация `/api/leads` (13.2с, 14 МБ, 82 поля) + 21 поле формы без id/name → BACKLOG | Хвост C: нет | Статус: done | Регрессия_счёт: 0/3 (all: crm_leads 111 PASS + 1 известный FAIL `test_tasks_filter_done_and_combined` — красный и до правок, остальные зоны PASS)

2026-08-01 | Действие: fix «новый контакт перекрывает предыдущий» — `page.subscribe(pullLead)` срабатывал на смену `?panel=`/`?tab=` и пересобирал черновики из сохранённого лида, незаполненная форма исчезала и ввод шёл в предыдущую карточку; `pullLead` теперь выходит сразу при том же лиде; добавлена свёртка >4 контактов в readonly-списке и форме («Показать все (N)» / «Свернуть»), `addContact` раскрывает список и даёт id со случайным хвостом вне secure context; браузер /leads/244: черновик пережил смену вкладки, 6 контактов сохранены, видно 4 | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 2/3 (crm_leads 111 PASS, 1 известный FAIL)

2026-08-01 | Действие: fix «третий контакт заменяет второй» — карточка читала лид из кэша списка (`fetchLeadById` вызывался, результат выбрасывался; `fetchLeads()` на 3258 лидах >10с), форма пересобиралась из старых данных и следующее сохранение стирало третий контакт; добавлены `refreshLeadFromApi` + фоновое обновление кэша, заменено в 10 местах; браузер /leads/244: 2→3→4, счётчик совпадает сразу; lib+contacts 122 PASS, crm_leads 111 PASS (1 известный FAIL из ISSUES) | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: удалённый последний контакт воскресает из плоских полей → ISSUES 2026-08-01 | Статус: done | Регрессия_счёт: 1/3 (crm_leads)

2026-08-01 | Действие: SBR GREEN+REVIEW — Groq TPM-бюджет: fit_prompt_to_token_budget + retry по Limit/Requested, JSON-паспорт без `## `, паспортный LLM в бюджете, Ollama на паспорте off, enrich 45→25с, query LLM 8→15с; Ollama serve поднята; прогон #97: llm=True provider=groq 52.9с (было 136с), паспорт industry/city/website; rag 127 PASS, p1 PASS, p6 PASS | Коммит: `этот` | Хвост A: нет | Хвост B: п.5 Checko (/finances, /legal-cases падают → enrich в deadline) | Хвост C: порядок в карточке клиента — ждём от пользователя, что чинить | Статус: done | Регрессия_счёт: 0/3 (rag+p1+p6)

2026-08-01 | Действие: SBR RED — Groq TPM-бюджет досье (413 `Limit 6000, Requested 6150`): test_research_groq_budget 5 FAIL (нет estimate_tokens / fit_prompt_to_token_budget / groq_tpm_budget / retry на 413) | Коммит: `этот` | Статус: in_progress

2026-07-31 | Действие: fix 🔍 hang — жёсткий deadline enrich/narrative (не ждём отмену Ollama), без 2-го LLM на паспорт после Ollama, quality-gate досье, env-лимиты; прямой прогон #97 99.7с fallback; Groq key expired | Коммит: `этот` | Хвост A: живой Groq (нужен новый ключ) | Хвост B: п.5 Checko | Хвост C: нет | Статус: done | Регрессия_счёт: 2/3 (rag)

2026-07-31 | Действие: SBR PHASE 3 REVIEW — 🔍 надёжная выжимка п.1–4; MCP /leads/97: статус+fallback 58с без LLM, досье видно, контакты живы; п.5 Checko → BACKLOG; reliability 8 + leads/analyst 32 PASS | Коммит: `этот` | Хвост A: нет | Хвост B: п.5 Checko + п.6 Resync UF | Хвост C: нет | Статус: done | Регрессия_счёт: 1/3 (rag)

2026-07-31 | Действие: SBR GREEN п.1–4 — 🔍 один LLM-проход (досье + JSON-паспорт), readable_fallback_dossier, ensure_nonempty_summary/ensureSummary, UI-статус ищу/синтез/без LLM + секунды; rag 117 PASS, analyst+leads 32 PASS | Коммит: `этот` | Хвост A: нет | Хвост B: п.5 Checko + п.6 Resync UF | Хвост C: нет | Статус: in_progress (стоп до «ок») | Регрессия_счёт: 1/3 (rag)

2026-07-31 | Действие: SBR RED — 🔍 надёжность п.1–4: test_research_reliability 5 FAIL / 1 PASS (нет ensure_nonempty_summary, readable_fallback, research_status, UI) | Коммит: `этот` | Статус: in_progress

2026-07-31 | Действие: SBR PHASE 0+1 SPEC — 🔍 надёжная выжимка п.1–4 (LLM/fallback/UI); п.5 Checko и п.6 Resync отложены; стоп до go на RED | Коммит: `этот` | Хвост A: нет | Хвост B: п.5+п.6 | Хвост C: нет | Статус: in_progress

2026-07-30 | Действие: fix 🔍 не затирает UF/паспорт — mergeCheckoJson+mergeTechJson (фронт) + lead_json_merge на PATCH; test_leads 27 PASS; p1+p6 PASS → сброс | Коммит: `этот` | Хвост A: нет | Хвост B: BACKLOG restore UF #97 | Хвост C: нет | Статус: done | Регрессия_счёт: 0/3

2026-07-30 | Действие: SBR GREEN+REVIEW — 🔍→паспорт: research_passport (regex+LLM), merge Checko, contacts/industry/phone/email; rag 109 PASS | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 2/3 (rag)

2026-07-30 | Действие: SBR RED — research→passport (почта/тел/контакты/отрасль): test_research_passport FAIL (нет research_passport.py) | Коммит: `этот` | Статус: in_progress

2026-07-30 | Действие: полное досье исследования — Groq→Ollama синтез, fetch 3 страниц, agent_brief в контекст агентов; rag 102 PASS, analyst 5 PASS | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 1/3 (rag)

2026-07-30 | Действие: fix each_key_duplicate в «Исследование (веб)» — ключ `${i}:url` при дублях hits | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 0/3 (frontend one-liner)

2026-07-29 | Действие: fix исследование — fallback-выжимка без LLM, фильтр мусора URL, без «Ошибка синтеза» в description; 8 PASS | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 2/3 (search)

2026-07-29 | Действие: 🔍 Исследовать — `POST /api/search/research-lead` (Brave/Tavily/Serper + enrich + выжимка в `checkoJson.analyses.web_research`); кнопка на карточке; smoke 5 PASS | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 2/3 (search+frontend)

2026-07-26 | Действие: fix скролл карточки лида — шапка ~450px съедала экран, hub ~90px; единый `lead-card-scroll` overflow-y-auto; smoke 18 PASS | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 0/3 (frontend layout)

2026-07-26 | Действие: fix «Лид не найден» на карточке — API OK, кэш localStorage ~5MB молча падал; memoryCache + lead из ответа fetchLeadById напрямую; smoke 2 PASS; crm_leads 109 PASS / 1 pre-existing ISSUES; p1+p6 PASS → сброс счётчика | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 0/3

2026-07-26 | Действие: fix tenderApi.js — восстановлен `export async function createLeadFromTender` (orphan-тело ломало Vite/preload /tenders) | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 2/3 (frontend + smoke; p1 PASS)

2026-07-26 | Действие: fix Svelte `{{company}}` в placeholder (email + nurture) — ReferenceError company is not defined | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: tenders preload 500 (не в этом шаге) | Статус: done | Регрессия_счёт: 2/3

2026-07-24 | Действие: fix coach — `taskDueBadge` null → `badge?.label` (карточка не падала при PATCH/создании) | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 2/3 (frontend one-liner)

2026-07-24 | Действие: Апрув 1 Карточка клиента — каркас секций (компания→…→системные→UF хвост); `LeadClientCardForm` + meta; Паспорт as-is; smoke 22 PASS; стоп до «ок»/`go` на Апрув 2 (контакты) | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 2/3 (frontend-only, счётчик не +)

2026-07-24 | Действие: бриф направления Лиды — `F4_LEADS_DIRECTION.md` + пункты CHECKLIST_F4 (автоскор, Мой день, шапка, путь сделки, 🔍); BACKLOG рабочий пул/умный импорт; код не трогали | Коммит: `этот` | Хвост A: нет | Хвост B: BACKLOG пул+импорт | Хвост C: нет | Статус: done

2026-07-23 | Действие: SBR GREEN+REVIEW — tech_specialist на карточке лида: AGENT_LIST + POST /api/agents/email/run + превью хаба; smoke 15 PASS | Коммит: `81d9c89` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 2/3

2026-07-23 | Действие: SBR RED — tech_specialist на карточке лида: `test_lead_card_tech_agent.py` 3 FAIL | Коммит: `ac73088` | Статус: in_progress

2026-07-23 | Действие: SBR GREEN+REVIEW — редизайн хаба карточки: 5 плиток (Клиент/Работа/Письма/Продукты/Агенты), этап+путь в шапке, без ✉️/🔗 в тулбаре; smoke 25 PASS; зона frontend lead-card | Коммит: `dc18dca` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done | Регрессия_счёт: 1/3

2026-07-23 | Действие: SBR RED — редизайн хаба карточки: `tests/smoke/test_lead_card_hub_v2.py` 5 FAIL (нет client/work, этап не в шапке) | Коммит: `05ec765` | Статус: in_progress

2026-07-23 | Действие: SBR GREEN+REVIEW — DnD порядка плиток хаба `/leads/[id]`: `hubTileOrder.js` (normalize/move/localStorage), DnD в `LeadHubTile`+карточке; тесты 3/3 PASS; регрессия frontend-only (счётчик не трогали) | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-23 | Действие: SBR RED — DnD порядка плиток хаба: `tests/frontend/test_hub_tile_order.py` FAIL (нет hubTileOrder.js + маркеров DnD) | Коммит: `40dd5f2` | Статус: in_progress

2026-07-23 | Действие: токен-оптимизация workflow — широкий заказ→2–3 варианта; короткие pytest-логи в отчёте; лёгкое чтение доков (пункт+спека); Регрессия_счёт зона×3→all в SESSION_STATE/dev-gates/SBR; RULES_MATRIX R15 | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-23 | Действие: переименование чеклистов фаз — `CHECKLIST.md` → `CHECKLIST_F1.md`…`CHECKLIST_F4.md`; ссылки в rules/docs/README обновлены; исторические записи в журналах не переписывались | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-23 | Действие: подписи чеклистов фаз — H1 уже «Чеклист: Фаза N»; тексты ссылок и README (phase1–4, docs/README, operations/README, ROADMAP, PRD, BACKLOG, todo, RULES_MATRIX, REPO_LAYOUT) приведены к «Чеклист: Фаза N — …»; файлы CHECKLIST.md не переименовывались | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-21 | Действие: SBR GREEN+REVIEW — «база → рассылка по source»: `import-csv?source=` (метка всем строкам, важнее колонки), `GET /leads/sources` (count/withEmail), фильтр «Источник» в массовой рассылке (`EmailCampaignPanel` + `campaignSegmentLogic` + smoke) и поле «Метка базы» в меню импорта `/leads/list`; тесты 4/4 + смоук 8 PASS; регрессия crm_leads 109 PASS / 1 pre-existing (`test_tasks_filter_done_and_combined` → ISSUES), email 33 PASS / 1 pre-existing (уже в ISSUES); DevTools: Plixer + балл 0 → «Лидов: 27» | Коммит: `этот` | Хвост A: нет | Хвост B: BACKLOG «фильтр даты регистрации компании» | Хвост C: ISSUES 🟡 `test_tasks_filter_done_and_combined` (pre-existing) | Статус: done

2026-07-21 | Действие: SBR RED — «база → рассылка по source»: `tests/api/test_lead_source_segment.py` (4 FAIL: import-csv?source=, GET /leads/sources 422, segment-preview по source 0) | Коммит: `этот` | Статус: in_progress

2026-07-21 | Действие: SBR GREEN+REVIEW — Ф4 Email «Ящики в UI без .env»: явный commit в `POST /accounts/connect` (тест 4/4 PASS); UI модал «Почтовые ящики» — синк per-account, секция «Ящики в .env» + импорт (`bootstrapEmailFromEnv`), скролл модалки; регрессия зоны email 33 PASS / 1 pre-existing FAIL → ISSUES; DevTools MCP проверено; доки F4_EMAIL_TUNING §A, tests/README | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: ISSUES 🟡 `test_faq_autoreply_mocked` env-зависимый (pre-existing) | Статус: done

2026-07-21 | Действие: SBR RED — `tests/api/test_email_accounts_api.py` (4 теста): 3 FAIL / 1 PASS — connect не коммитит сам (держится на commit внутри sync), bootstrap после UI-connect видит created=True; GREEN — явный commit в connect-потоке | Коммит: `этот` | Статус: in_progress

2026-07-21 | Действие: SBR PHASE 0+1 — Ф4 Email «Ящики в UI без .env»: заказ дословно + микро-чеклист в todo.md; разведка: connect/DELETE/шифрование уже есть, гэпы — список ящиков+сводка env+bootstrap в модалке настроек `/email`, API-тесты accounts; ждём go на BUILD (RED) | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: in_progress

2026-07-21 | Действие: PHASE 0 INTAKE в SBR — заказ пользователя дословной цитатой в todo.md (§ «Заказ (дословно)» + «Как понял»), пункт чеклиста фазы и доки области создаются до кода; правки: spec-build-review (PHASE 0), task-workflow (старт задачи), index, RULES_MATRIX, шаблон todo.md; verify_cursor_rules_precedence OK | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-21 | Действие: свежесть CHANGELOG/HANDOFF в check_agent_step — `ops_freshness_errors()`: done-шаг в SESSION_STATE новее последней записи CHANGELOG (`## дата`) / HANDOFF (`**дата:**`) → FAIL в check_step; in_progress (RED) не проверяется; +8 тестов `test_check_agent_step.py`, pytest tests/scripts 30 PASS; README scripts (3 валидатора) + tests; переустановлен pre-commit hook (был мёртвый путь без session/) — руками пользователя | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: hook был мёртвый — закрыт переустановкой, не в ISSUES (пофикшен сразу) | Статус: done

2026-07-21 | Действие: BACKLOG запись «процесс · todo.md» — агент сам начинает вести todo.md в ближайшие 3–6 прогонов, без напоминания; сейчас ничего не заполняем | Коммит: `этот` | Хвост A: нет | Хвост B: BACKLOG «процесс · todo.md» | Хвост C: нет | Статус: done

2026-07-21 | Действие: оптимизация workflow — (1) один коммит на шаг: ops с `Коммит: этот` едут вместе с кодом, валидаторы принимают маркер, HANDOFF-проверка по последним 20 хешам (вечный WARN убран); (2) `scripts/check_step.cmd` — 3 валидатора одним вызовом UTF-8 (python в PowerShell Cursor теряет exit code); (3) триаж ISSUES: 4 стейл-записи закрыты с подтверждения, архив 2026-05/06_ISSUES, правило R14 «должки >месяца»; (4) BACKLOG: закрытое → архив 2026-06/07_BACKLOG; (5) regex сужены `{0,25}` + фикс scan_file; pytest tests/scripts 22 PASS | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-21 | Действие: чеклисты фаз вместо PRD_MAP — созданы `docs/operations/phase{1-4}/CHECKLIST.md` (Ф1–Ф3 из архива, Ф4 из живого MAP + сводка модулей); `PRD_MAP.md` и `PRD_MAP_F1-F3.md` удалены; PHASE2_ENTRY → `docs/archive/ops/`; правила и доки переведены на «чеклист фазы»; +phase3/README; фикс ссылок PRD_NOTES; линк-чек 0 битых, валидаторы OK | Коммит: `7462df9` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-21 | Действие: разгрузка токенов — 4 шага: (1) дедуп правил: agent-workflow влит в commit-ops, task-workflow/-40%, .cursorrules/AGENTS.md/index сжаты, repo-layout+file-size-split на globs; (2) архив ops по месяцам → docs/archive/ops/; (3) продукт: VISION/ROADMAP/BUSINESS_LOGIC/FUNCTIONAL созданы, PRD/PRD_MAP разгружены, NOTES/DELTA/Ф1-Ф3 в архив; (4) DESIGN_SYSTEM.md; линк-чек 0 битых, все валидаторы OK | Коммит: `fdadf31`+`119d94d`+`8ffc43b`+`5b2070d`+ops | Хвост A: нет | Хвост B: BACKLOG редизайн UI | Хвост C: починены 7 старых битых ссылок в доках | Статус: done

2026-07-21 | Действие: чистка git status — runtime backend/data (api_stats, traces, checko_cache, ops_queue, sqlite и др.) в .gitignore + untrack; eval_benchmark_data.py → scripts/; .pytest_cache корня удалён; pytest tests/scripts 12 PASS | Коммит: `7a57856` | Хвост A: нет | Хвост B: BACKLOG архивация толстых ops-файлов | Хвост C: нет | Статус: done

2026-07-21 | Действие: BACKLOG § фронт/бэк связка — BFF-прокси, SSR-load, стриминг агентов; пока не делаем, ждёт go | Коммит: `3a98435` | Хвост A: нет | Хвост B: BACKLOG § фронт/бэк связка | Хвост C: нет | Статус: done

2026-07-18 | Действие: кнопка «+ Добавить ящик» в сайдбаре под «Все ящики»; browser-проверка через DevTools MCP (2 ящика видны, модал открывается) | Коммит: `f5d94d6` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-18 | Действие: управление ящиками — DELETE /api/email/accounts/{id} + сервис purge + UI кнопка «Отключить»; pytest 30 PASS | Коммит: `dfe93de` | Хвост A: browser не кликали; второй ящик не подключали | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-18 | Действие: BACKLOG § улучшения CI — 3 апгрейда (GROQ_API_KEY secret, зоны регрессии в CI, check_agent_step в CI); не срочно | Коммит: `f58fbde` | Хвост A: нет | Хвост B: BACKLOG § улучшения CI | Хвост C: нет | Статус: done

2026-07-18 | Действие: `.claude/` в .gitignore — untrack (git rm --cached), файлы на диске остались; секреты settings.local.json больше не в git | Коммит: `3e69864` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 6 — SBR scope апрув (MAP+фичи; one-liner без SBR); миграция закрыта; BACKLOG post-migration долги | Коммит: `4a77384` | Хвост A: нет | Хвост B: BACKLOG § долги post-migration | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 5 — doc links workflow/ (PRD_MAP, PHASE2_ENTRY, docs/README, archive, debt); backend/scripts/scratch/; scripts/README | Коммит: `e89aa99` | Хвост A: SBR scope апрув (шаг 6) | Хвост B: BACKLOG обновлён | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 4 — merged отчёт: таблица Сделано/Не сделано + A/B/C в task-workflow, commit-ops, agent-workflow, SBR, AGENTS, RULES_MATRIX | Коммит: `c872031` | Хвост A: doc links, scratch, SBR scope | Хвост B: BACKLOG обновлён | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 3 — project-rules: 6× smartcrm-{core,tests,http,data,agents,performance}.mdc; index, .cursorrules, RULES_MATRIX; BACKLOG 4–6 | Коммит: `4456d72` | Хвост A: merged отчёт, doc links, scratch, SBR scope | Хвост B: BACKLOG обновлён | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 2 — SBR: spec-build-review.mdc, todo.md, RED/GREEN в commit-ops/task-workflow/dev-gates/index; BACKLOG шаги 3–6 | Коммит: `a5f72b3` | Хвост A: project-rules, merged отчёт, doc links, scratch, scope SBR апрув | Хвост B: BACKLOG обновлён | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 1 — `.cursor/rules/workflow/` (6 mdc), `project/` placeholder, `smartcrm-index.mdc`; rename code-split→file-size-split; обновлены AGENTS.md, .cursorrules, RULES_MATRIX, verify_cursor_rules_precedence.py; BACKLOG шаги 2–6 | Коммит: `c4318aa` | Хвост A: SBR, project-rules, merged отчёт, mass doc links, scratch | Хвост B: BACKLOG § CoffeeOS migration | Хвост C: нет | Статус: done

2026-07-01 | Действие: spawn_bitrix_backfill_focused — поля/tasks/products/import; task scope OK; timeline done; FAQ/IMAP выкл; pytest 2 PASS | Коммит: `7d40b32` | Хвост A: дождаться fields+import | Хвост B: нет | Хвост C: requisite.list Access denied (не блокер) | Статус: in_progress

> Архив: `docs/archive/ops/` (записи по месяцам).
