# Долг: layout кода (не ops)

**Статус:** отложено · **не блокер Ф2** · **go отдельно**

Операционка упакована в `docs/operations/` (2026-06-13). **Код** (`backend/`, `frontend/`) — по канону [`REPO_LAYOUT.md`](../../dev/REPO_LAYOUT.md), но legacy-монолиты и `backend/data/` ещё не приведены.

## Когда делать

После старта Ф2 по MAP — отдельный спринт «layout cleanup» с **`go`** на пакет из [`LAYOUT_AUDIT.md`](../../dev/LAYOUT_AUDIT.md).

## Пакеты (кандидаты)

| # | Что | Где смотреть |
|---|-----|--------------|
| 1 | Сплит файлов >200 строк | `LAYOUT_AUDIT.md` § монолиты |
| 2 | `.gitignore` runtime в `backend/data/` | дубли кэшей в git status |
| 3 | Новый код — только по REPO_LAYOUT | правило `smartcrm-repo-layout.mdc` |

## Не делать в этом долге

- Перенос `docs/product/`, `eval/` — вне scope
- Рефактор «ради красоты» без задачи MAP

Запись в BACKLOG: [`../session/BACKLOG.md`](../session/BACKLOG.md) — добавить при первом `go` на layout.
