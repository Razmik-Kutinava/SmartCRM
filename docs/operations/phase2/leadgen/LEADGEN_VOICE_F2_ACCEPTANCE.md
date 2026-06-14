# §8 Лидоген + голос — acceptance (Ф2)

## Scope

Live UI pipeline на `/leadgen` по голосу + lookalike из won-сделок с апрувом.

## Команда

```powershell
cd backend
python -m pytest tests/api/test_leadgen_section8.py tests/smoke/test_leadgen_voice_ws.py tests/agents/scenarios/test_similar_clients.py tests/api/test_lookalike_import.py tests/smoke/test_voice_layer_ui.py -q
```

## Закрыто

| PRD_MAP | Что |
|---------|-----|
| WS audio → generate_lead | smoke `test_leadgen_voice_ws.py` — navigate `/leadgen?inn=&autorun=1` |
| Live UI + полный pipeline | `voiceLeadgenContext` + autorun на `/leadgen` → `/api/leadgen/analyze` или `/portrait` |
| Lookalike won + апрув | `find_similar_clients` → modal → `lookalike-import`; `GET /won-portrait`; кнопка на UI |

## Голос

- `generate_lead` → `/leadgen?mode=direct&inn=…&autorun=1`
- `find_leads_portrait` → `/leadgen?mode=portrait&portrait=…&autorun=1`
- `cluster_company` → `/leadgen?mode=cluster&inn=…&autorun=1`
- `find_similar_clients` → modal + «Добавить» → `POST /api/leads/lookalike-import`

## UI

- `/leadgen` — бейдж `voice-leadgen-context`, autorun pipeline
- «Профиль из выигранных сделок» — `leadgen-won-portrait-btn`
- Voice modal — `voice-lookalike-won` при source won_deals

## Связь

- Ф1 smoke: [`LEADGEN_VOICE_ACCEPTANCE.md`](../../phase1/leadgen/LEADGEN_VOICE_ACCEPTANCE.md)
- Lookalike сценарий: [`SCENARIO_SIMILAR_CLIENTS_ACCEPTANCE.md`](../agents/SCENARIO_SIMILAR_CLIENTS_ACCEPTANCE.md) (если есть) / `test_similar_clients.py`
