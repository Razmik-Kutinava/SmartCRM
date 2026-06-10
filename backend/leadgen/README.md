# Leadgen — лидогенерация

Поиск компаний, сбор данных, скоринг, карточка лида. Вызывается из `/api/leadgen` и из `agents/orchestrator`.

---

| `inn_constants.py` | Канон ИНН: мок `7707070010` (ТехноСофт), live `5040048921` (Хохланд) |

## Пакет `pipeline/` — главный пайплайн

| Файл | За что |
|------|--------|
| `run_pipeline.py` | Точка входа: ИНН/название/портрет → карточка |
| `gather.py` | Параллельный сбор: Checko, ФНС, Hunter, Apollo, новости |
| `search_by_portrait.py` | Поиск компаний по текстовому портрету |
| `cluster.py` | Связанные компании по ИНН (2 уровня) |
| `score_card.py` | Финальный скор и сборка карточки |
| `persist.py` | Сохранение лида в CRM (БД) |
| `portrait_helpers.py` | Критерии портрета, match, эталон |
| `portrait_cache.py` | Кэш portrait-review |
| `utils.py` | Утилиты: домен, деньги, JSON, контакты |

Публичный API: `from leadgen.pipeline import run_pipeline, run_cluster, search_by_portrait`.

---

## Пакет `modules/checko/` — API Checko.ru

| Файл | За что |
|------|--------|
| `search.py` | Поиск и `fetch_company` по ИНН |
| `endpoints.py` | Финансы, арбитраж, ФССП, закупки, профиль |
| `parse_company.py` | Парсинг ответа ЕГРЮЛ |
| `http_client.py` | HTTP + ключ API |
| `cache.py` | Кэш и circuit breaker |
| `helpers.py` | `_parse_status`, `_num` и др. |
| `person.py` | Данные по физлицу |

---

## Другие модули в `modules/`

| Файл | За что |
|------|--------|
| `fns.py` | ФНС: финансы, ЕГРЮЛ fallback |
| `apollo.py` | Apollo.io: люди и компании |
| `buster.py` | Hunter/Buster: email по домену |
| `builtwith.py` | Технологии на сайте |
| `newsapi.py` | Новости компании |
| `dadata.py` | DaData (если подключён) |

---

## Корень `leadgen/`

| Файл | За что |
|------|--------|
| `analyzers.py` | 5 анализов профиля (IT, решения, рост…) |
