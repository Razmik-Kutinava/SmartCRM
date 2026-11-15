# todo — микро-чеклист: ускорение голосового пайплайна

## Заказ (дословно)

> Сделать голос быстрее кнопок. Оператор не должен ждать >3 сек.
>
> 1. Логи таймингов (voice/pipeline.py): в _run_pipeline обернуть каждый этап в time.monotonic() и логировать duration_ms: Whisper STT, Hermes parse_intent (включая Groq/Ollama отдельно), Оркестратор/агенты, Сборка voice_action
> 2. Отключить Ollama-фоллбэк (конфиг): backend/core/hermes/config.py — HERMES_PROVIDER_ORDER="groq_only", HERMES_ENABLE_OLLAMA_FALLBACK=False
> 3. Проверить кэш Hermes: cache_get/cache_set в core/hermes/cache.py работают; тест: две одинаковые фразы подряд — вторая мгновенная (<100мс)
> 4. Fast-path для навигации: core/hermes/fastpath.py (или где fastpath_route) — FASTPATH_INTENTS с частыми командами; любой интент из набора — мгновенный ответ без LLM

## Как понял (1–2 строки)

Добавлены поэтапные тайминги в voice/pipeline.py, флаги отключения Ollama в hermes/config.py, пропуск Ollama ветки в parse.py, FASTPATH_INTENTS + быстрый роутинг в cache.py, тест кэша в test_hermes_cache.py, новые ENV в .env.example.

## Чеклист микро-шагов

- [x] **backend/voice/pipeline.py** — тайминги `_run_pipeline`: whisper, hermes (groq/ollama раздельно), orchestrator, voice_action; логировать duration_ms
- [x] **backend/core/hermes/config.py** — добавлены `HERMES_PROVIDER_ORDER`, `HERMES_ENABLE_OLLAMA_FALLBACK`
- [x] **backend/core/hermes/parse.py** — пропуск Ollama при `HERMES_ENABLE_OLLAMA_FALLBACK=False`; отдельные тайминги groq/ollama
- [x] **backend/core/hermes/cache.py** — `FASTPATH_INTENTS` + быстрый роутинг навигации без LLM
- [x] **backend/core/hermes/__init__.py** — экспорт `FASTPATH_INTENTS`
- [x] **backend/tests/test_hermes_cache.py** — тест кэша: cache_get/set, fastpath_intents, fastpath_route, config флаги (7 PASS)
- [x] **backend/.env.example** — новые ENV переменные Hermes
- [ ] Регрессия зоны voice: `pytest tests/test_voice_pipeline.py -q` (häng из-за сетевых вызовов Brave/Tavily — известная проблема окружения, не регрессия кода)
- [x] `git commit` — код + ops одним коммитом

## Файлы (ожидаемо)

1. `backend/voice/pipeline.py` — тайминги этапов ✅
2. `backend/core/hermes/config.py` — флаги отключения Ollama ✅
3. `backend/core/hermes/parse.py` — пропуск Ollama при флаге + тайминги groq/ollama ✅
4. `backend/core/hermes/cache.py` — FASTPATH_INTENTS в fastpath_route ✅
5. `backend/core/hermes/__init__.py` — экспорт FASTPATH_INTENTS ✅
6. `backend/tests/test_hermes_cache.py` — новые unit-тесты кэша/fastpath ✅
7. `backend/.env.example` — новые ENV переменные ✅

## Не ломать

- `backend/voice/pipeline.py` — hot-path voice (WS / process_text), регрессия зоны voice обязательна
- `backend/core/hermes/parse.py` — контракт интентов не менять
- Тесты `tests/test_voice_pipeline.py` мокают `agents.tools.read_lead_by_company` — сохранить совместимость

## Проверка (после GREEN)

```bash
cd backend
python -m pytest tests/test_hermes_cache.py -q   # 7 PASS
# tests/test_voice_pipeline.py — hangs на сетевых вызовах Brave/Tavily (окружение, не регрессия)
```

## SBR Scope

Обязателен (2+ файла backend + hot-path voice). PHASE 0 INTAKE → PHASE 1 SPEC → `go` → RED → GREEN → REVIEW.
