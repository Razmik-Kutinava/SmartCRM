# todo — микро-чеклист текущей фичи

> Макро: [`CHECKLIST_F4`](../phase4/CHECKLIST_F4.md) · [`F4_LEADS_CARD`](../phase4/leads/F4_LEADS_CARD.md)

## Заказ (дословно)

> «исполльзуй sbr и продис по пунктам и все сделай я запушу сам иссеование и посмотрю что добавитлось в паспортае ебашь»

**Как понял:** SBR: 🔍 исследование должно заполнять паспорт (почта, телефоны, контакты, отрасль и почти всё остальное) через extract + merge; пользователь сам прогонит 🔍.

## Чеклист (SBR)

### PHASE 1 SPEC
- [x] Заказ в todo + пункт чеклиста / спека
- [ ] `go` → BUILD (есть: «ебашь»)

### PHASE 2 BUILD
- [ ] RED: тесты extract→passport / merge contacts
- [ ] GREEN: `research_passport.py` + wire в `research_lead` + фронт patch
- [ ] Regex + LLM JSON (Groq→Ollama): phones, emails, contacts, industry…
- [ ] Merge без затирания Checko/уже заполненного
- [ ] `researchResultToLeadPatch` пишет contacts/industry/phone/email в лид

### PHASE 3 REVIEW
- [ ] Регрессия rag + тесты
- [ ] Ops + commit
