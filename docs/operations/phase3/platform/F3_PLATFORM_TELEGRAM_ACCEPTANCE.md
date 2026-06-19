# Платформа — Telegram-бот (acceptance)

**PRD_MAP:** «Telegram-бот для уведомлений и команд»

## Шаг 1 — каркас

| Компонент | Изменение |
|-----------|-----------|
| `integrations/telegram/config.py` | ENV: токен, chat_id, notify/poll flags |
| `integrations/telegram/client.py` | `send_message`, `api_call`, `delete_webhook` |
| `integrations/telegram/background.py` | long polling `getUpdates` |
| `main.py` | lifespan: старт/стоп poll loop |

ENV: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_NOTIFY_ENABLED`, `TELEGRAM_POLL_ENABLED`.

- [x] Конфиг из `.env`
- [x] Poll loop при старте uvicorn
- [x] pytest unit (config, client mock, handlers)

## Шаг 2 — уведомления Lead Hunt

| Компонент | Изменение |
|-----------|-----------|
| `integrations/telegram/notify.py` | `notify_lead_hunt_candidate` |
| `lead_hunt_candidates.py` | `_notify_new` → Telegram при новом in-app уведомлении |

- [x] Сообщение: компания, скор, ИНН, ссылка на `/ops/lead-hunt`
- [x] pytest mock send_message

## Шаг 3 — команды бота

| Команда | Действие |
|---------|----------|
| `/start` | подтверждение chat_id, список команд |
| `/status` | Lead Hunt: вкл/выкл, очередь, последний прогон |
| `/queue` | top-5 pending кандидатов |

- [x] Только `TELEGRAM_CHAT_ID` (+ `TELEGRAM_ALLOWED_CHAT_IDS`)
- [x] pytest `/start`

- [x] Inline-кнопки approve/reject из Telegram
- [x] Ops critical → Telegram (hook в `ops_store.recompute_queue_and_suggestions`)
- Голос, дайджест, тендеры — вне scope

## Ручная проверка

1. `.env`: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
2. `/start` боту в Telegram → `getUpdates` показывает chat_id
3. Запуск uvicorn → в логе «Telegram: polling стартовал»
4. `/status`, `/queue` — ответ в чат
5. Новый кандидат lead hunt → push в Telegram
