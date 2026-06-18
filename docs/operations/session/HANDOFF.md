# HANDOFF

`Спринт:[Ф3] | Задача:[Платформа — CSV импорт/экспорт лидов] | Статус: ✅ done`

**2026-06-17:** `crm_sync/csv_adapter`, `POST /import-csv`, `GET /export?format=csv`, UI `/leads/list`; pytest **8 PASS**. Следующий шаг MAP: **Битрикс push (шаг 2)**.

---

`Спринт:[Ф3] | Задача:[Платформа — экспорт Excel/PDF] | Статус: ✅ done`

**2026-06-17:** `export_reports.py` (openpyxl + fpdf2); API analytics `format=csv|xlsx|pdf`, `GET /api/leads/{id}/export`, `GET /api/tenders/saved/export`; UI analytics/карточка/тендеры; pytest **16 PASS**; Telegram → BACKLOG. Коммит: `2bf1adf`.

**Следующий шаг:** «ок» MAP экспорт · Платформа (импорт CRM) / Ф4 по go.

---

`Спринт:[Ф4 docs] | Задача:[Аналитика v2 — план тюнинга] | Статус: ✅ done`

**2026-06-17:** `F4_ANALYTICS_V2_TUNING.md` + пункты в PRD_MAP §Ф4 (прогноз на лиде, калибровка, агенты, квартал).

**Следующий шаг:** реализация Ф4 analytics по go · или **Платформа** / другой блок MAP.

---

`Спринт:[Ф3] | Задача:[Аналитика v2 — прогноз закрытия] | Статус: ✅ done`

**2026-06-17:** `lead_close_forecast`, `closureForecast` в analytics, UI таблица; **Аналитика v2 закрыта 4/4**; pytest **19 PASS**.

**Следующий шаг:** «ок» MAP аналитика · Платформа / Ф4 по go.

---

`Спринт:[Ф3] | Задача:[Аналитика v2 — воронка по источнику] | Статус: ✅ done`

**2026-06-17:** `funnelBySource`, UI чипы на `/leads/analytics`, CSV; pytest **17 PASS**.

**Следующий шаг:** «ок» MAP п.3 · п.4 прогноз закрытия (Экономист).

---

`Спринт:[Ф3] | Задача:[Аналитика v2 — агенты по трейсам] | Статус: ✅ done`

**2026-06-17:** `agent_trace_analytics`, `GET /api/ops/analytics/agents`, UI `/ops/stats`, ссылки улучшения; pytest **5 PASS**.

**Следующий шаг:** «ок» MAP п.2 · п.3 воронка по источнику.

---

`Спринт:[Ф3] | Задача:[Аналитика v2 — когорты] | Статус: ✅ done`

**2026-06-17:** `compute_cohorts`, API `cohorts`, UI `/leads/analytics`, pytest **15 PASS** зона.

**Следующий шаг:** «ок» MAP когорты · п.2 эффективность агентов по трейсам.

---

`Спринт:[Ф4 docs] | Задача:[Тех. спец тендеры — план тюнинга] | Статус: ✅ done`

**2026-06-17:** `F4_TECH_TENDER_TUNING.md` + пункты в PRD_MAP §Ф4 (автопайплайн, доки, матрица ТЗ, CRM, eval).

**Следующий шаг:** реализация Ф4 по go · или **Аналитика v2** / другой блок MAP.

---

**2026-06-17:** MAP п.3 sources `[x]` апрув; п.4 вердикт участия — `tender_participation`, API `participation`, UI вкладка «Вердикт», snapshot; pytest **29 PASS** зона.

**Следующий шаг:** «ок» MAP п.4 · Аналитика v2 / Контур Ф4 — только по go.

---

`Спринт:[Ф3] | Задача:[Тендеры: sources + MAP] | Статус: ✅ done`

**2026-06-17:** MAP п.2 `[x]`; Контур → Ф4 `F4_KONTUR_GATE`; п.3 `tender_sources` + Gosplan prod + фильтры + DataNewton UI; pytest зона тендеров.

**Следующий шаг:** «ок» MAP п.3 sources · **не трогать** п.4 участвовать/нет до go.

---

`Спринт:[Ф3] | Задача:[MAP мониторинг + уведомления/календарь] | Статус: ✅ done`

**2026-06-17:** MAP п.1 мониторинг `[x]`; п.2 — уведомления + календарь (`/tenders/notifications`, `/tenders/calendar`); pytest **16 PASS**.

**Следующий шаг:** «ок» MAP п.2 · Контур API / решение участвовать.

---

`Спринт:[Ф3] | Задача:[pytest.ini filterwarnings] | Статус: ✅ done`

**2026-06-17:** убран битый `StarletteDeprecationWarning` из `pytest.ini` (Starlette 0.46+); `tests/test_pytest_config.py` — 2 PASS; обычный `pytest` без `-c NUL`.

**Следующий шаг:** «ок» MAP мониторинг тендеров п.1 · п.2 календарь.

---

`Спринт:[Ф3] | Задача:[Тех. спец — мониторинг тендеров п.1] | Статус: ✅ done`

**2026-06-17:** переименование «тендерный агент» → **Тех. спец — тендеры**; мониторинг 24/7 — config, фон, API, UI `/ops/tender-monitor`; pytest **9 PASS**.

**Следующий шаг:** «ок» MAP п.1 · п.2 уведомления/календарь дедлайнов.

---

`Спринт:[Ф3] | Задача:[Суфлёр MAP + Ф4 рекомендации] | Статус: ✅ done`

**2026-06-17:** апрув суфлёр → `[x]` MAP; `F4_STRATEGIST_SUGGESTER_TUNING.md` (8 пунктов).

**Следующий шаг:** Ф3 **Тендерный агент** (строка 479 MAP) или Ф4 тюнинг.

---

`Спринт:[Ф3] | Задача:[Авто-суфлёр Стратега] | Статус: ✅ done`

**2026-06-17:** `strategist_suggester.py` + API suggest/apply + UI `/ops/agents`; pytest **8 PASS**. MAP A/B `[x]`.

**Следующий шаг:** «ок» MAP суфлёр · дальше по Ф3/Ф4.

---

`Спринт:[Ф3] | Задача:[A/B промптов — MAP апрув] | Статус: ✅ done`

**2026-06-17:** `[x]` MAP строка 476.

---

`Спринт:[Ф3] | Задача:[A/B промптов по трейсам] | Статус: ✅ done`

**2026-06-17:** `prompt_ab_traces.py` + API `ab-traces` + UI improve; pytest **5 PASS**. MAP crawl `[x]`.

**Следующий шаг:** «ок» MAP A/B · авто-суфлёр Стратега.

---

`Спринт:[Ф3] | Задача:[Vendor crawl — MAP закрыт] | Статус: ✅ done`

**2026-06-17:** краулинг `[x]` MAP; тюнинг → Ф4.

---

`Спринт:[Ф3] | Задача:[Vendor crawl — шаг 4 Playwright SPA] | Статус: ✅ done`

**2026-06-17:** `vendor_crawl_playwright.py`; `use_playwright` (PT on); fallback fetch; UI; pytest **29 PASS**. Live discover на PT seed — 0 новых PDF (уже через search); инфра готова.

**Следующий шаг:** «ок» MAP crawl → A/B промптов.

---

`Спринт:[Ф3] | Задача:[Vendor crawl — шаг 3 live PDF+RAG] | Статус: ✅ done`

**2026-06-17:** live ME+PT — **10 PDF → RAG**, **871 чанк**; фикс `_fetch_bytes`; RAG tech_specialist видит PDF. Tavily 432 (Brave/Serper OK).

**Следующий шаг:** «ок» MAP crawl **или** шаг 4 Playwright.

---

`Спринт:[Ф3] | Задача:[Vendor crawl — шаг 2 фильтр качества] | Статус: ✅ done`

**2026-06-17:** `vendor_crawl_quality.py`; pytest 23 PASS.

---

`Спринт:[Ф3] | Задача:[Vendor crawl — шаг 1 PDF автопоиск] | Статус: ✅ done`

**2026-06-17:** `site:домен filetype:pdf`; `max_pdf_pages`; ingest `%PDF`; pytest 18 PASS.

---

`Спринт:[Ф3] | Задача:[Vendor crawl v2] | Статус: ✅ done`

**2026-06-17:** doc_urls в конфиге/UI; фильтр мусора; приоритет ссылок; PDF ingest; sitemap; live **80/80 стр, 582 чанка** (было 51). pytest **13 PASS**. `[x]` MAP crawl — после «ок».

**Дальше по списку Ф3 Self-improvement:**
1. `[x]` MAP crawl — ваше «ок»
2. A/B промптов по трейсам
3. Авто-суфлёр Стратега
4. (опц.) Playwright для SPA; голосом добавлять doc_urls

---

`Спринт:[Ф3] | Задача:[Vendor crawl live + gate close] | Статус: ✅ done`

**2026-06-17:**
- **Quality gate tuning** — `[x]` MAP: A+B+C + апрув «ок»; Economist 93.3%, остальные 100%. Таблица: `AGENTS_QUALITY_GATE_ACCEPTANCE.md`.
- **Vendor crawl live:** ManageEngine (33 чанка) + PT Security (18) → **51** в RAG `tech_specialist`. Конфиг в `vendor_crawl_config.json`. `[x]` MAP crawl — после вашего «ок».

**Следующий шаг Ф3 Self-improvement:** A/B промптов по трейсам · авто-суфлёр Стратега.

---

`Спринт:[Ф3] | Задача:[Vendor crawl → RAG tec] | Статус: ✅ done`

**2026-06-17:** API + UI `/ops/vendor-crawl` + фон + **live** на manageengine.com/ru и ptsecurity.com.

---

`Спринт:[Ф3] | Задача:[Quality gate tuning] | Статус: ✅ done — [x] MAP`

**2026-06-17:** A+B+C зелёные; acceptance [`F3_GATE_TUNING_ACCEPTANCE.md`](../phase3/agents/F3_GATE_TUNING_ACCEPTANCE.md).

---

`Спринт:[Ф3] | Задача:[Quality gate tuning — шаг 2] | Статус: ✅ done`

**2026-06-16:** Ф3 gate шаг 2 — rescue 36/36, enrich smoke 100%. **Коммит:** `dc1220c`.

---

`Спринт:[Ф3] | Задача:[Quality gate tuning — шаг 1] | Статус: ✅ done`

**2026-06-16:** шаг 1 — порог 85%, parse_intent, enrich tech/econ/strategist. **Коммит:** `6efd107`.
