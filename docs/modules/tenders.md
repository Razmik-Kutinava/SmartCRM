# SmartCRM — Тендеры и планы закупок

Краткое описание реализованного функционала: единая вкладка **«Тендеры»**, агрегирующий поиск по внешним источникам, планы закупок через TenderGuru, обогащение карточек и учёт лимитов API.

---

## UI

- Маршрут: **`/tenders`** (`frontend/src/routes/tenders/+page.svelte`).
- В шапке приложения пункт навигации **«Тендеры»** (`frontend/src/routes/+layout.svelte`).
- Режимы:
  - **Тендеры** — общий поиск с датами, фильтрами, консолидация ответов провайдеров.
  - **Планы закупок** — поиск планов (ИНН, ключевые слова, год) и при необходимости детализация плана.
- Результаты нормализуются под единые поля (в т.ч. `title`, `url`, источник) для отображения.

---

## Бэкенд

- Роутер: `backend/api/routes/tenders/` (search, web_search, saved, analyze, plans, detail, classifiers), префикс **`/api/tenders`**.
- Подключение в приложении: `backend/main.py` (импорт и `include_router` для роутера тендеров).

### Основные эндпоинты

| Method | Path | Назначение |
|--------|------|------------|
| GET | `/api/tenders/search` | Поиск: TenderGuru, Gosplan/EИС, **Serper/Tavily** (веб-подсказки); DataNewton по ИНН |
| GET | `/api/tenders/saved` | Список сохранённых (`status=saved\|archived`) |
| POST | `/api/tenders/saved` | Upsert карточки в «Мои» |
| PATCH | `/api/tenders/saved/{id}` | Архив / восстановление, доп. анализы |
| POST | `/api/tenders/analyze` | LLM-анализ: `agent=tender\|tech` |
| GET | `/api/tenders/plans/search` | Поиск планов закупок (TenderGuru `planzakup`) |
| GET | `/api/tenders/plans/detail` | Детальная карточка плана (TenderGuru `plans`) |
| GET | `/api/tenders/enrich/{inn}` | Ручное обогащение контрагента через DataNewton (несколько методов API на один ИНН) |
| GET | `/api/tenders/{tender_id}`, `/api/tenders/number/{tend_num}` | Вспомогательные пути к карточкам/номерам (по реализации клиентов) |
| GET | `/api/tenders/search/docs`, `/api/tenders/search/products`, `/api/tenders/online` | Доп. сценарии поиска/онлайн по API TenderGuru |
| POST | `/api/tenders/save` | Сохранение в `tender_saved` (legacy-совместимость с UI) |

### Провайдеры и сервисы

| Модуль | Файл | Роль |
|--------|------|------|
| TenderGuru | `backend/services/tenderguru.py` | Тендеры, планы (`/planzakup`, `/plans`), форматирование под UI |
| Gosplan (EИС) | `backend/services/gosplan.py` | Официальные закупки через API v2 (тестовый контур `v2test.gosplan.info`) |
| DataNewton | `backend/services/datanewton.py` | Обогащение: контрагент, риски, скоринг, сводка по госконтрактам и др. |
| Zakupki (парсер) | `backend/services/zakupki_parser.py` | Дополнительный разбор/данные с площадок по мере подключения |

Поисковый пайплайн лидогенерации/веб-поиска также умеет дергать **DataNewton** как провайдера подсказок (`/v1/suggestions`) — см. `backend/rag/search.py` и `docs/modules/search.md`.

### Переменные окружения

| Переменная | Назначение |
|------------|------------|
| `TENDERGURU_API_KEY` | Доступ к API TenderGuru |
| `DATANEWTON_API_KEY` | Обогащение и подсказки DataNewton |
| `SERPER_API_KEY` | Google-поиск в выдаче тендеров |
| `TAVILY_API_KEY` | Tavily в выдаче тендеров |
| `GROQ_API_KEY` | LLM для `/analyze` |
| Ключи Gosplan | Задаются в клиенте Gosplan (см. `backend/services/gosplan.py` и комментарии в коде) |

---

## Учёт лимитов API

- Счётчики: `backend/core/stats.py`, функция `track_api`, персистентность `backend/data/api_stats.json`.
- В справочнике лимитов (`KNOWN_LIMITS`) — **`gosplan`**, **`datanewton`**, **`serper`**, **`tavily`**.
- В маршруте тендеров вызовы **Gosplan** и пакеты **DataNewton** при поиске/обогащении учитываются через `track_api`, в т.ч. ошибки — чтобы видеть расход и сбои в **Ops → API Limits** и **Лидогенерация → API Limits**.
- Реальные лимиты у провайдеров могут отличаться (например, ответ **409** у DataNewton при исчерпании квоты) — интерфейс лимитов даёт **наблюдаемость**, не заменяет договор с провайдером.

---

## Экономика и gate платного API

| Этап | Источники | Условие |
|------|-----------|---------|
| Фаза 1–2 | TenderGuru, ЕИС/Gosplan, Serper/Tavily | сейчас |
| Платный API | Контур.Закупки и аналоги | **только после** закрытия минимум одной крупной тендерной сделки через систему |

До gate — не тратить время на стабилизацию парсеров сверх baseline; приоритет — одна реальная сделка. См. `docs/product/PRD.md` (Тендеры), `docs/product/PRD_MAP.md`.

## Известные ограничения

- Релевантность выдачи по коротким запросам различается по источникам; Gosplan может давать много «шума» без узких фильтров.
- DataNewton при исчерпании лимита может возвращать ошибки лимита — смотреть счётчики/алерты в панели лимитов.

---

## См. также

- Маршруты CRM как зеркало лидов: `docs/modules/leads.md`
- Поиск и провайдеры: `docs/modules/search.md`
- Архитектура: `docs/product/ARCHITECTURE.md`
- API (сводная таблица): `docs/api/API.md`
