# Смоук голосовых сценариев — «Голос → лиды» (2026-06-08)

## Команда

```powershell
cd backend; python scripts/smoke_voice_lead_scenarios.py
```

Цепочка: **47 pytest** (сценарии S01–S09 + whisper + hermes + voice_action) + smoke_whisper + hermes_leads + voice_action + hermes_full.

## Матрица сценариев (langgraph / лиды)

| ID | Фраза | Intent | voice_action | pytest CPU | API live | UI DevTools |
|----|-------|--------|--------------|------------|----------|-------------|
| S01 | покажи горячих лидов | list_leads | filter | ✅ | ✅ | ✅ WS текст |
| S02 | создай лид АКМЕ… | create_lead | navigate | ✅ | ✅ | ⚠️ агенты медленно |
| S03 | смени этап… | update_lead | navigate | ✅ | — | — |
| S04 | удали лид… | delete_lead | approve | ✅ | ✅ | ⚠️ модал вручную |
| S05 | напоминалку… | create_task | navigate | ✅ | — | — |
| S06 | проанализируй лид… | analyze_lead | modal | ✅ | — | ⚠️ fanout 15–30с |
| S07 | история по лиду… | lead_history | modal | ✅ | — | — |
| S08 | стадии переговоры | list_leads | filter | ✅ | — | — |
| S09 | лидов из Москвы | list_leads | filter | ✅ | — | — |

**Легенда:** ✅ автомат / проверено · ⚠️ частично · — не гоняли в этом прогоне

## DevTools (2026-06-08, `localhost:5174/leads/list`)

| Проверка | Результат |
|----------|-----------|
| WS индикатор `ws` | ✅ |
| `POST /api/voice/command` ×3 (list/create/delete) | ✅ intent + voice_action |
| Текст в панели → Enter «горячих лидов» | ✅ ответ ✓, фильтр |
| Модалка approve (delete) через UI | ⚠️ автоматизация Enter нестабильна; API `ui:approve` OK |

## Блок PRD_MAP п.1–5 — итог

| # | Пункт | Статус |
|---|--------|--------|
| 1 | Whisper STT | ✅ |
| 2 | Hermes CRUD/стадия/задача | ✅ |
| 3 | voice_action UI | ✅ |
| 4 | Полные интенты | ✅ |
| 5 | Смоук сценариев | ✅ автомат; ⚠️ микрофон + UI approve |

## Хвост → BACKLOG (блок «Голос → лиды»)

См. `BACKLOG.md` § «Голос → лиды — сводный хвост».
