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
| **P4** | `backend/test_email_integration.py` → `backend/tests/integration/` | — | ждёт `go` |
| **P5** | Незакоммиченное удаление старых `docs/*.md` из корня `docs/` | git history | ждёт `go` |
| **P6** | Сплит топ-монолитов (см. ниже) | регрессия | ждёт `go` по файлу |

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
| `backend/test_email_integration.py` | `backend/` | `backend/tests/integration/test_email_integration.py` | P4 |

### Данные / артефакты — P3 done

| Файл | Было | Стало |
|------|------|-------|
| `tender_sources_ab.json` | `backend/backend/data/` | `backend/data/tender_sources_ab.json` |
| `tender_sources_via_qa.json` (дубль) | `backend/backend/data/` | удалён (канон в `backend/data/`) |
| `backend/backend/` | лишняя вложенность | каталог удалён |

### Доки

| Проблема | Действие | Пакет |
|----------|----------|-------|
| Удалённые `docs/PRD.md`, `docs/ARCHITECTURE.md` … (в git status) | Закоммитить миграцию в `docs/product/`, `docs/modules/` | P5 |
| `docs/reference/CRM-points-system/` | Референс — **не переносить** без явного решения | — |

---

## Код > 200 строк (legacy — сплит по `smartcrm-code-split.mdc`)

Приоритет для P6 (после Фазы 1 по PRD_MAP):

| Строк | Файл | Предлагаемый сплит |
|-------|------|-------------------|
| 1725 | `backend/leadgen/pipeline.py` | `pipeline/search.py`, `score.py`, `persist.py` |
| 983 | `backend/rag/search.py` | `search/providers.py`, `search/merge.py` |
| 962 | `backend/leadgen/modules/checko.py` | по endpoint-группам |
| 793 | `backend/api/routes/ops.py` | `routes/ops/stats.py`, `agents.py`, … |
| 757 | `backend/api/routes/tenders.py` | `routes/tenders/search.py`, `favorites.py` |
| 664 | `backend/core/hermes.py` | `core/hermes/parse.py`, `rescue.py`, `cache.py` |
| 640 | `backend/core/qa_agent.py` | `core/qa/experiments.py`, `stats.py` |
| 354 | `backend/api/routes/leads.py` | `routes/leads/crud.py`, `score.py` |
| 300 | `backend/agents/analyst.py` | промпт / tools / run |

Полный список — по мере касания; не сплитить всё сразу.

---

## Как апрувить

Напиши, например: **`go P1`** или **`go P2+P3`**.  
Агент выполняет один пакет → коммит → обновляет таблицу «Статус» выше.
