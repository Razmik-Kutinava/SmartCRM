# /spec — PHASE 1 SPEC

SmartCRM SBR. Канон: `spec-build-review.mdc` § PHASE 0–1, `smartcrm-task-workflow.mdc`.

## Сделай

1. Убедись: PHASE 0 — заказ **дословно** в `todo.md` + «Как понял».
2. Обнови `docs/operations/session/todo.md`: микро-чеклист + галочки.
3. Секция **«Файлы (ожидаемо)»** — **2–7 точных путей** + зачем каждый.
4. Секция **«Читать»** — только нужные § docs/zone-notes (не весь PRD/чеклист). Бюджет: Grep `^##` → Read offset/limit; файл >150 строк — не целиком.
5. **`explore`:** только если пути реально неясны после 1–2 узких поисков (1 раз). Иначе `нет — пути ясны`. Не «на всякий».
6. Hot-path (`orchestrator` / `voice` / `hermes` / `leadgen pipeline` / `db/session`) — в todo **обязательно**:
   ```
   ## Не ломать
   - … (2–4 пункта)
   ## Проверка
   - python -m pytest …   # 1–2 команды из smartcrm-dev-gates
   ```
   Без этих секций SPEC неполный — не звать `/sbr`.
7. ZONE_NOTES: если задача трогает зону — прочитать **только** `## <зона>` в `docs/operations/phase4/ZONE_NOTES.md`.
8. Обнови **только шапки** SESSION_STATE (без полного CHANGELOG/HANDOFF).
9. **Не** пиши код и не RED (если в том же сообщении нет «ебашь» / «сразу sbr» / `go` на BUILD).

## Отчёт

Сделано | Не сделано + файлы + Читать + Не ломать/Проверка (если hot-path).  
Стоп до `go` / `ебашь` (если не сказали «до конца»).

## Обязательно в конце

`Next: /sbr`
