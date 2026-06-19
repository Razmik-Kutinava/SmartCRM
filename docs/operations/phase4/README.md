# Фаза 4 — тюнинг и доводка до MVP

**Не блокер Ф3.** Сюда — polish, retrieval, автоматизация обновлений, eval там, где базовый функционал уже есть.

| Домен | Документ |
|-------|----------|
| **Дашборд** (обход Ф4, старт) | [`dashboard/F4_DASHBOARD_ACCEPTANCE.md`](dashboard/F4_DASHBOARD_ACCEPTANCE.md) |
| Vendor crawl → RAG `tech_specialist` | [`rag/F4_VENDOR_CRAWL_TUNING.md`](rag/F4_VENDOR_CRAWL_TUNING.md) |
| A/B промптов по трейсам (Hermes / агенты) | [`agents/F4_PROMPT_AB_TUNING.md`](agents/F4_PROMPT_AB_TUNING.md) |
| Авто-суфлёр Стратега (все агенты + Hermes) | [`agents/F4_STRATEGIST_SUGGESTER_TUNING.md`](agents/F4_STRATEGIST_SUGGESTER_TUNING.md) |
| Контур.Закупки API (gate) | [`tenders/F4_KONTUR_GATE.md`](tenders/F4_KONTUR_GATE.md) |
| Тех. спец — тендеры (автоматизация, матрица ТЗ, eval) | [`tenders/F4_TECH_TENDER_TUNING.md`](tenders/F4_TECH_TENDER_TUNING.md) |
| Аналитика v2 (прогноз, калибровка, агенты) | [`analytics/F4_ANALYTICS_V2_TUNING.md`](analytics/F4_ANALYTICS_V2_TUNING.md) |
| **Платформа** (интеграции без `.env`, синк, Telegram, баллы P3) | [`platform/F4_PLATFORM_TUNING.md`](platform/F4_PLATFORM_TUNING.md) |
| **Лиды** (обход Ф4: CRUD, карточка) | [`leads/F4_LEADS_ACCEPTANCE.md`](leads/F4_LEADS_ACCEPTANCE.md) |

Новые acceptance Ф4 → `phase4/{домен}/`.
