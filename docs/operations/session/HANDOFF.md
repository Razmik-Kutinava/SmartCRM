# HANDOFF

`Спринт:[Ф3] | Задача:[Vendor crawl v2 — doc_urls, фильтр, PDF] | Статус: ✅ done`

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
