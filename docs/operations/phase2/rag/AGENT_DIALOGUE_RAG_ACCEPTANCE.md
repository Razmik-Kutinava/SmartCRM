# Search→RAG: факты из диалога агента (Ф2 §4 п.2)

**PRD_MAP:** «Факты из диалога агента → RAG»

## Было

- `save_to_rag` голосом → сырой текст в коллекцию `all`
- Ответ агента на `/agents` не попадал в RAG автоматически
- Нет извлечения фактов о сделке из JSON вывода агента

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `rag/dialogue_facts.py` | извлечение фактов (summary, BANT, score, …) → Q&A текст |
| `POST /api/rag/ingest-dialogue` | ручной/программный ингест диалога в коллекцию **того же агента** |
| `POST /api/ops/agents/{id}/run` | поле `rag_ingest` (авто при `RAG_DIALOGUE_AUTO_INGEST=1`) |
| `voice/pipeline.py` | после fanout — `rag_dialogue_ingest` для каждого агента с output |
| `/agents` UI | кнопка «💾 В RAG», бейдж авто-ингеста |
| voice `save_to_rag` | approve → `ingest-dialogue` + agent из Hermes |

## Пайплайн

```
Диалог (транскрипт + output агента)
        ↓
extract_deal_facts (эвристика, ≥ RAG_DIALOGUE_MIN_FACTS)
        ↓
dialogue_to_rag_text → ingest_manual_text → Chroma (for_agent = тот же агент)
```

## Env

```env
RAG_DIALOGUE_AUTO_INGEST=1
RAG_DIALOGUE_MIN_FACTS=2
```

## Команды

```bash
cd backend
python -m pytest tests/rag/test_dialogue_facts.py tests/api/test_rag_ingest_dialogue_api.py -q --override-ini="filterwarnings="
python -m pytest tests/test_voice_pipeline.py -q --override-ini="filterwarnings="
```

## Критерии

- [x] Факты из JSON агента → чанки в RAG **его** коллекции
- [x] Авто после `/agents` run и после голосового fanout (env)
- [x] Кнопка «В RAG» на `/agents`
- [x] Voice approve `save_to_rag` с agent_id
- [x] pytest без live LLM

## Не в scope

- LLM-структурирование фактов (BACKLOG, как Q&A из поиска)
- п.3–4 §4 (save everywhere, enrich cache)
