# Full quality gate — фоновый прогон (~4 ч)

> **Когда:** уходите на 3–4+ часа (кафе, ноутбук включён, не спит).  
> **Не блокирует Ф2** — можно параллельно работать над MAP.  
> **Цель:** один полный live-прогон всех **111** кейсов (Hermes 36 + 5×15 агентов) → JSON + лог → при green обновить acceptance.

---

## Перед стартом (5 мин)

1. **Ollama**
   ```powershell
   ollama serve
   ollama pull hermes3:latest
   ```

2. **Backend** (отдельное окно терминала — агенты ходят в API)
   ```powershell
   cd c:\Tools\workarea\SmartCRM\backend
   uvicorn main:app --port 8000
   ```
   Если порт занят — освободить или сменить порт в `.env` / конфиге API клиента агентов.

3. **`.env`** в корне репо: `SMARTCRM_API_KEY` задан (иначе agents → 401).

4. **Smoke** (опционально, 1 мин):
   ```powershell
   cd c:\Tools\workarea\SmartCRM\backend
   python scripts/run_agents_quality_gate.py --check-only
   python scripts/run_agents_quality_gate.py --hermes-limit 1 --agent-limit 1 --log-file data/artifacts/eval/gate_smoke.log
   ```

5. **Питание ноутбука:** режим «не спать при питании от сети»; лучше от розетки.

---

## Full gate в фоне (основная команда)

**Окно 1** — backend (см. выше).  
**Окно 2** — прогон:

```powershell
cd c:\Tools\workarea\SmartCRM\backend
$env:EVAL_OLLAMA_TIMEOUT = "3600"
$env:OLLAMA_CHAT_TIMEOUT = "3600"
$env:GROQ_API_KEY = ""
$log = "data/artifacts/eval/gate_live_$(Get-Date -Format yyyyMMdd_HHmmss).log"
python -u scripts/run_agents_quality_gate.py `
  --log-file $log `
  --write-acceptance
```

> **Не** дублировать вывод в тот же файл через `Tee-Object` — скрипт сам пишет в `--log-file`, иначе file lock на Windows.

Замените `YYYYMMDD` на дату (например `gate_full_20260608.log`).

**Время:** на CPU обычно **2–4 ч**; на слабом железе может дольше — это нормально, пусть крутится.

**Фон через PowerShell** (можно закрыть текущее окно, процесс останется):

```powershell
cd c:\Tools\workarea\SmartCRM\backend
$log = "data/artifacts/eval/gate_full_$(Get-Date -Format yyyyMMdd_HHmm).log"
Start-Process powershell -ArgumentList @(
  '-NoExit',
  '-Command',
  "cd c:\Tools\workarea\SmartCRM\backend; `$env:EVAL_OLLAMA_TIMEOUT='1200'; `$env:OLLAMA_CHAT_TIMEOUT='1200'; python -u scripts/run_agents_quality_gate.py --log-file $log --write-acceptance"
)
```

---

## После возвращения

| Проверить | Где |
|-----------|-----|
| Процесс завершился | Окно PowerShell / `Overall gate: pass\|warn\|fail` в конце лога |
| Артефакт | `backend/data/artifacts/eval/agents_gate_*.json` (последний по времени) |
| Лог | `backend/data/artifacts/eval/gate_full_*.log` |
| Acceptance | `docs/operations/phase2/agents/AGENTS_QUALITY_GATE_ACCEPTANCE.md` (если был `--write-acceptance`) |
| UI | `/ops/intents/eval` → вкладка Quality gate |

**Если `overall_gate: pass` (или warn по политике):** сказать агенту «ок» → `[x]` в [`PRD_MAP`](../../../product/PRD_MAP.md) (строка quality gates).  
**Если `fail`:** смотреть gaps в JSON и `/ops/insights` → тюнинг промптов → новый прогон. **Ф2 не стопорится.**

---

## Частые проблемы

| Симптом | Действие |
|---------|----------|
| ReadTimeout / оборвался на Hermes | Увеличить timeout: `$env:EVAL_OLLAMA_TIMEOUT="1800"` |
| Agents 401 | Проверить `SMARTCRM_API_KEY` + backend на :8000 |
| Порт 8000 занят | `netstat -ano \| findstr :8000` → освободить процесс |
| Нет JSON после «завершения» | Прогон упал — смотреть хвост лога, запустить заново |
| Только Hermes или только 5 агентов | `--hermes-only` / `--agents-only` (для догона после обрыва) |

---

## Ссылки

- Пороги и таблица: [`AGENTS_QUALITY_GATE_ACCEPTANCE.md`](AGENTS_QUALITY_GATE_ACCEPTANCE.md)
- Карта обучения: [`AGENTS_LEARNING_MAP.md`](AGENTS_LEARNING_MAP.md)
- Вход в Ф2: [`../../session/PHASE2_ENTRY.md`](../../session/PHASE2_ENTRY.md)
