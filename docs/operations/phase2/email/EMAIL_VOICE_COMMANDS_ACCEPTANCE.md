# Email: голосовые команды (Ф2 §3 п.407)

**PRD_MAP:** «Голосовые команды email»

## Цель

Три голосовых интента email работают end-to-end: **list_emails**, **write_email**, **send_email** (с апрувом п.406).

## Команды (примеры)

| Голос | intent | UI |
|-------|--------|-----|
| «открой входящие письма» | list_emails | navigate → `/email` + папка |
| «покажи отправленные письма» | list_emails | folder=sent |
| «напиши письмо клиенту …» | write_email | modal + черновик маркетолога |
| «отправь письмо на …» | send_email | approve → SMTP |

## Сделано

| Компонент | Изменение |
|-----------|-----------|
| `voice/email_context.py` | folder/search payload для list_emails |
| `orchestrator._run_write_email` | `marketer._analyze("write_email")` |
| `rescue.py` | слоты target/topic/filter для email |
| `voiceAction.js` | store `voiceEmailContext` |
| `/email` +page.svelte | подписка на folder/search с голоса |
| `VoiceActionHost` | «Отправить» в modal → approve (не автосенд) |

## Команды pytest

```bash
cd backend
python -m pytest tests/voice/test_email_voice_commands.py tests/lib/test_email_voice_context.py tests/voice/test_voice_action.py -q --override-ini="filterwarnings="
```

## Критерии

- [x] list_emails → `/email` + папка (inbox/sent/archive)
- [x] write_email → маркетолог + modal + route `/email`
- [x] send_email → approve с draft_email
- [x] Modal «Отправить» → очередь approve (п.406)
- [x] pytest без live LLM

## Не в scope

- E2E mic «голосом письмо → апрув → отправка» (отдельный пункт MAP Ф2)
- sync_emails голосом
- unread как отдельная папка (hint → inbox)
