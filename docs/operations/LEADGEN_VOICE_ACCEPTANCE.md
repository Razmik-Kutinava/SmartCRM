# Лидоген + голос — acceptance (2026-06-11)

PRD_MAP: **Ф2 §8** · очередь **5** · статус **⚠️ smoke slice** (не полный live UI).

## Что закрыто (smoke)

| Слой | Как |
|------|-----|
| Backend WS | `tests/smoke/test_leadgen_voice_ws.py` — audio/text → `generate_lead` → `voice_action` navigate `/leadgen` |
| Связь mic E2E | общий WS-контракт с `VOICE_MIC_E2E_ACCEPTANCE.md` |

## Команда

```bash
cd backend && python -m pytest tests/smoke/test_leadgen_voice_ws.py -q
```

## Хвост (не в scope smoke)

- [ ] Live UI: голос на `/leadgen` → полный pipeline (портрет/ИНН, результаты, автосейв)
- [ ] Lookalike из won-сделок + апрув менеджера

## Связь MAP

- Очередь 5 → ⚠️ до закрытия хвостов выше
- DoD Ф2 п.5 → 🔲
