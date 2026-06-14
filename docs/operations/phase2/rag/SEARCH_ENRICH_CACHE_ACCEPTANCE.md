# Search: кэш результата enrich (Ф2 §4 п.4)

**PRD_MAP:** «Кэш результата enrich» (ключ: company + ИНН + industry, TTL ~24 ч)

## Было

- Кэшировался только **Brave** по одному поисковому запросу (`brave_limit.py`)
- Повторный `enrich_lead` для той же компании снова гонял Serper/Brave/Tavily + Groq LLM (~60–90 с)
- Нет флага «обновить без кэша» в API/UI

## Стало

| Компонент | Поведение |
|-----------|-----------|
| `enrich_cache.py` | Ключ `sha256(company\|inn\|industry)[:32]`; файл `data/artifacts/search/enrich_cache.json`; TTL `ENRICH_CACHE_TTL_HOURS` (default 24) |
| `enrich_lead(..., force=False)` | Cache hit → мгновенный ответ, `cached: true`, без провайдеров/LLM |
| `POST /enrich-lead` | Поле `force: bool` — игнор кэша |
| `GET/DELETE /api/search/cache` | `company_entries` + `enrich_entries` (stats) |
| UI `/search` enrich | Чекбокс «Без кэша»; бейдж «из кэша enrich (24 ч)» |

## Команды

```bash
cd backend
python -m pytest tests/rag/test_enrich_cache.py tests/rag/test_search_modes.py tests/api/test_search_enrich_lead_api.py -q --override-ini="filterwarnings="
```

## Критерии

- [x] Ключ company + ИНН + industry
- [x] TTL ~24 ч (env)
- [x] Повторный enrich без Serper/Brave/Groq
- [x] `force` в API + UI
- [x] pytest hit/miss/TTL/force

---

## §4 «Поиск → RAG авто» — итог после п.4

| п. | Пункт MAP | Статус |
|----|-----------|--------|
| 1 | Авто-чанки при relevance > порога | ✅ |
| 2 | Факты из диалога агента → RAG | ✅ |
| 3 | «Сохранить в базу» везде в поиске | ✅ |
| 4 | Кэш результата enrich | ✅ |

**§4 закрыт** (все 4 пункта MAP).

### Не сделано / отложено (вне scope §4)

| Что | Где |
|-----|-----|
| LLM-структурирование Q&A перед авто-ingest | BACKLOG `RAG_AUTO_STRUCTURE_LLM` |
| LLM-извлечение фактов из диалога | BACKLOG `RAG_DIALOGUE_LLM` |
| Live E2E enrich smoke (реальные ключи) | BACKLOG phase1 |
| Полный fetch страницы по URL при enrich | улучшение, не в MAP §4 |
| Quality gate тюнинг ≥85% | Ф3 `AGENTS_GATE_TUNING_BASELINE.md` |

### Следующий блок MAP

**§5 Self-improvement** — версионирование промптов в Ops.
