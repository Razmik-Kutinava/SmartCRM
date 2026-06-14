# Email: апрув и отправка (Ф2 §3 п.406)

**PRD_MAP:** «Апрув и отправка (голос или кнопка)»

## Цель

Перед отправкой письма/ответа — подтверждение оператором (кнопка на `/email` или голосовой `send_email`).

## Было

- `/email`: «Ответить» и «Отправить» сразу вызывали SMTP без подтверждения
- Голос `send_email`: approve-модалка без превью черновика; только новое письмо, без reply в тред

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `EmailApproveModal.svelte` | Модалка: кому / тема / текст → Отправить / Отмена |
| `emailApproveLogic.js` | Превью для reply и compose |
| `/email` +page.svelte | Reply и compose → апрув → `POST /reply` или `/send` |
| `voiceApproveHandlers.js` | `thread_id` → `replyToEmail`; иначе `sendEmail` |
| `VoiceActionHost.svelte` | Превью `draft_email` в voice approve |

## UI `/email`

1. Написать ответ (или «В ответ ↓» после анализа)
2. **↑ Ответить** → модалка апрува
3. **Отправить** → SMTP + обновление треда

Аналогично для **Новое письмо**.

## Голос

- Intent `send_email`, `ui_action: approve`
- Confirm → отправка (новое письмо или reply при `slots.thread_id`)
- Превью черновика в модалке

## Команды

```bash
cd backend
python -m pytest tests/lib/test_email_approve_logic.py tests/smoke/test_email_approve_ui.py tests/api/test_email_thread_analyze.py -q --override-ini="filterwarnings="
```

## Критерии

- [x] Кнопка: апрув перед reply и compose на `/email`
- [x] Голос: `send_email` approve с превью draft
- [x] Reply в тред по `thread_id` из voice slots
- [x] pytest smoke + lib mirror зелёные

## Не в scope

- п.407 — голосовые команды email (list/navigate/write без send)
- E2E «голосом письмо → апрув → отправка» (отдельный пункт MAP Ф2)
