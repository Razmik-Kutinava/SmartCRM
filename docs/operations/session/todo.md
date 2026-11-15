# todo — микро-чеклист: ускорение голосового пайплайна

## Заказ (дословно)

> Сделать голос быстрее кнопок. Оператор не должен ждать >3 сек.
>
> 1. Логи таймингов (voice/pipeline.py): в _run_pipeline обернуть каждый этап в time.monotonic() и логировать duration_ms: Whisper STT, Hermes parse_intent (включая Groq/Ollama отдельно), Оркестратор/агенты, Сборка voice_action
> 2. Отключить Ollama-фоллбэк (конфиг): backend/core/hermes/config.py — HERMES_PROVIDER_ORDER="groq_only", HERMES_ENABLE_OLLAMA_FALLBACK=False
> 3. Проверить кэш Hermes: cache_get/cache_set в core/hermes/cache.py работают; тест: две одинаковые фразы подряд — вторая мгновенная (<100мс)
> 4. Fast-path для навигации: core/hermes/fastpath.py (или где fastpath_route) — FASTPATH_INTENTS с частыми командами; любой интент из набора — мгновенный ответ без LLM

## Как понял (1–2 строки)

Добавить поэтапные тайминги в voice/pipeline.py, выключить Ollama fallback в hermes/config.py, покрыть кэш Hermes тестом, расширить fastpath_route детерминированными навигационными интентами без LLM.

## Чеклист микро-шагов

- [ ] **backend/voice/pipeline.py** — тайминги `_run_pipeline`: whisper, hermes (groq/ollama раздельно), orchestrator, voice_action; логировать duration_ms
- [ ] **backend/core/hermes/config.py** — добавить `HERMES_PROVIDER_ORDER`, `HERMES_ENABLE_OLLAMA_FALLBACK`; по умолчанию groq_only, ollama выкл
- [ ] **backend/core/hermes/parse.py** — уважать флаги: отключить Ollama ветку при `HERMES_ENABLE_OLLAMA_FALLBACK=False`
- [ ] **backend/core/hermes/cache.py** — `fastpath_route`: добавить `FASTPATH_INTENTS` навигации; мгновенный возврат без LLM
- [ ] **backend/tests/test_voice_pipeline.py** — тест кэша: две одинаковые фразы → вторая <100мс (кэш hit)
- [ ] **backend/tests/test_hermes_cache.py** (новый) — unit-тесты cache_get/cache_set/fastpath_route
- [ ] **backend/.env.example** — добавить HERMES_PROVIDER_ORDER, HERMES_ENABLE_OLLAMA_FALLBACK
- [ ] Регрессия зоны voice: `pytest tests/test_voice_pipeline.py -q` + `run_zone_regression.py voice`
- [ ] `git commit` — `feat: ускорение голосового пайплайна — тайминги, только Groq, кэш Hermes, fast-path [GREEN]`

## Файлы (ожидаемо)

1. `backend/voice/pipeline.py` — тайминги этапов
2. `backend/core/hermes/config.py` — флаги отключения Ollama
3. `backend/core/hermes/parse.py` — пропуск Ollama при флаге
4. `backend/core/hermes/cache.py` — FASTPATH_INTENTS в fastpath_route
5. `backend/tests/test_voice_pipeline.py` — тест кэша
6. `backend/tests/test_hermes_cache.py` — новые unit-тесты кэша/fastpath
7. `backend/.env.example` — новые ENV переменные

## Не ломать

- `backend/voice/pipeline.py` — hot-path voice (WS / process_text), регрессия зоны voice обязательна
- `backend/core/hermes/parse.py` — контракт интентов не менять
- Тесты `tests/test_voice_pipeline.py` мокают `agents.tools.read_lead_by_company` — сохранить совместимость

## Проверка (после GREEN)

```bash
cd backend
python -m pytest tests/test_voice_pipeline.py tests/test_hermes_cache.py -q
python scripts/run_zone_regression.py voice
```

## SBR Scope

Обязателен (2+ файла backend + hot-path voice). PHASE 0 INTAKE → PHASE 1 SPEC → `go` → RED → GREEN → REVIEW.
