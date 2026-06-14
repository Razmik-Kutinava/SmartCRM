# RAG хвост §4 — закрытие BACKLOG (Ф2)

**Дата:** 2026-06-14

## Закрыто в этом шаге

| BACKLOG | Реализация | Acceptance |
|---------|------------|------------|
| `RAG_AUTO_STRUCTURE_LLM` | `qa_structure.py` + `RAG_AUTO_STRUCTURE_LLM=1` | `test_qa_structure.py` |
| `RAG_DIALOGUE_LLM` | `collect_deal_facts` + `RAG_DIALOGUE_LLM=1` | `test_dialogue_facts.py` |
| Live E2E enrich smoke | `smoke_search_enrich_lead.py` + cache repeat | phase1 `SEARCH_ENRICH_LEAD_ACCEPTANCE.md` |
| Полный fetch URL | `fetch_urls_from_hits` / `page_fetch` в enrich | `test_enrich_sources.py` |
| Кнопка на карточке | `/leads/{id}` + `enrichLeadOnCard.js` | `LEADS_CARD_ENRICH_ACCEPTANCE.md` |

## Остаётся (честно)

| Что | Почему не закрыто в Ф2 |
|-----|------------------------|
| **Quality gate ≥85% все агенты** | **Ф3** — baseline 72.2% Hermes, 60% Tech; нужен live Ollama/Groq тюнинг промптов (`AGENTS_GATE_TUNING_BASELINE.md`) |
| Голос «обогати лид» | MAP §9 опц.; отдельный шаг |
| Spot-check live Groq в UI | 👤 ручная проверка |

## §4 + §9 enrich UI — итог MAP

- §4 п.1–4: ✅
- §9 кнопка карточки: ✅
- Опц. LLM-флаги: ✅ (выкл. по умолчанию, без live LLM в CI)
