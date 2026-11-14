# /ctx-trim — оптимизация контекста и токенов

SmartCRM. Следуй **`.cursor/rules/workflow/smartcrm-context-hygiene.mdc`** целиком.

## Сделай

1. Прочитай `smartcrm-context-hygiene.mdc` (on-demand, не глотать другие workflow).
2. Выполни **чеклист** §1–6 (архив прошлого месяца если нужен).
3. Обнови `ctx_trim: YYYY-MM-DD` в шапках HANDOFF + SESSION_STATE.
4. **Анализ до/после** — таблица строк (и ~tok если оцениваешь: ~4 символа = 1 tok).
5. **`git commit`** + ops (SESSION_STATE, CHANGELOG, HANDOFF; ISSUES/BACKLOG если трогал).
6. **Не трогай код фич.** Зонную регрессию / A/B/C / push-по-go **не отменяй**.

## Weekly (авто-подсказка, не silent)

Если сегодня **пт–вс** и `ctx_trim` в HANDOFF старше 7 дней — в отчёте одна строка: «следующий trim рекомендован».  
На `/start` в те же дни — та же одна строка (не блокировать работу).

## Отчёт

Таблица Сделано | Не сделано · A/B/C · таблица анализа · `Коммит: <хеш>`

## Обязательно в конце

`Next: /start`
