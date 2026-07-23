# Чеклист: Фаза 3 — Автономия

**Статус фазы:** ✅ по блокам

> **Легенда:** ✅ готово (код + смоук + acceptance) · ⚠️ код ✅, хвост в `BACKLOG.md` · 🔲 не начато · `[x]` = ✅ по коду/автомату · `[ ]` = 🔲 или хвост.
> **Закрытие пункта:** pytest + acceptance → `[x]`; финальный `[x]` — только после «ок» оператора. DoD пункта → [`dev-gates`](../../../.cursor/rules/workflow/smartcrm-dev-gates.mdc).
> Результаты (acceptance) — в папках областей рядом: `./{область}/*.md`. Хвосты → [`../session/BACKLOG.md`](../session/BACKLOG.md).

---

## Фаза 3 — Автономия

**Порядок:** голосовой апрув → email цепочки → тех. спец (тендеры) → аналитика v2 → краулинг/A/B → Telegram → CRM → экспорт.

### Voice

- [x] Подтверждение голосом («да, отправляй» / «нет») · [`F3_VOICE_APPROVAL_ACCEPTANCE.md`](../phase3/voice/F3_VOICE_APPROVAL_ACCEPTANCE.md)
- [x] «Переделай короче» голосом · см. acceptance §2
- [x] История команд Ops → Voice · см. acceptance §3

### Email

- [x] Автоответ FAQ по правилам Ops · [`F3_EMAIL_AUTONOMY_ACCEPTANCE.md`](../phase3/email/F3_EMAIL_AUTONOMY_ACCEPTANCE.md)
- [x] Рассылки по сегменту лидов · см. acceptance §2
- [x] Цепочки 20 касаний (автономно) · см. acceptance §3 · LLM под продукт [`email_nurture.md`](../modules/email_nurture.md) · **UI:** `/email` + кнопка «Рассылка» на карточке лида
- [x] Автолинк письмо → лид по домену · см. acceptance §4

### Self-improvement

- [x] **Quality gate tuning:** все агенты ≥85% (baseline 2026-06-14: Hermes 72.2%, Tech 60%) → [`AGENTS_GATE_TUNING_BASELINE.md`](../baselines/AGENTS_GATE_TUNING_BASELINE.md) · [`F3_GATE_TUNING_ACCEPTANCE.md`](../phase3/agents/F3_GATE_TUNING_ACCEPTANCE.md) — **A+B+C ✅ 2026-06-17**, апрув «ок»
- [x] Краулинг URL вендоров → RAG тех. спеца · **live 871 чанк, 10 PDF** · шаг1–4 ✅ [`F3_VENDOR_CRAWL_ACCEPTANCE.md`](../phase3/rag/F3_VENDOR_CRAWL_ACCEPTANCE.md) · тюнинг → **Ф4** · апрув «ок» 2026-06-17
- [x] A/B промптов по трейсам · [`F3_PROMPT_AB_TRACES_ACCEPTANCE.md`](../phase3/agents/F3_PROMPT_AB_TRACES_ACCEPTANCE.md) · апрув «ок» 2026-06-17
- [x] Авто-суфлёр Стратега · [`F3_STRATEGIST_SUGGESTER_ACCEPTANCE.md`](../phase3/agents/F3_STRATEGIST_SUGGESTER_ACCEPTANCE.md) · тюнинг → **Ф4** · апрув «ок» 2026-06-17

### Тех. спец — тендеры

> Один агент: RAG вендоров + мониторинг закупок + разбор ТЗ. Не отдельный «тендерный агент».

- [x] Мониторинг ключевых слов / ОКПД2 24/7 · [`F3_TECH_TENDER_MONITOR_ACCEPTANCE.md`](../phase3/tenders/F3_TECH_TENDER_MONITOR_ACCEPTANCE.md) · апрув «ок» 2026-06-17
- [x] Уведомления + календарь дедлайнов · [`F3_TECH_TENDER_NOTIFY_CALENDAR_ACCEPTANCE.md`](../phase3/tenders/F3_TECH_TENDER_NOTIFY_CALENDAR_ACCEPTANCE.md) · апрув «ок» 2026-06-17
- [x] Дожать бесплатные источники (Gosplan prod, TenderGuru, мониторинг, DataNewton, доки) · [`F3_TECH_TENDER_SOURCES_ACCEPTANCE.md`](../phase3/tenders/F3_TECH_TENDER_SOURCES_ACCEPTANCE.md) · Контур → **Ф4** · апрув «ок» 2026-06-17
- [x] Решение участвовать/нет с обоснованием (Тех. спец + Экономист → Стратег) · [`F3_TECH_TENDER_PARTICIPATION_ACCEPTANCE.md`](../phase3/tenders/F3_TECH_TENDER_PARTICIPATION_ACCEPTANCE.md) · апрув «ок» 2026-06-17

### Аналитика v2

- [x] Когортный анализ · [`F3_ANALYTICS_V2_COHORT_ACCEPTANCE.md`](../phase3/analytics/F3_ANALYTICS_V2_COHORT_ACCEPTANCE.md)
- [x] Эффективность агентов по трейсам · [`F3_ANALYTICS_V2_AGENT_TRACES_ACCEPTANCE.md`](../phase3/analytics/F3_ANALYTICS_V2_AGENT_TRACES_ACCEPTANCE.md)
- [x] Воронка по источнику · [`F3_ANALYTICS_V2_FUNNEL_SOURCE_ACCEPTANCE.md`](../phase3/analytics/F3_ANALYTICS_V2_FUNNEL_SOURCE_ACCEPTANCE.md)
- [x] Прогноз закрытия (Экономист) · [`F3_ANALYTICS_V2_CLOSE_FORECAST_ACCEPTANCE.md`](../phase3/analytics/F3_ANALYTICS_V2_CLOSE_FORECAST_ACCEPTANCE.md)

### Платформа

- [x] Telegram-бот · [`F3_PLATFORM_TELEGRAM_ACCEPTANCE.md`](../phase3/platform/F3_PLATFORM_TELEGRAM_ACCEPTANCE.md) · апрув 2026-06-17
- [x] Экспорт Excel/PDF (воронка, карточка, тендеры) · [`F3_PLATFORM_EXPORT_ACCEPTANCE.md`](../phase3/platform/F3_PLATFORM_EXPORT_ACCEPTANCE.md)
- [x] Импорт/экспорт Битрикс24, AmoCRM, HubSpot, CSV · CSV: [`F3_PLATFORM_CSV_SYNC_ACCEPTANCE.md`](../phase3/platform/F3_PLATFORM_CSV_SYNC_ACCEPTANCE.md) · Битрикс push: [`F3_PLATFORM_BITRIX_PUSH_ACCEPTANCE.md`](../phase3/platform/F3_PLATFORM_BITRIX_PUSH_ACCEPTANCE.md) · Amo: [`F3_PLATFORM_AMO_SYNC_ACCEPTANCE.md`](../phase3/platform/F3_PLATFORM_AMO_SYNC_ACCEPTANCE.md) · HubSpot: [`F3_PLATFORM_HUBSPOT_SYNC_ACCEPTANCE.md`](../phase3/platform/F3_PLATFORM_HUBSPOT_SYNC_ACCEPTANCE.md)
- [x] Автономный поиск новых лидов агентами · шаг 1–7: [`F3_PLATFORM_LEAD_HUNT_ACCEPTANCE.md`](../phase3/platform/F3_PLATFORM_LEAD_HUNT_ACCEPTANCE.md) · апрув 2026-06-17

### Баллы P3 (остаток)

- [x] Расширенные SLA-протоколы + эскалация · [`F3_SLA_PROTOCOLS_ACCEPTANCE.md`](../phase3/leads/F3_SLA_PROTOCOLS_ACCEPTANCE.md) · апрув 2026-06-17
- [x] Экспорт отчёта по баллам и воронке · [`F3_SCORING_EXPORT_ACCEPTANCE.md`](../phase3/leads/F3_SCORING_EXPORT_ACCEPTANCE.md)

---
