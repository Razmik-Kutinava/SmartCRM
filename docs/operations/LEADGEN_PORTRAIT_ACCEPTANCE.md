# Смоук лидогена — поиск по портрету (2026-06-09)

PRD_MAP: **«Лидогенерация `/leadgen`» — Поиск по портрету** (перепроход)

## Команда

```bash
cd backend && python scripts/smoke_leadgen_portrait.py
```

9 pytest + live `search_by_portrait(reference_inn=5040048921)` (Хохланд Руссланд) + probe `/leadgen`.

**ИНН:** моки `7707070010` (ТехноСофт) — только pytest с Checko mock; live — `5040048921` (`inn_constants.py`).

---

## Пайплайн

1. **Эталон** — `reference_inn` → Checko `fetch_company` + `fetch_full_profile` → критерии (ОКВЭД, город, выручка ±)
2. **Текст портрета** — LLM `_parse_portrait_criteria` + эвристики (город, сотрудники, госконтракты)
3. **Поиск** — параллельно: Checko EGRUL, **Tavily**, **Brave** (ИНН из сниппетов → Checko)
4. **Скоринг** — `_match_portrait` + бонус `_score_reference_similarity`
5. **LLM review** — один вызов `_portrait_fit_analysis` (fit_score, verdict, продукт)

---

## Было → стало

| Было | Стало |
|------|--------|
| Нет API-тестов `/portrait` | **+5** `test_leadgen_portrait_api.py` |
| `reference_inn` без `portrait` → 422 | API принимает только ИНН эталона |
| `NameError: re` в seed queries | `import re` в `portrait_helpers.py` |
| `NameError: _parse_json_safe` в fit analysis | import в `search_by_portrait.py` |
| Критерии только руками | **Select лида из CRM** → `portraitFromLead.js` |
| Нет smoke / testid | `smoke_leadgen_portrait.py`, testid portrait |

**testid:** `leadgen-mode-portrait`, `leadgen-portrait-lead-select`, `leadgen-portrait-inn`, `leadgen-portrait-progress`, `leadgen-portrait-progress-step`, `leadgen-portrait-results`, `leadgen-portrait-reference`, `leadgen-portrait-total`, `leadgen-portrait-company-card`

---

## ✅ СДЕЛАНО и ПРОВЕРЕНО

| # | Шаг | Результат |
|---|-----|-----------|
| 1 | Live smoke эталон `5040048921` (Хохланд) | **3 кандидата**, ОКВЭД пищевка, регион Пенза |
| 2 | API only `reference_inn` | 200, автотекст портрета |
| 3 | Integration mock | эталон исключён из выдачи, match score |
| 4 | UI режим «По портрету» | форма + select лидов (CRM загружается) |
| 5 | DevTools E2E 2026-06-10 (**user-chrome-devtools** MCP) | `/leadgen` → «По портрету» → ИНН `5040048921` → «Найти компании» → progress «Загружаем эталон…» + таймер → POST `/api/leadgen/portrait` **200**, эталон **ХОХЛАНД**, **3** кандидата |
| 6 | Progress UI | `leadgen-portrait-progress`, step + elapsed + bar (`portraitProgress.js`) |

---

## ⚠️ НЕ СДАНО / хвосты

| Пробел | Примечание |
|--------|------------|
| ~~Долгий запрос ~30–90 с без progress~~ | **исправлено:** стадии + таймер + полоса |
| ~~ИНН 7736207543 = Яндекс в ЕГРУЛ, в тестах был ТехноСофт~~ | **исправлено:** `LEADGEN_INN_FIX.md` |
| LLM review при недоступном Groq | **отложено (Ф2):** сейчас ошибка в `errors[]`, кандидаты есть; сделаем graceful fallback без Groq |
| ~~Кластер / холдинг~~ | **отдельный пункт:** `LEADGEN_CLUSTER_ACCEPTANCE.md` |
