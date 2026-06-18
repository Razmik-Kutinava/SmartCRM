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
| `datanewton.py` | DataNewton (контракты, компании) |
| `zakupki_parser.py` | Парсер zakupki.gov.ru |
| `lookalike_import.py` | Batch-импорт lookalike-кандидатов в CRM (`source: lookalike`) |
| `email_bootstrap.py` | Подключение почты из `.env` в БД (`bootstrap-from-env`) |
| `email_thread_list.py` | Enriched список тредов для UI (`isArchived`, `previewFrom`) |
| `email_thread_analyze.py` | Анализ треда: тип письма + черновик маркетолога |
| `industry_catalog.py` | Справочник отраслей (фикс + CRM) и статистика сегмента |
| `lead_products_owned.py` | Нормализация списка «уже купили» на лиде |
| `lead_segment_query.py` | Фильтр лидов по сегменту для рассылок |

Кэш ответов: `data/moy_zakupki_cache/`.  
Тесты: `tests/test_tender_sources.py`.
