# Ф4 — Email (тюнинг после Ф2–Ф3)

**Откуда:** Ф2 закрыл ассистирующий режим (IMAP, `/email`, черновик, апрув, голос). Ф3 — автономию (FAQ, рассылки, nurture 20 касаний, автолинк).  
**Зачем Ф4:** довести почту до **операционного MVP** — без `.env` для менеджера, антиспам, LLM-nurture на полную цепочку, паритет UI карточки и `/email`, аудит перед продом.

**База:**
- Ф1: [`EMAIL_CONNECT_ACCEPTANCE.md`](../../phase1/email/EMAIL_CONNECT_ACCEPTANCE.md)
- Ф2: [`EMAIL_IMAP_SMTP_ENV_ACCEPTANCE.md`](../../phase2/email/EMAIL_IMAP_SMTP_ENV_ACCEPTANCE.md) и соседние `EMAIL_*_ACCEPTANCE.md`
- Ф3: [`F3_EMAIL_AUTONOMY_ACCEPTANCE.md`](../../phase3/email/F3_EMAIL_AUTONOMY_ACCEPTANCE.md)
- Модуль nurture: [`docs/modules/email_nurture.md`](../../../modules/email_nurture.md)

**PRD_MAP:** Фаза 4 → Email (тюнинг).

---

## Критичные пробелы после Ф3

| # | Проблема | Почему критично |
|---|----------|-----------------|
| 1 | Ящики только через `.env` / bootstrap | Менеджер не подключит почту сам |
| 2 | Нет лимита отправок/день | Риск спама при nurture + campaigns |
| 3 | LLM-nurture — пилот 3 письма, не 20 | Цепочка касаний не дотянута до PRD |
| 4 | Карточка лида и `/email` — разный UX | Оператор живёт в карточке, функции разъехались |
| 5 | Нет аудита «кто отправил» | Блокер перед мульти-пользователем и продом |
| 6 | PII email в логах/traces | Сквозной Ф2, не закрыт для почты |

---

## План Ф4 (чеклист)

### A. Подключение без `.env`

- [ ] UI добавления ящика: `/email` → Настройки или секция в `/ops/integrations`
- [ ] Тест IMAP + SMTP из формы; статус: подключён / ошибка / токен истёк
- [ ] Шифрование пароля at rest (как у CRM credentials)
- [ ] Bootstrap из env остаётся, но не единственный путь

### B. Лимиты и антиспам

- [ ] Счётчик исходящих/день (SMTP + nurture + campaigns + FAQ)
- [ ] Warn / block перед `send_now` и массовой рассылкой
- [ ] Лимит FAQ auto-reply настраивается в `/ops/email-agents` (не только env)

### C. Nurture и рассылки

- [ ] LLM-цепочка на все **20** касаний (`start-llm`; сейчас пилот 3)
- [ ] Апрув превью цепочки перед стартом по сегменту
- [ ] Пауза nurture при inbound-ответе клиента — smoke на живом ящике
- [ ] История кампаний и цепочек: фильтры, статус шагов

### D. Карточка лида и `/email`

- [ ] Вкладка «Почта» на карточке — паритет с `/email` (ответ, апрув, анализ+черновик)
- [ ] Кнопка «Рассылка» — превью сегмента + лимит перед отправкой
- [ ] Relink сирот с карточки лида (не только `/ops/email`)

### E. Безопасность и аудит

- [ ] Маскировка email в логах и `/ops/traces`
- [ ] Аудит: кто отправил письмо / запустил кампанию / nurture
- [ ] Фильтр PII перед LLM (черновики, nurture)

### F. Голос (после приёмки лидов)

- [ ] Smoke: `write_email`, `send_email`, рассылка по сегменту голосом
- [ ] «Переделай короче» для черновика письма (связка F3 Voice §2)

### G. Acceptance

- [ ] pytest `tests/email/` + API sync/send
- [ ] Live smoke: connect, sync, send, nurture, campaign
- [ ] DevTools: `/email`, `/ops/email`, `/ops/email-agents`, карточка лида

### H. UI как Яндекс.Почта

Детали: [`F4_EMAIL_YANDEX_UI.md`](F4_EMAIL_YANDEX_UI.md)

- [x] Сайдбар: градиент, «Почта», «Написать» + синк, папки как в Яндексе
- [x] Поиск pill + «Найти» + чипы (вложения, дата, папки, от/кому, ещё)
- [x] «Главное» — звезда на треде (localStorage)
- [ ] Browser-апрув владельца по чеклисту `F4_EMAIL_YANDEX_UI.md`
- [ ] `is_read` / реальные вложения из IMAP (хвост API)
- [ ] Trash / Drafts / Spam — синк с IMAP-папками

### I. Полная история почты (backfill)

- [x] Фоновый backfill батчами по датам (`EMAIL_BACKFILL_*`, `email_sync/backfill.py`)
- [x] API `/api/email/backfill/*` + кнопка «Догрузить всю историю» на `/email`
- [x] Скрипт `scripts/run_email_backfill.py` для ускоренной догрузки
- [ ] Sent-папка в backfill (сейчас только INBOX)
- [ ] Browser-апрув: счётчик писем/тредов вырос до полной истории

---

## Не в Ф4 (явно вне scope)

| Тема | Почему |
|------|--------|
| Новый почтовый провайдер (не IMAP/SMTP) | Вне текущего стека |
| Полноценный webmail-клон | `/email` уже закрыт в Ф2 |
| Отдельный email-агент в LangGraph | Маркетолог + orchestrator достаточно |

---

## Порядок работ (рекомендуемый)

1. **A** — ящики в UI  
2. **B** — лимиты/антиспам  
3. **C** — nurture LLM ×20  
4. **D** — паритет карточки  
5. **E** — аудит и PII  
6. **F** — голос (когда снимут отложенность на лидах)  
7. **G** — acceptance и smoke  

---

## Автотесты (база, уже есть)

```bash
cd backend
python -m pytest tests/email/test_email_f3.py tests/api/test_email_sync_api.py -q
```
