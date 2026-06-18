# Ф3 — Тех. спец: мониторинг тендеров 24/7

**PRD_MAP:** Фаза 3 → Тех. спец — тендеры → п.1 мониторинг.

**Суть:** один Тех. спец — не отдельный агент. Фоновый поиск по правилам (слова + ОКПД2) → новые закупки в Ops-очередь.

---

## Сделано

| # | Что | Где |
|---|-----|-----|
| 1 | Конфиг правил мониторинга | `backend/data/tender_monitor_config.json` |
| 2 | Поиск Gosplan + TenderGuru, дедуп, фильтры | `services/tender_monitor.py` |
| 3 | Фоновый планировщик | `services/tender_monitor_background.py`, `main.py` |
| 4 | API | `GET/PUT /api/tenders/monitor/config`, `GET /status`, `POST /run` |
| 5 | UI Ops | `/ops/tender-monitor` |
| 6 | Очередь Ops | `kind: tender_monitor`, id `auto-tender-{watch}-{fp}` |

---

## Проверка

1. Открыть `/ops/tender-monitor`, добавить правило (слова или ОКПД2), включить.
2. **Dry-run** — в ответе `total_new` без записи в очередь.
3. **Запустить сейчас** — новые тендеры в `/ops/queue`.
4. Повторный запуск — те же тендеры не дублируются (`seen` в state).
5. Включить авто-мониторинг → в логах backend «Tender monitor auto» по интервалу.

```bash
cd backend
python -m pytest tests/services/test_tender_monitor.py tests/api/test_tenders_monitor_api.py -q
```

---

## Не в этом шаге

- Календарь дедлайнов (п.2 MAP)
- Контур API
- Авто-разбор ТЗ → RAG
- Полное слияние промптов `tender_agents.py` в `tech_specialist.py` (отдельный шаг)

---

## Связанные файлы

- `backend/services/tender_monitor_config.py`
- `backend/services/tender_monitor.py`
- `backend/api/routes/tenders/monitor_routes.py`
- `frontend/src/lib/tenders/tenderMonitorOps.js`
