# DB — база данных

PostgreSQL через SQLAlchemy async. Схема создаётся при старте (`init_db` в `main.py`).

---

## Корень `db/`

| Файл | За что |
|------|--------|
| `session.py` | Подключение, `get_session`, `init_db` |
| `database.py` | Вспомогательные функции БД |

Переменная: `DATABASE_URL` в `.env`.

---

## Пакет `models/` — таблицы

| Файл | Таблица / сущность |
|------|-------------------|
| `lead.py` | Лид CRM (стадия, скор, поля) |
| `task.py` | Задачи по лиду |
| `user.py` | Пользователи |
| `email.py` | Настройки почты |
| `eval_scenario.py` | Сценарии eval |
| `training_dataset.py` | Датасеты обучения |
| `agent_run_log.py` | Логи запусков агентов |
| `agent_email_intent.py` | Интенты email-агента |
| `lead_comment.py` | Комментарии к лиду |
| `lead_communication_log.py` | Лог звонков/писем |
| `lead_field_audit.py` | История изменений полей |

Все модели регистрируются в `models/__init__.py`.
