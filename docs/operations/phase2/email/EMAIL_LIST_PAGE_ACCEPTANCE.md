# Email список `/email` — acceptance (Ф2 §3 п.404)

**PRD_MAP:** «Список `/email`»

## Было

- Страница `/email` была с Ф1, но фильтры/группировка inline в `+page.svelte`
- `GET /threads` без `isArchived` и `previewFrom` — архив и «от кого» в UI не работали
- Часть запросов через raw `fetch` без `X-API-Key`
- Нет индикатора фонового синка на странице

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `frontend/src/lib/email/emailListLogic.js` | папки, фильтр, группировка по дате, label фонового синка |
| `frontend/src/routes/email/+page.svelte` | lib + `apiFetch` helpers; фильтр ящика; sync status bar |
| `services/email_thread_list.py` | enriched threads: `isArchived`, `previewFrom` |
| `GET /api/email/threads` | список для UI с обогащёнными полями |
| `emailStorage.js` | `fetchEmailSyncStatus`, `fetchEmailConfigStatus` |

## UI `/email`

- Папки: входящие, отправленные, Zoho, рассылки, архив
- Поиск по теме / snippet / отправителю
- Группировка: сегодня / вчера / неделя / месяц
- Кнопка «Синхронизировать» + строка фонового синка
- Модал треда с перепиской и ответом
- Фильтр «Все ящики» при 2+ аккаунтах

## Команды

```bash
cd backend
pytest tests/api/test_email_threads_api.py tests/lib/test_email_list_logic.py tests/api/test_email_sync_api.py -q
```

## Критерии

- [x] Маршрут `/email` в навигации, список тредов из API
- [x] Фильтры папок + поиск + группировка по дате
- [x] `isArchived` / `previewFrom` с бэкенда
- [x] pytest зелёный (13+ в зоне email list)
- [x] API-ключ через `emailStorage` / `apiFetch`

## Не в scope

- Черновик/апрув (п.405–407)

## Cleanup 2026-06-14

- [x] Удалён legacy `email/[mailbox].svelte` — канон `/email` → `+page.svelte`
- [x] BACKLOG `me@agneko.am` снят (пароль уже в `.env`)
