# Email: анализ типа + черновик (Ф2 §3 п.405)

**PRD_MAP:** «Анализ типа письма + черновик (Маркетолог)»

## Цель

На `/email` в модалке треда: кнопка **«Анализ + черновик»** → тип письма (pricing/support/…) + черновик ответа от Маркетолога **без отправки**.

## Было

- `classify_email` только при IMAP-синке
- Черновик письма — через `POST /api/agents/email/run` на карточке лида, не в UI `/email`
- Голосовой сценарий `analyze_and_email` — отдельный flow

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `core/email_category_labels.py` | RU-метки для `classify_email` |
| `services/email_thread_analyze.py` | `analyze_email_thread`: rule-based тип + LLM маркетолог |
| `POST /api/email/threads/{id}/analyze` | API: `{ category, category_label, draft, agent, summary }` |
| `frontend/src/lib/emailStorage.js` | `analyzeEmailThread()` |
| `frontend/src/routes/email/+page.svelte` | Кнопка «Анализ + черновик», превью, «В ответ ↓» |

## API

```http
POST /api/email/threads/{thread_id}/analyze
Content-Type: application/json

{ "lead_id": 123 }  // опционально
```

Ответ:

```json
{
  "thread_id": 1,
  "category": "pricing",
  "category_label": "Прайс / коммерция",
  "agent": "marketer",
  "draft": { "subject": "Re: …", "body": "…" },
  "summary": "…",
  "value_hook": "…",
  "lead_id": 123
}
```

## UI

1. Открыть тред на `/email`
2. **«✨ Анализ + черновик»** — вызов API (mock LLM в CI)
3. Бейдж типа + превью черновика
4. **«В ответ ↓»** — подставить текст в textarea (апрув/отправка — п.406)

## Команды

```bash
cd backend
python -m pytest tests/api/test_email_thread_analyze.py -q
python -m pytest tests/api/test_email_threads_api.py tests/api/test_email_sync_api.py -q
```

## Критерии

- [x] `POST /threads/{id}/analyze` — category + draft, без автосенда
- [x] Rule-based `classify_email` + маркетолог `write_email`
- [x] UI: кнопка, тип, превью, «В ответ»
- [x] pytest с mock LLM (без live Groq)
- [x] Опц. `lead_id` в теле и из треда

## Не в scope

- п.406 — апрув и отправка после кнопки/голоса
- п.407 — голосовые команды email
