# Services — внешние API тендеров

Клиенты к госзакупкам и агрегаторам. Вызываются из `api/routes/tenders/` и скриптов бенчмарков.

| Файл | За что |
|------|--------|
| `moy_zakupki.py` | API «Мои закупки» |
| `gosplan.py` | Госплан / ЕИС |
| `tenderguru.py` | TenderGuru |
| `datanewton.py` | DataNewton (контракты, компании) |
| `zakupki_parser.py` | Парсер zakupki.gov.ru |
| `lookalike_import.py` | Batch-импорт lookalike-кандидатов в CRM (`source: lookalike`) |
| `email_bootstrap.py` | Подключение почты из `.env` в БД (`bootstrap-from-env`) |
| `email_thread_list.py` | Enriched список тредов для UI (`isArchived`, `previewFrom`) |

Кэш ответов: `data/moy_zakupki_cache/`.  
Тесты: `tests/test_tender_sources.py`.
