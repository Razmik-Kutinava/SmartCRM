# todo — микро-чеклист: баг поиска «arman» в /leads/list

## Заказ (дословно)

> Баг: поиск «arman» в /leads/list показывает «АО СИТРОНИКС» первым, хотя в запросе Арман

## Как понял

Поиск по полю ПОИСК в /leads/list использует `leadMatchesSearchExact` с `hay.includes(q)` по всем полям (company|contact|description|city|industry|email|phone). Короткий запрос `arman` может попасть в description/контакт/email у «АО СИТРОНИКС» — и лид попадает в выдачу без «arman» в названии. После exact-фильтра `applyLeadListView` сортирует по баллу (Балл ↑), игнорируя релевантность, поэтому Ситроникс встаёт выше Арман Холдинг.

## Чеклист микро-шагов

- [x] Диагностика (до кода): зафиксировать, какое поле даёт ложный матч Ситроникс по `arman` (в отчёте)
- [x] `frontend/src/lib/leads/leadCompanyFuzzy.js`: взвешенный рейтинг при непустом search — компания ≫ контакт ≫ остальные поля
- [x] `frontend/src/lib/leads/leadCompanyFuzzy.js`: для коротких запросов (≤5 символов) не матчить `description` (и `phone`)
- [x] `frontend/src/lib/leads/leadListFilter.js`: `applyLeadListView` не давать score-сортировке убивать релевантность при непустом search (secondary sort = выбранная сортировка)
- [x] `backend/core/lead_company_fuzzy.py`: зеркало изменений алгоритма
- [x] `backend/tests/lib/test_lead_company_fuzzy.py`: RED→GREEN фикстура [Ситроникс без arman в company + шум в description; Арман Холдинг (arman-holding.com)] + query `arman` → первым Арман, Ситроникс не выше
- [x] Регрессия зоны `crm_leads` (pytest) — 39 PASS
- [ ] git commit + ops (код + ops одним коммитом) + ответ с хешем

## Файлы (ожидаемо)

- `frontend/src/lib/leads/leadCompanyFuzzy.js`
- `frontend/src/lib/leads/leadListFilter.js`
- `backend/core/lead_company_fuzzy.py`
- `backend/tests/lib/test_lead_company_fuzzy.py`

## Читать (только нужное)

- `frontend/src/lib/leads/leadCompanyFuzzy.js` — SEARCH_FIELDS, leadMatchesSearchExact, filterLeadsSearch
- `frontend/src/lib/leads/leadListFilter.js` — applyLeadListView, filterLeadsSearch, sortLeads
- `backend/core/lead_company_fuzzy.py` — зеркало алгоритма
- `docs/operations/phase4/leads/F4_LEAD_SEARCH_FUZZY.md` — спека exact/fuzzy

## Не ломать

- fuzzy целиком не отключать
- Hermes/voice pipeline не трогать (баг в фильтре списка)
- не «лечить» только сортировкой — убрать/ослабить ложный exact

## Статус

PHASE 2 GREEN. Ожидается коммит + ops.
