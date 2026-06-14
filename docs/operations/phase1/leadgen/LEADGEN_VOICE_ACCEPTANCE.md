# Лидоген + голос — acceptance (2026-06-11)

PRD_MAP: **Ф2 §8** · статус **✅ закрыт** (live UI + lookalike).

## Что закрыто (smoke)

| Слой | Как |
|------|-----|
| Backend WS | `tests/smoke/test_leadgen_voice_ws.py` — navigate `/leadgen?inn=&autorun=1` |
| Live UI pipeline | `voiceLeadgenContext` + autorun → analyze/portrait на `/leadgen` |
| Lookalike won | `find_similar_clients` + `lookalike-import` + `GET /won-portrait` |

Полный acceptance Ф2: [`LEADGEN_VOICE_F2_ACCEPTANCE.md`](../../phase2/leadgen/LEADGEN_VOICE_F2_ACCEPTANCE.md)

## Команда

```bash
cd backend && python -m pytest tests/smoke/test_leadgen_voice_ws.py -q
```

## Хвост (закрыт в Ф2)

- [x] Live UI: голос на `/leadgen` → полный pipeline — см. `LEADGEN_VOICE_F2_ACCEPTANCE.md`
- [x] Lookalike из won-сделок + апрув менеджера — `find_similar_clients` + `lookalike-import`

## Связь MAP

- Очередь 5 → ⚠️ до закрытия хвостов выше
- DoD Ф2 п.5 → 🔲
