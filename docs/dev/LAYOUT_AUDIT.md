# SmartCRM — аудит структуры (что не на месте)

> **Статус:** только список. Переносы — пакетами после **`go`**.  
> Обновлять при каждом согласованном пакете.

---

## Пакеты для апрува

| Пакет | Что | Риск | Статус |
|-------|-----|------|--------|
| **P1** | Корневой `tests/` → `backend/tests/` | импорты, pytest.ini, CI | **done** (2026-06-07) |
| **P2** | Мусор в корне → `docs/api/openapi/`, `backend/data/artifacts/`; `.gitignore` | — | **done** (2026-06-07) |
| **P3** | `backend/backend/data/` → `backend/data/` | пути в тендерных скриптах | **done** (2026-06-07) |
| **P4** | `backend/test_email_integration.py` → `backend/tests/integration/` | — | **done** (2026-06-07) |
| **P5** | Миграция плоских `docs/*.md` → вложенная структура | git history | **done** (2026-06-07) |
| **P6** | Сплит топ-монолитов (см. ниже) | регрессия | **done** (2026-06-07) |

---

## Файлы не в каноне (детально)

### Корень репозитория

| Файл | Сейчас | Куда | Пакет |
|------|--------|------|-------|
| `result.json` | `/` | `backend/data/artifacts/` | P2 |
| `swagger.json` | `/` | `docs/api/` или `backend/data/openapi/` | P2 |
| `datanewton-api-v1-openapi-schema.json` | `/` | `docs/api/` | P2 |

### Тесты (дубль) — P1 done

| Файл | Было | Стало |
|------|------|-------|
| `conftest.py` | `/tests/` | `backend/tests/conftest.py` |
| `test_leads_api.py` | `/tests/` | `backend/tests/api/test_leads_api.py` |
| `test_eval_scenarios_api.py` | `/tests/` | `backend/tests/api/test_eval_scenarios_api.py` |
| `test_hermes_eval.py` | `/tests/` | `backend/tests/core/test_hermes_eval.py` |
| `test_rag_chunks.py` | `/tests/` | `backend/tests/rag/test_rag_chunks.py` |
| `test_email_integration.py` | `backend/` | `backend/tests/integration/test_email_integration.py` | P4 done |

### Данные / артефакты — P3 done

| Файл | Было | Стало |
|------|------|-------|
| `tender_sources_ab.json` | `backend/backend/data/` | `backend/data/tender_sources_ab.json` |
| `tender_sources_via_qa.json` (дубль) | `backend/backend/data/` | удалён (канон в `backend/data/`) |
| `backend/backend/` | лишняя вложенность | каталог удалён |

### Доки — P5 done

| Было | Стало |
|------|-------|
| 17 файлов `docs/*.md` в корне | удалены из git; контент в `product/`, `modules/`, `start/`, `email/`, `voice/`, `dev/`, `archive/` |
| Таблица миграции | `docs/README.md` § «Старые пути» |

`docs/reference/CRM-points-system/` — **не в git** (локальный клон для сравнения).

---

## Код > 200 строк (legacy — сплит по `smartcrm-code-split.mdc`)

Приоритет для P6 (после Фазы 1 по PRD_MAP):

| Строк | Файл | Предлагаемый сплит |
|-------|------|-------------------|
| ~~1725~~ | ~~`backend/leadgen/pipeline.py`~~ | **`leadgen/pipeline/`** (run, cluster, search_by_portrait, gather, score_card, persist, portrait_*, utils) — done |
| ~~983~~ | ~~`backend/rag/search.py`~~ | **`rag/search/`** (cache, config, providers, merge, company_search, prospect, rag_queries) — done |
| ~~962~~ | ~~`backend/leadgen/modules/checko.py`~~ | **`leadgen/modules/checko/`** (cache, http_client, helpers, parse_company, search, endpoints, person) — done |
| ~~793~~ | ~~`backend/api/routes/ops.py`~~ | **`api/routes/ops/`** — done |
| ~~757~~ | ~~`backend/api/routes/tenders.py`~~ | **`api/routes/tenders/`** — done |
| ~~664~~ | ~~`backend/core/hermes.py`~~ | **`core/hermes/`** — done |
| ~~640~~ | ~~`backend/core/qa_agent.py`~~ | **`core/qa/`** — done |
| ~~354~~ | ~~`api/routes/leads.py`~~ | **`api/routes/leads/`** — done |
| ~~300~~ | ~~`backend/agents/analyst.py`~~ | **`agents/analyst/`** — done |

Полный список — по мере касания; не сплитить всё сразу.

---

## Как апрувить

Напиши, например: **`go P1`** или **`go P2+P3`**.  
Агент выполняет один пакет → коммит → обновляет таблицу «Статус» выше.
