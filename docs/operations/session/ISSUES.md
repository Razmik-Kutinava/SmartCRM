# ISSUES

Журнал инцидентов и багов. Приоритеты: 🔴 блокер, 🟡 важно, 🟢 потом.

**Должки (R14):** открытая запись старше месяца — «должок»: агент показывает её пользователю в старте сессии и просит подтвердить закрытие или оставить. Закрывать — только после явного «да». Закрытые записи прошлых месяцев → `docs/archive/ops/YYYY-MM_ISSUES.md`.

Шаблон одной записи:

`[YYYY-MM-DD] — [название]`  
`Приоритет: 🔴/🟡/🟢 | Статус: открыта/в работе/закрыта`  
`Описание:[...] | Влияние:[...] | Решение:[...] | Агент:[...]`

---

`[2026-08-01] — test_leads_list_filters_labeled ищет tasks_urgent в +page.svelte`  
`Приоритет: 🟢 | Статус: открыта`  
`Описание: tests/smoke/test_leads_list_page.py::test_leads_list_filters_labeled — assert "tasks_urgent" in text; в /leads/list опция сортировки берётся из SORT_OPTIONS (leadListFilter.js), в самой странице строки нет. Падает и на чистом HEAD (git show HEAD:… — совпадений нет) | Влияние: ложный FAIL при точечном прогоне smoke списка; в зону crm_leads этот файл не входит | Решение: проверять SORT_OPTIONS в leadListFilter.js, а не текст страницы | Агент: найден при фиксе импорта CSV/Excel 2026-08-01`

`[2026-08-01] — два фронт-смоука красные на чистом HEAD`  
`Приоритет: 🟢 | Статус: открыта`  
`Описание: tests/frontend/test_lead_card_cache_resilience.py::test_leads_storage_has_memory_cache_on_quota — ищет слово «квота» в leadsStorage.js, в файле другое написание; tests/frontend/test_lead_mailing_ui.py::test_lead_mailing_ui_smoke — node:internal/modules/esm/resolve (нет зависимости для node-прогона). Оба падают после git stash всех правок | Влияние: шум при прогоне tests/frontend; в зону crm_leads не входят | Решение: поправить строку в assert и node-окружение смоука | Агент: найден при экране импорта базы 2026-08-01`

`[2026-08-01] — удалённый последний контакт «воскресает» из плоских полей`  
`Приоритет: 🟡 | Статус: открыта`  
`Описание: PATCH с contacts:[] чистит JSON, но contacts_for_api при пустом списке отдаёт legacy_to_contacts() из lead.contact/phone/email, которые flat_fields_from_lpr записал от прошлого ЛПР → в карточке снова один контакт. Проверено на лиде 846: отправили [], получили 1 | Влияние: пользователь удаляет контакт, после F5 он возвращается | Решение: различать None (никогда не сохраняли) и [] (явно очищено) в contacts_for_api + чистить плоские поля при пустом списке | Агент: найден при фиксе «третий контакт заменяет второй» 2026-08-01`

`[2026-07-21] — test_tasks_filter_done_and_combined падает (комбо-фильтр задач)`  
`Приоритет: 🟡 | Статус: открыта`  
`Описание: tests/api/test_tasks_api.py::test_tasks_filter_done_and_combined — assert "Смотрим сегодня" in titles → titles пуст (GET /api/tasks?task_status=open&due=today); падает и на чистом HEAD — вероятно, зависит от текущей даты/часового пояса при создании задачи | Влияние: ложный FAIL регрессии зоны crm_leads; не связан с шагом «база → рассылка по source» | Решение: разобрать генерацию due в тесте (freeze времени или задать дату явно) | Агент: найден при регрессии crm_leads 2026-07-21`

`[2026-07-21] — test_faq_autoreply_mocked зависит от окружения`  
`Приоритет: 🟡 | Статус: открыта`  
`Описание: tests/email/test_email_f3.py::test_faq_autoreply_mocked падает при EMAIL_FAQ_AUTOREPLY=0 / EMAIL_FAQ_MAX_PER_DAY=0 в корневом .env — сервис читает env, тест его не изолирует (monkeypatch нет) | Влияние: ложный FAIL регрессии зоны email на машинах с выключенным FAQ-автоответом; падает и на чистом HEAD — не связан с шагом «Ящики в UI» | Решение: добавить monkeypatch.setenv("EMAIL_FAQ_AUTOREPLY","1") и MAX_PER_DAY в тест | Агент: найден при регрессии зоны email 2026-07-21`

> Архив: [`docs/archive/ops/2026-05_ISSUES.md`](../../archive/ops/2026-05_ISSUES.md) · [`2026-06_ISSUES.md`](../../archive/ops/2026-06_ISSUES.md)
