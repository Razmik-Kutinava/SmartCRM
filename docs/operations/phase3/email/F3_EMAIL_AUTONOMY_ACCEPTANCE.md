# Ф3 Email — автономия

**PRD_MAP:** Фаза 3 → Email (4 пункта).

## Критерии

| # | Пункт | Проверка |
|---|-------|----------|
| 1 | FAQ auto-reply по Ops | `AgentEmailIntent.auto_send` + триггеры; после IMAP sync → `try_faq_autoreply` |
| 2 | Рассылки по сегменту | `POST /api/email/campaigns` с `segment`; UI `/email` campaigns |
| 3 | 20 касаний автономно | `POST /api/email/nurture/start` (лид) или `/nurture/start-segment` (фильтры); фон `process_due_nurture_steps`; персонализация `{{company}}`/`{{contact}}` |
| 4 | Автолинк по домену | `find_lead_for_email` domain; `POST /api/email/relink-orphans` |

## Автотесты

```bash
cd backend
python -m pytest tests/email/test_email_f3.py tests/api/test_email_sync_api.py -q
```

## Nurture 20 касаний (маркетолог)

**Смысл:** одна цепочка = один клиент (лид) или пакет лидов по сегменту. Шаблоны писем общие, при отправке подставляются имя компании и контакт; продукт задаётся при старте (`product_name`).

| Режим | API | Когда |
|-------|-----|-------|
| Один клиент | `POST /api/email/nurture/start` | `lead_id`, `account_id`, опц. `product_name` |
| Сегмент | `POST /api/email/nurture/start-segment` | `segment` (как campaigns: `stage`, `min_score`), `limit` до 200 |
| Исполнение | `POST /api/email/nurture/process-due` | шаги с `scheduled_at <= now`; шаг 1 — сразу (day=0) |
| Пауза | `POST /api/email/nurture/{id}/pause` | вручную или при inbound ответе |
| Список | `GET /api/email/nurture/chains?lead_id=` | UI `/ops/email` |

**20 шагов:** каналы email → phone → linkedin → email…; интервал 3 дня; ~10 писем SMTP, остальное — задачи CRM (Маркетолог).

**Плейсхолдеры:** `{{company}}`, `{{contact}}`, `{{greeting}}` — при отправке; продукт вшивается в шаблон при создании плана.

**Код:** `services/email_nurture_plan.py`, `services/email_nurture.py`, `services/email_nurture_llm.py`, `agents/marketer_nurture.py`.

### LLM-цепочка под продукт (пилот 3 письма)

Маркетолог анализирует лида → генерирует N писем под продукт (MaxPatrol VM) → nurture с кастомным планом.

| API | `POST /api/email/nurture/start-llm` |
| Smoke | `python scripts/smoke_email_nurture_llm_live.py` |
| Модуль | [`docs/modules/email_nurture.md`](../../../modules/email_nurture.md) |

Live 2026-06-15: лид HOCHLAND (3187) → 3 письма на ib@, `emails_sent=3`.

### UI этап B — массовая рассылка `/email`

| Элемент | Где |
|---------|-----|
| Вкладка «Массовая (сегмент)» | `/email` sidebar |
| Фильтры + 3 примера + апрув + send | `EmailCampaignPanel.svelte` |
| API | `preview-llm`, `test-send`, `campaigns` send_now |

**Live DevTools MCP 2026-06-16:** `/email` → Массовая → «без отрасли» (2 лида) → 3 LLM → test ib@ → **send 2/2** (`DevTools mass smoke 2026-06-16`, me@agneko.am).

## ENV (nurture)

- `NURTURE_TEST_CLIENT_EMAIL` — email тестового «клиента» для live smoke (иначе `EMAIL_ACCOUNT_2_USER`)
- `NURTURE_PRODUCT_NAME` — дефолт продукта в шаблонах, если не передан `product_name`


## Ops UI

- `/ops/email-agents` — правила FAQ + toggle автоответ
- `/ops/email` — nurture chains + relink

## Live smoke (2026-06-15, полный прогон)

| Шаг | Команда | Результат |
|-----|---------|-----------|
| Connect me@ | `EMAIL_CONNECT_ONLY=1 python scripts/smoke_email_connect.py` | **OK** `imported=50` — `imap.yandex.com` |
| Connect ib@ | `EMAIL_CONNECT_ONLY=2 python scripts/smoke_email_connect.py` | **OK** `total=50` |
| me@ SMTP live | `python scripts/smoke_email_faq_live.py` | **OK** self-send me@ |
| FAQ live | `python scripts/smoke_email_faq_live.py` | **OK** ib@→me@ «прайс» → sync `faq_autoreplies=1` + outbound `faq_auto` |
| IMAP sync | `python scripts/smoke_email_sync.py` | OK |
| SMTP ib@ | `python scripts/smoke_email_smtp_send.py` | OK |
| Relink | `POST /api/email/relink-orphans?limit=100` | OK `scanned=100` |
| DevTools UI | `/email`, `/ops/email`, `/ops/email-agents` | OK: треды «прайс», Relink, FAQ-правила |
| Nurture live | `python scripts/smoke_email_nurture_live.py` | **OK** лид 3191 → chain 2 → `emails_sent=1`, subject с `Nurture Live Клиент ООО` |
| Nurture segment | `python scripts/smoke_email_nurture_segment_live.py` | **OK** preview count=2 → `started=2`, chains 3–4 |
| Nurture API | `GET /api/email/nurture/chains` | **OK** active chains в UI |
| DevTools `/ops/email` | nurture table | **OK** таблица `nurture-chains-table`: ID, лид, active, шаги 1/20 (vite proxy + `PUBLIC_SMARTCRM_API_KEY`) |
| LLM nurture 3 | `python scripts/smoke_email_nurture_llm_live.py` | **OK** lead 3187 HOCHLAND → 3 emails ib@, MaxPatrol VM |
| Mass campaign UI | Chrome DevTools MCP `/email` Массовая | **OK** 2026-06-16: 2/2 sent, кампания в истории |

## ENV

- `EMAIL_FAQ_AUTOREPLY=1` (default) — вкл FAQ
- `EMAIL_FAQ_MAX_PER_DAY=50` — лимит автоответов/день

Backend: `uvicorn` :8000, фоновый auto-sync `imported=0 total=50` в логах.

## Коммит

См. SESSION_STATE.
