# Services — внешние API тендеров

Клиенты к госзакупкам и агрегаторам. Вызываются из `api/routes/tenders/` и скриптов бенчмарков.

| Файл | За что |
|------|--------|
| `moy_zakupki.py` | API «Мои закупки» |
| `gosplan.py` | Госплан / ЕИС |
| `tenderguru.py` | TenderGuru |
| `tender_monitor_config.py` | Конфиг правил мониторинга (слова, ОКПД2) |
| `tender_monitor.py` | Поиск, дедуп, очередь Ops |
| `tender_monitor_background.py` | Фоновый планировщик мониторинга |
| `tender_sources/` | Провайдер поиска: legacy (Gosplan+TG), kontur-stub (Ф4) |
| `tender_tracked.py` | Tracked тендеры для календаря |
| `tender_notifications.py` | In-app уведомления |
| `tender_calendar.py` | Календарь дедлайнов и скан напоминаний |
| `datanewton.py` | DataNewton (контракты, компании) |
| `zakupki_parser.py` | Парсер zakupki.gov.ru |
| `lookalike_import.py` | Batch-импорт lookalike-кандидатов в CRM (`source: lookalike`) |
| `email_bootstrap.py` | Подключение почты из `.env` в БД (`bootstrap-from-env`) |
| `email_account_delete.py` | Отключение ящика: удаление аккаунта + очистка тредов/писем/кампаний/цепочек |
| `email_thread_list.py` | Enriched список тредов для UI (`isArchived`, `previewFrom`) |
| `email_thread_analyze.py` | Анализ треда: тип письма + черновик маркетолога |
| `industry_catalog.py` | Справочник отраслей (фикс + CRM) и статистика сегмента |
| `lead_products_owned.py` | Нормализация списка «уже купили» на лиде |
| `lead_segment_query.py` | Фильтр лидов по сегменту для рассылок |
| `lead_hunt_config.py` | Конфиг автономного поиска лидов |
| `lead_hunt_background.py` | Фоновый планировщик lead hunt (ICP → поиск) |
| `lead_hunt_icp.py` | ICP из won + funnelBySource + Стратег |
| `lead_hunt_search_cycle.py` | Цикл: portrait/prospect → pipeline → fanout агентов |
| `lead_hunt_candidates.py` | Поиск кандидатов, очередь approve → CRM |
| `lead_hunt_queue.py` | Нормализованный вид очереди (company, score, summary) |
| `lead_hunt_notifications.py` | In-app уведомления lead hunt |
| `lead_hunt_run_log.py` | Trace прогона + agent_run_log fanout при approve |
| `sla_protocol_runner.py` | Назначение SLA-протокола на лид, автозадачи, статус шагов |
| `sla_escalation.py` | Просрочка SLA → escalated + Ops queue (+ Telegram critical) |
| `sla_escalation_background.py` | Фоновый poll эскалации (`SLA_ESCALATION_POLL_MINUTES`) |

Кэш ответов: `data/moy_zakupki_cache/`.  
Тесты: `tests/test_tender_sources.py`.
