# Email — фича SmartCRM

## Что реализовано

### Подключение почты
- Yandex Mail через IMAP/SMTP (библиотеки `imap_tools` + `aiosmtplib`)
- Требует App Password (не основной пароль аккаунта)
- Настройки хранятся в `backend/config.py` (env-переменные `IMAP_*`, `SMTP_*`)

### Синхронизация писем
- `GET /api/email/sync` — загружает письма с IMAP-сервера в БД
- Таблица `email_messages`, модель `backend/db/models/email.py`
- Поля: `message_id`, `thread_id`, `subject`, `from_email`, `to_email`, `body`, `date`, `folder`, `is_read`, `is_archived`, `is_outbound`
- Треды группируются по `thread_id`

### Привязка писем к лидам
- `lead_id` (FK на `leads`) в таблице `email_messages`
- `GET /api/email/threads?lead_id={id}` — треды конкретного лида
- Привязка идёт по совпадению email лида с `from_email`/`to_email`

### API маршруты (`backend/api/routes/email.py`)
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/email/threads` | Список тредов (фильтр: lead_id, folder, search) |
| GET | `/api/email/threads/{id}/messages` | Сообщения треда |
| POST | `/api/email/send` | Отправить письмо |
| POST | `/api/email/archive` | Архивировать письмо |
| GET | `/api/email/sync` | Синхронизировать с IMAP |

### UI — страница почты (`/email`)
Макет в стиле Яндекс Почты:
- **Левый сайдбар**: кнопки «Написать» / «Настройки», папки (Входящие, Отправленные, Zoho, Рассылки, Архив), счётчики непрочитанных
- **Правая панель**: поиск, письма сгруппированные по дате (Сегодня / Вчера / На этой неделе / Месяц Год)
- **Тред-модал**: диалог с пузырьками (входящие слева, исходящие справа), инлайн-ответ
- **Compose-модал**: новое письмо или ответ с предзаполнением
- **Настройки-модал**: подключение почты
- **Zoho-папка**: фильтрует по ключевым словам Zoho в теме/сниппете

### UI — страница лида (`/leads/[id]`, вкладка «Почта»)
- Показывает треды лида, загружаемые лениво при переключении вкладки
- Клик по треду → модал с историей переписки
- Кнопка «Написать» — compose с предзаполненным email лида
- Инлайн-ответ прямо из треда

---

## Агенты на почте

### Интенты (`backend/db/models/agent_email_intent.py`)
Таблица `agent_email_intents` — настраиваемые правила поведения агента:
- `agent_name` — к какому агенту относится правило
- `intent_name` — название ситуации (напр. «Клиент молчит 7 дней»)
- `trigger_keywords` — ключевые слова-триггеры
- `action_template` — что делать агенту
- `priority`, `is_active`

Управляется через Ops → Агенты почты (`/ops/email-agents`)

### Запуск агента (`POST /api/agents/email/run`)
1. Загружает лида из БД
2. Читает последние 5 тредов лида (по 10 писем)
3. Загружает активные интенты для данного агента
4. Загружает few-shot примеры из `AgentRunLog`
5. Собирает всё в промпт → вызывает агента
6. Сохраняет результат в `agent_run_logs`

### Feedback & Few-shot (`backend/db/models/agent_run_log.py`)
Таблица `agent_run_logs`:
- Каждый запуск агента пишется в лог
- Пользователь ставит 👍/👎 на странице лида
- 👍 → `is_few_shot=True` → при следующих запусках инжектируется в промпт
- Статистика и управление few-shot в Ops → Агенты почты

### API агентов (`backend/api/routes/agent_email.py`)
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/agents/email-intents` | Список интентов |
| POST | `/api/agents/email-intents` | Создать интент |
| PUT | `/api/agents/email-intents/{id}` | Обновить интент |
| DELETE | `/api/agents/email-intents/{id}` | Удалить интент |
| POST | `/api/agents/email/run` | Запустить агента |
| POST | `/api/agents/email/feedback` | Сохранить 👍/👎 |
| GET | `/api/agents/email/history/{lead_id}` | История запусков по лиду |
| GET | `/api/agents/email/few-shots` | Все few-shot примеры |
| POST | `/api/agents/email/few-shots` | Пометить запуск как few-shot |
| DELETE | `/api/agents/email/few-shots/{run_id}` | Снять метку few-shot |
| GET | `/api/agents/email/stats` | Статистика feedback по агентам |

---

## DB-миграции

Добавляются автоматически при старте в `backend/db/session.py → init_db()`:
```sql
ALTER TABLE email_messages ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;
```
