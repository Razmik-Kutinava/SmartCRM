# HANDOFF

`Спринт:[Ф3] | Задача:[Quality gate tuning — шаг 3 live] | Статус: 🔄 in_progress — фоновый прогон`

**2026-06-17:** старт **live full gate** Ollama (не enrich smoke).

| Параметр | Значение |
|----------|----------|
| Команда | `run_agents_quality_gate.py --write-acceptance --log-file …` |
| Timeout | `EVAL_OLLAMA_TIMEOUT=3600` |
| Модель | `hermes3:latest` |
| Лог | `backend/data/artifacts/eval/gate_live_20260617_152400.log` |
| Backend | `:8000` OK, `SMARTCRM_API_KEY` loaded |

**Найдено при старте:** `Tee-Object` + `--log-file` на один путь → file lock; перезапуск без Tee.

**Дальше:** тейл лога → fail-кейсы → fix prompt/rescue → commit+ops пакетами → повтор до всех ≥85% live → `[x]` MAP после «ок».

---

`Спринт:[Ф3] | Задача:[Quality gate tuning — шаг 2] | Статус: ✅ done`

**2026-06-16:** Ф3 gate шаг 2 — rescue 36/36, enrich smoke 100%. **Коммит:** `dc1220c`.

---

`Спринт:[Ф3] | Задача:[Quality gate tuning — шаг 1] | Статус: ✅ done`

**2026-06-16:** шаг 1 — порог 85%, parse_intent, enrich tech/econ/strategist. **Коммит:** `6efd107`.
