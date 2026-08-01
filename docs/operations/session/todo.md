# todo — микро-чеклист текущей фичи

## Заказ (дословно)

> «итак сделай ты исправь првоерь что надо работает ли у нас кгрок и так же например проверь получается и сколько лимит у нас будет в день или вообщше
> я имею ввиду не всю тратть ее просто давай добтем задачи првоерм и что работает
> в карточке клиента надо навести порядок»

**Как понял:** проверить живой Groq и его суточные лимиты; починить то, из-за чего Groq не доходит до досье; не жечь лимит зря; довести задачи «Исследовать» до рабочего состояния.

## Найдено (диагностика 2026-08-01)

- Ключ Groq **живой**: `http 200`, лимиты `14400 req/day`, `6000 tokens/min` (llama-3.1-8b-instant).
- Досье падает: **HTTP 413 rate_limit_exceeded** — `Limit 6000, Requested 6150` TPM. Промпт + `max_tokens=2800` не влезают в минутный бюджет.
- Ollama **не запущен** (`ConnectError`) → второго fallback нет → `done_fallback` без LLM.

## Чеклист SBR

### PHASE 1 SPEC
- [x] Диагностика: 413 TPM + Ollama down
- [x] `scripts/check_groq.py` — проверка ключа и остатка лимитов

### PHASE 2 BUILD
- [x] RED: `test_research_groq_budget` 5 FAIL
- [x] GREEN: `estimate_tokens` / `groq_tpm_budget` / `fit_prompt_to_token_budget` + retry по `Limit/Requested` из ответа Groq
- [x] GREEN: env `RESEARCH_GROQ_TPM_BUDGET=5200`, `RESEARCH_GROQ_MAX_TOKENS=2000`, `LLM_CHARS_PER_TOKEN`
- [x] GREEN: JSON-паспорт находится и без `## ` (модель теряет разметку)
- [x] GREEN: паспортный LLM в том же бюджете; Ollama на паспорте выключена (`RESEARCH_PASSPORT_OLLAMA=0`)
- [x] Ollama поднята как второй fallback досье

### PHASE 3 REVIEW
- [x] Прогон #97: `llm=True provider=groq fallback=False`, 52.9с (было 136с), паспорт: industry/city/website + 1 контакт
- [x] Логи: `research_passport: JSON из досье (без второго LLM-вызова)`, 413 нет
- [x] Регрессия `tests/rag/` 127 PASS

### Позже (BACKLOG)
- [ ] п.5 Checko полнее + кэш (сейчас `/finances`, `/legal-cases`, `/contracts` падают → enrich уходит в deadline 25с)
- [ ] п.6 Resync UF (Хохланд #97 и битые)
- [ ] Порядок в карточке клиента — уточнить у пользователя, что именно чинить
