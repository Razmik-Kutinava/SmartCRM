# Смоук обогащения лида из поиска — acceptance (2026-06-09)

PRD_MAP: **«Поиск и RAG (базово)» — enrich-lead**

## Команда

```bash
cd backend && python scripts/smoke_search_enrich_lead.py
```

20 pytest + live `enrich_lead("Сбербанк")` + probe `/search`.

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

## ✅ СДЕЛАНО и ПРОВЕРЕНО

| # | Шаг | API | UI | Тест |
|---|-----|-----|-----|------|
| 1 | Запрос обогащения | `POST /api/search/enrich-lead` | таб «Обогащение лида» | pytest mock + live |
| 2 | Поиск в вебе | fanout serper/brave/tavily | — | live 43 источника |
| 3 | LLM extract полей | Groq `core.llm.chat` | блок «Найденные данные» | live phone/email/website |
| 4 | Валидация | 400 без company | кнопка disabled без имени | API test |

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
| **Brave 429** при пачке запросов | часть полей только из Serper/Tavily | dedup запросов ✅; опц. semaphore/кэш enrich |
| **revenue / linkedin / ЛПР** часто пустые | слабые сниппеты в выдаче | отдельные запросы + Checko/ИНН если есть в лиде |
| UI **не тянет лид из CRM** | ручной ввод company | кнопка «обогатить» на карточке лида (Ф2) |
| **Нет «применить к лиду»** | только просмотр | PATCH lead из UI после апрува |
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
| Логика | `backend/rag/search/prospect.py` (`enrich_lead`) |
| API | `backend/api/routes/search.py` |
| UI | `frontend/src/routes/search/+page.svelte` |
| Тесты | `tests/rag/test_search_modes.py`, `tests/api/test_search_enrich_lead_api.py` |
| Смоук | `backend/scripts/smoke_search_enrich_lead.py` |
