# LLM — Groq + Ollama (Hermes и агенты)

## Два контура

1. **`core/llm.py` — чат агентов**  
   `model="auto"` → **Groq** (`GROQ_MODEL`, по умолчанию `llama-3.1-8b-instant`), при ошибке/лимите → **Ollama** (`OLLAMA_MODEL`).

2. **`core/hermes.py` — роутер интентов** — `parse_intent`  
   Возвращает строгий JSON: `intent`, `agents`, `slots`, `parallel`, `reply`.  
   Использует **Groq** и **Ollama** (не «только локально»): порядок задаётся `HERMES_ROUTING_POLICY` и наличием `GROQ_API_KEY`.

## Схема Hermes (упрощённо)

```text
Текст → [fastpath?] → [cache?] → [memory?]
              ↓
         Groq ИЛИ Ollama (по политике)
              ↓
         JSON parse → post_verify
              ↓
         при полном отказе → rescue (детерминированные правила)
```

- **`default`:** сначала Groq, затем цепочка Ollama (`HERMES_MODEL` → `HERMES_FALLBACK`).
- **`local_first`:** для коротких (≤120 симв.) и «низкорисковых» фраз (покажи/список/… — см. `_choose_provider`) — сначала Ollama, затем Groq.

## Модели (ориентир на прод-конфиг)

| Роль | Где задаётся | Типичное значение |
|------|----------------|-------------------|
| Groq для агентов | `GROQ_MODEL` | `llama-3.1-8b-instant` |
| Groq для Hermes | тот же `GROQ_MODEL` | как выше |
| Ollama для агентов | `OLLAMA_MODEL` | `qwen2.5:0.5b` |
| Hermes primary | `HERMES_MODEL` | `qwen2.5:0.5b` |
| Hermes fallback | `HERMES_FALLBACK` | `qwen2.5:3b` |

Полный список переменных — см. блок ниже. На **CPU-only** (например WSL ARM) GPU не используется: `HERMES_ENABLE_GPU_OFFLOAD=0`.

## Пример конфигурации `.env`

```env
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-8b-instant

OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b

HERMES_MODEL=qwen2.5:0.5b
HERMES_FALLBACK=qwen2.5:3b
HERMES_PROMPT_MODE=compact
HERMES_MAX_TOKENS=120

HERMES_ENABLE_FASTPATH=1
HERMES_ENABLE_POST_VERIFY=1
HERMES_ENABLE_CACHE=1
HERMES_CACHE_TTL_SEC=600
HERMES_ENABLE_MEMORY=0

HERMES_ENABLE_CONTEXT_COMPRESS=1
HERMES_COMPRESS_MAX_CHARS=2000
HERMES_ROUTING_POLICY=local_first
HERMES_PROMPT_PROFILE=

HERMES_OLLAMA_TIMEOUT_SEC=12
HERMES_OLLAMA_TOTAL_TIMEOUT_SEC=14
HERMES_OLLAMA_NUM_PREDICT=96

HERMES_ENABLE_CONTEXT_PROFILE=1
HERMES_OLLAMA_CTX_SHORT=2048
HERMES_OLLAMA_CTX_MEDIUM=4096
HERMES_OLLAMA_CTX_LONG=8192

HERMES_ENABLE_QUANT_MODEL=0
HERMES_MODEL_QUANT=qwen2.5:0.5b
HERMES_OLLAMA_KEEP_ALIVE=10m
HERMES_ENABLE_OLLAMA_PRELOAD=0

HERMES_ENABLE_GPU_OFFLOAD=0
HERMES_OLLAMA_NUM_GPU=99
HERMES_OLLAMA_NUM_THREAD=6
HERMES_ENABLE_CONTEXT_HYGIENE=1
```

## Оптимизация Hermes

- `HERMES_PROMPT_MODE=compact` — короткий системный промпт.
- `HERMES_MAX_TOKENS=120` — ограничение ответа роутера.
- `HERMES_ENABLE_FASTPATH` — детерминированный pre-router без LLM.
- `HERMES_ENABLE_POST_VERIFY` — правка типичных false-positive.
- `HERMES_ENABLE_CACHE` + `HERMES_CACHE_TTL_SEC` — кэш повторов.
- `HERMES_ENABLE_MEMORY=1` — SQLite `backend/data/agent_memory.sqlite3`.
- `HERMES_ENABLE_CONTEXT_COMPRESS` + `HERMES_COMPRESS_MAX_CHARS` — сжатие длинного ввода.
- `HERMES_PROMPT_PROFILE=compact-modular` — модульный профиль (`core/hermes_prompt_profiles.py`).
- `HERMES_ROUTING_POLICY=local_first` — см. раздел «Схема Hermes».
- `HERMES_OLLAMA_TIMEOUT_SEC` / `HERMES_OLLAMA_TOTAL_TIMEOUT_SEC` — защита от зависаний.
- `HERMES_ENABLE_CONTEXT_PROFILE` + `HERMES_OLLAMA_CTX_*` — динамический `num_ctx`; на CPU без GPU контекст дополнительно ограничивается в коде.
- `HERMES_ENABLE_QUANT_MODEL` + `HERMES_MODEL_QUANT` — опциональная квант-модель в цепочке.
- `HERMES_OLLAMA_KEEP_ALIVE` + `HERMES_ENABLE_OLLAMA_PRELOAD` — снижение cold-start.
- `HERMES_ENABLE_GPU_OFFLOAD` — имеет смысл на машине с GPU; на CPU оставлять `0`.
- `HERMES_ENABLE_CONTEXT_HYGIENE` — чистка URL/шума перед LLM.

### A/B-проверка одной командой

Из каталога `backend`:

```bash
python scripts/run_hermes_ab_check.py --status approved --models groq
```

### Поэтапный rollout фич Hermes

```bash
python scripts/run_hermes_parse_rollout.py --status all --repeat 3
```

Стадии включают `baseline`, `f1_context_profile`, … `f9_recommended_profile`. Отчёт: `accuracy`, `avg_ms`, `p95_ms`, `throughput_rps`, токены Groq.

### KPI gate

```bash
python scripts/hermes_kpi_gate.py --input data/parse_rollout_8features_r1.json
```

(`--input` — JSON от `run_hermes_parse_rollout.py`, поле `stages`.)

### Расширение eval из трейсов

```bash
python scripts/expand_eval_from_traces.py --limit 40 --status pending_review
```

---

## См. также

- Операционный обзор: `docs/start/RUNBOOK.md`
- Архитектура: `docs/product/ARCHITECTURE.md`
