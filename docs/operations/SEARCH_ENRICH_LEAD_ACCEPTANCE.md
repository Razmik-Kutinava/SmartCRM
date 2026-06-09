# Смоук обогащения лида из поиска — acceptance (2026-06-09)

PRD_MAP: **«Поиск и RAG (базово)» — enrich-lead**

## Команда

```bash
cd backend && python scripts/smoke_search_enrich_lead.py
```

28+ pytest + live `enrich_lead("Сбербанк")` + probe `/search`.

---

## Было → стало

| Было | Стало |
|------|--------|
| enrich-lead только моки в `test_search_modes_api.py` | **+3 API-теста**, **+2 unit** (Brave, LLM, skip-if-filled) |
| **Brave не вызывался** в `enrich_lead` (баг) | serper + **brave** + tavily |
| DataNewton/Мои-Закупки гонялись на «телефон компании» | убраны — только веб-поиск |
| Пустой `lead.company` проходил API | **400** `lead.company обязателен` |
| LLM мог вернуть `null` в JSON | фильтр пустых значений |
| Нет live smoke / DevTools | `smoke_search_enrich_lead.py` + DevTools таб enrich |
| UI без testid результатов | `search-enrich-results`, `search-enrich-providers` |

---

## §2 Усиление enrich (2026-06-09)

| Было | Стало |
|------|--------|
| Brave 429 при fanout | `brave_limit.py`: **кэш 1ч** + **semaphore 2** + backoff 45с |
| revenue/ЛПР без ИНН | **Checko** по `lead.inn`; таргет-запросы LinkedIn/CEO/выручка |
| Только сниппеты | **Парсинг сайта** (главная + /contacts) |
| Ручной ввод | **Выбор лида из CRM** + **«Сохранить в карточку»** PATCH |

**testid:** `search-enrich-lead-select`, `search-enrich-apply`

---

## ✅ СДЕЛАНО и ПРОВЕРЕНО

| # | Шаг | API | UI | Тест |
|---|-----|-----|-----|------|
| 1 | Запрос обогащения | `POST /api/search/enrich-lead` | таб «Обогащение лида» | pytest mock + live |
| 2 | Поиск в вебе | fanout serper/brave/tavily | — | live 43 источника |
| 3 | LLM extract полей | Groq `core.llm.chat` | блок «Найденные данные» | live phone/email/website |
| 4 | Валидация | 400 без company | кнопка disabled без имени | API test |
| 5 | Checko по ИНН | `lead.inn` в body | select лида | `test_enrich_sources` |
| 6 | Сохранить в CRM | `PATCH /api/leads/{id}` | `search-enrich-apply` | `enrichLeadApply.js` |

**Live smoke (Сбербанк):** `phone`, `website`, `email`, `address` — OK.

**DevTools (`localhost:5173/search`, таб enrich):**

| Проверка | Результат |
|----------|-----------|
| Сбербанк + финансы → «Обогатить» | ✅ ~60 с |
| Провайдеры: serper, tavily, brave | ✅ |
| phone +7 495…, email, website, address | ✅ |
| 43 источника (details) | ✅ |

---

## ⚠️ Тонкие места (известные, не блокер)

| Проблема | Влияние | Как чинить дальше |
|----------|---------|-------------------|
| **Brave 429** при пиковой нагрузке | редко, backoff 45с | кэш+semaphore ✅; при необходимости кэш всего enrich |
| **revenue / linkedin** без ИНН | всё ещё слабо | Checko только с ИНН; мелкие компании — ручной дозапрос |
| Обогащение **с карточки лида** one-click | только `/search` | Ф2: кнопка на `/leads/[id]` |
| Зависимость **GROQ_API_KEY** | без LLM — только raw_results | fallback regex extract или CPU rescue |
| ~**60–90 с** на запрос | UX | кэш enrich по company+industry |

---

## ❌ НЕ СДАЛИ (другой scope)

| Что | Куда |
|-----|------|
| Авто-чанки без approve | Фаза 2 |
| Обогащение с карточки лида one-click | Ф2 / лиды |
| pgvector | BACKLOG инфра |

---

## Файлы

| Зона | Путь |
|------|------|
| Логика | `prospect.py`, `enrich_sources.py`, `brave_limit.py` |
| API | `backend/api/routes/search.py`, `PATCH /api/leads/{id}` |
| UI | `search/+page.svelte`, `lib/search/enrichLeadApply.js` |
| Тесты | `test_brave_limit`, `test_enrich_sources`, `test_search_enrich_lead_api` |
| Смоук | `backend/scripts/smoke_search_enrich_lead.py` |
