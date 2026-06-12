# PR checklist (backend)

Перед merge в `main`:

- [ ] **Тест на фичу** — минимум 1 pytest на happy path изменённого модуля (`backend/tests/`, зеркало кода)
- [ ] `cd backend && python -m pytest -q` — зелёный локально
- [ ] CI: `pytest (sqlite)` + `smoke (ops / leads / voice)` — зелёные (required на `main`)
- [ ] Новый HTTP-роут — строка в `backend/api/routes/README.md` (если менялся API)
- [ ] Coverage **не gate** — но не добавлять большие куски без тестов в `leadgen` / `email_sync` / `integrations`

Live (`live_eval`, IMAP live, Bitrix webhook) — вне CI, только с ключами и `*_LIVE=1`.
