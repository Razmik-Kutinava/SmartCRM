# Ф3 Voice — голосовой апрув и история

**PRD_MAP:** Фаза 3 → Voice (3 пункта).

## Критерии

| # | Пункт MAP | Проверка |
|---|-----------|----------|
| 1 | Подтверждение голосом («да, отправляй» / «нет») | При открытой модалке approve: голос/текст «да» → `resolveVoiceApprove('confirm')`; «нет» → reject. `data-testid="voice-approve-hint"`. |
| 2 | «Переделай короче» голосом | При модалке с `draft_email`: «короче» → `POST /api/voice/revise-draft`, черновик обновляется без закрытия. `data-testid="voice-revise-hint"`. |
| 3 | История команд Ops → Voice | `GET /api/ops/voice/history` + таблица на `/ops/voice`. `data-testid="voice-history-table"`. |

## Автотесты

```bash
cd backend
python -m pytest tests/voice/test_voice_f3_followup.py tests/test_voice_pipeline.py -q
python -m pytest tests/smoke/test_voice_approve_ui.py -q
```

## Ручной смоук

1. Вызвать интент с approve (удаление лида / отправка письма).
2. Сказать «да, отправляй» или ввести в текстовое поле голоса — модалка закрывается, действие выполняется.
3. Открыть черновик письма в modal → «переделай короче» — текст короче.
4. `/ops/voice` — блок «История голосовых команд» показывает traces.

## Файлы

- `frontend/src/lib/voice/voiceFollowup.js` — перехват да/нет/короче
- `frontend/src/lib/voice/voiceReviseDraft.js` — клиент revise API
- `backend/voice/approval_followup.py`, `revise_draft.py`
- `POST /api/voice/revise-draft`, `GET /api/ops/voice/history`
