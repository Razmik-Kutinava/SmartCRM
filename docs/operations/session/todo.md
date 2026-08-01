# todo — микро-чеклист текущей фичи

## Заказ (дословно)

> «итак у нас есть ли какие проблемы тут?
> … Три независимые дырки…
> будем делать ? …
> ебашь как задачу сбр все сделай»

**Как понял:** закрыть три дырки почты через SBR целиком — UF→passport, lead.email→ЛПР, research emails в контакты.

## Чеклист фазы

- [ ] **🔍 Исследовать / паспорт:** почта из UF + lead.email + веб → company.emails / ЛПР · [`CHECKLIST_F4.md`](../phase4/CHECKLIST_F4.md) · «🔍 Исследовать»

## PHASE 1 SPEC

1. **UF → company.emails** — regex по `bitrix_extra` (+ tech UF); валидные адреса в `checko.company.emails` на чтении API (без сети, сразу на старых лидах).
2. **lead.email → ЛПР** — в `mergePassportContacts` при enrich/research: если у ЛПР emails пусто, а `lead.email` / company.emails есть — дописать.
3. **🔍 как источник** — не склеивать с «Обогатить»; research уже regex-ит email; добить apply так, чтобы найденные emails попадали в ЛПР (тот же merge).
4. Security: только валидные email (`local@domain.tld`); `@x5.ru` без local — отбрасывать. Без raw SQL.
5. Тесты: backend extract + to_dict; фронт-контракт merge.

## Чеклист микро

- [ ] RED: тесты 3 дырок падают
- [ ] GREEN п.1: `emails_from_bitrix_blobs` + merge в `Lead.to_dict` / checko
- [ ] GREEN п.2: `mergePassportContacts` заполняет ЛПР из lead.email / company.emails
- [ ] GREEN п.3: research apply через тот же merge (контракт)
- [ ] Регрессия crm_leads / rag + REVIEW
