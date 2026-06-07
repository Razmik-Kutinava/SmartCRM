# API-слой

Всё, что отвечает на HTTP/WebSocket запросы от фронта.

## Структура

```
api/
└── routes/     ← все эндпоинты (см. routes/README.md)
```

Роуты **тонкие**: принимают запрос, валидируют, вызывают `core`, `agents`, `leadgen` или `db`, отдают JSON.

## Правила

- Новый эндпоинт → `api/routes/` (файл или подпакет по домену).
- Бизнес-логику не писать здесь — только в `core/` / `services/` / `leadgen/`.
- Префиксы URL: `/api/leads`, `/api/ops`, `/api/tenders` и т.д. (см. `main.py`).

Подробный список всех роутов: [`routes/README.md`](routes/README.md).
