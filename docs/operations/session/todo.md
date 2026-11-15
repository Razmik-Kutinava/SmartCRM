# todo — микро-чеклист: «открой третий» после «найди лид» → «Лид не найден»

## Заказ (дословно)

> когда я говорю найди лид вроде все норм но потом когда выпадает список я даю еще команду открой лид третий пятый и тд и это не срабатывает … пишет лид не найден … надо устранить этот баг

## Как понял (1–2 строки)

После поиска список на экране запоминается во фронте (`voiceLeadFocus`), но `resolveVoiceOpenLeadId` игнорировал `selected_index` — «открой третий» не брал 3-й из этого списка. Плюс open_lead затирал список одним лидом.

## Чеклист микро-шагов

- [x] `frontend/src/lib/voice/voiceLeadFocus.js` — `selected_index` → `focus.leads[idx]` (раньше lead_id)
- [x] `frontend/src/lib/voice/voiceAction.js` — не затирать список при open; понятный toast
- [x] `frontend/src/routes/leads/list/+page.svelte` — findLead + open_lead по selected_index
- [x] `backend/voice/voice_action.py` — payload.selected_index
- [x] бэк: id|lead_id в pipeline/slot_normalize/rescue
- [x] тесты 94 PASS (voice+frontend)
- [ ] git commit + ops
