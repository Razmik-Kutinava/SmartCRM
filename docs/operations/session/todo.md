# todo — микро-чеклист текущей фичи

## Заказ (дословно)

> «итак у нас есть ли какие проблемы тут?
> … Три независимые дырки…
> будем делать ? …
> ебашь как задачу сбр все сделай»

**Как понял:** закрыть три дырки почты через SBR целиком — UF→passport, lead.email→ЛПР, research emails в контакты.

## Чеклист фазы

- [ ] **🔍 Исследовать / паспорт:** почта из UF + lead.email + веб → company.emails / ЛПР · [`CHECKLIST_F4.md`](../phase4/CHECKLIST_F4.md) · «🔍 Исследовать» (пункт чеклиста `[x]` — после «ок»)

## Чеклист микро

- [x] RED: `test_email_passport_holes` 6 FAIL / 1 PASS · коммит `d0cc4fa`
- [x] GREEN п.1: `emails_from_bitrix_blobs` + `merge_uf_emails_into_checko` + `Lead.to_dict`
- [x] GREEN п.2: `mergePassportContacts(..., lead)` — spareEmails → ЛПР при пустых emails
- [x] GREEN п.3: research apply через `enrichResultToLeadPatch` (тот же merge)
- [x] Регрессия: rag 134 PASS; crm_leads 111 PASS + 1 известный FAIL
