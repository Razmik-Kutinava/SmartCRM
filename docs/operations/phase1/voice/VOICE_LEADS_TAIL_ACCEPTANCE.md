# Acceptance — хвост «Голос → лиды» (2026-06-08)

Закрыто агентом (кроме **#1 E2E микрофон** — вручную пользователем).

| # | Пункт | Статус | Проверка |
|---|--------|--------|----------|
| 1 | E2E микрофон → Whisper → UI | 👤 пользователь | `WHISPER_STT_ACCEPTANCE.md` |
| 2 | UI approve delete автотест | ✅ | `data-testid` + `tests/smoke/test_voice_approve_ui.py`; Playwright при `SMOKE_UI=1` |
| 3 | Индикатор fanout analyze/create | ✅ | `+layout.svelte` — «Агенты анализируют…» |
| 4 | `add_communication` голосом | ✅ | rescue + `list/+page.svelte` → API comments/communications |
| 5 | Fuzzy stage ↔ crm_settings | ✅ | `core/hermes/stage_fuzzy.py` |
| 6 | Чипы industry/city | ✅ | чипы в фильтрах списка лидов |
| 7 | LLM eval analyze/history/comm | ✅ | `eval-034`…`036` + CPU rescue тесты |
| 8 | Flaky eval-003/020 | ✅ | `_extract_company`, phone regex, `slots_match` field |
| 9 | create_lead fanout live | ✅ | `scripts/smoke_hermes_leads_live.py` (skip без GROQ) |
| 10 | health_check Whisper ping | ✅ | `GET /health/whisper?ping=1` |
| 11 | email `@field_validator` | ✅ | `api/routes/email.py` |

**Команды:**

```bash
cd backend
python -m pytest tests/smoke/test_voice_lead_scenarios.py tests/core/hermes/ -q
python scripts/smoke_voice_lead_scenarios.py
# live fanout (опционально):
GROQ_API_KEY=... python scripts/smoke_hermes_leads_live.py
curl "http://127.0.0.1:8000/health/whisper?ping=1"
```
