# Смоук лидогена — автосохранение в CRM (2026-06-10)

PRD_MAP: **«Лидогенерация `/leadgen`» — Автосохранение в CRM при скор ≥ 30**

## Команда

```bash
cd backend && python scripts/smoke_leadgen_autosave.py
```

8 pytest + probe `/leadgen` + порог из `leadgen/crm_threshold.py` (конфиг `data/leadgen_config.json`, дефолт **30**).

---

## Поведение

1. UI: чекбокс «Сохранить в CRM автоматически» → `save_to_crm: true` в POST `/api/leadgen/analyze`
2. Pipeline: `should_autosave_to_crm(save_to_crm, final_score)` — порог из конфига
3. При проходе порога: `_save_to_crm(card)` → `crm_lead_id` в ответе и баннер «Автосохранён в CRM»
4. Скор ниже порога или чекбокс выкл. — ручная кнопка «+ Добавить в CRM» (`POST /api/leadgen/save`)

**Live-ИНН для E2E:** `5040048921` (Хохланд, `leadgen/inn_constants.py`).

---

## ✅ СДЕЛАНО и ПРОВЕРЕНО

| # | Шаг | Результат |
|---|-----|-----------|
| 1 | Порог из конфига | `leadgen/crm_threshold.py`, не хардкод в pipeline |
| 2 | Unit + persist | `test_autosave.py` — порог 29/30, запись в Lead |
| 3 | API | `test_leadgen_autosave_api.py` — analyze + `/save` |
| 4 | UI testid | `leadgen-direct-autosave`, `leadgen-autosave-done` |
| 5 | DevTools E2E 2026-06-10 (**user-chrome-devtools**) | ИНН `5040048921`, чекбокс вкл. → скор **84** → «Автосохранён в CRM», лид **#3187** |

---

## ⚠️ Хвосты (не блокер MAP)

| Пробел | Примечание |
|--------|------------|
| ~~Дубликаты при повторном анализе~~ | **исправлено:** dedup по ИНН — update существующего (`persist_card.py`) |
| Портрет / кластер | автосейв только режим «По ИНН / названию» |
