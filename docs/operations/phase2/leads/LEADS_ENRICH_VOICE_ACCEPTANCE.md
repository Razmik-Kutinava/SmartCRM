# §9 Лиды + enrich — голос (Ф2)

## Scope

Голос «обогати лид …» → тот же `enrich-lead` пайплайн → modal preview → апрув → PATCH карточки.

## Команда

```powershell
cd backend
python -m pytest tests/voice/test_enrich_voice.py tests/lib/test_enrich_lead_apply.py tests/api/test_search_enrich_lead_api.py -q
```

## Закрыто

| Шаг | Поведение |
|-----|-----------|
| Rescue | `обогати лид «Компания»` → `enrich_lead` / modal / module leads |
| Pipeline | `fetch_enrich_preview` — enrich без orchestrator |
| voice_action | route `/leads/{id}`, payload `scenario=enrich_lead`, actions `apply/reject` |
| UI | `VoiceActionHost` — `voice-enrich-preview`, кнопка «Применить в карточку» |

## Голос (примеры)

- «обогати лид Ромашка»
- «обогати карточку #12»
- «дополни контакты компании «Альфа»»

## DevTools

1. `/leads` — открыть карточку с company
2. Текст в voice bar: `обогати лид <компания>`
3. Modal с полями → «Применить в карточку»

## Связь

- Кнопка на карточке: [`LEADS_CARD_ENRICH_ACCEPTANCE.md`](LEADS_CARD_ENRICH_ACCEPTANCE.md)
- Enrich API: [`SEARCH_ENRICH_LEAD_ACCEPTANCE.md`](../rag/SEARCH_ENRICH_LEAD_ACCEPTANCE.md) (phase1)
