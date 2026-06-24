# Ф4 — X5-gap: 👤 browser-апрув (шаги 5 и 7)

**Когда:** после частичного mass-resync (данные в БД). **Кто:** оператор в Chrome.

---

## Перед проверкой

```bash
# бэкенд :8000
curl http://127.0.0.1:8000/health

# фронт (5173 или 5174 если занят)
cd frontend && npm run dev

# счётчики БД
cd backend && python scripts/check_bitrix_fields_backfill.py
```

Минимум для шага **5:** лид 5227 (`/leads/289`) — `amount`, `bitrixExtra`, `contacts`.  
Минимум для шага **7:** `subscription_end in extra` > 0 в check script.

---

## Шаг 5 — карточка

**URL:** `http://localhost:5173/leads/289` (bitrix lead **5227**, ИКС 5)

| Что | Ожидание |
|-----|----------|
| Шапка сумма | `15 780 $` (`data-testid="lead-card-deal-amount"`) |
| Бейдж | «Повторный лид» |
| Блок лицензия/подписка | reservedUntil, licenseRegistration |
| Контакты | 5 контактов (readonly список) |

**Ок** → напиши агенту: `ок, шаг 5`

---

## Шаг 7 — список

**URL:** `http://localhost:5173/leads/list`

| Что | Ожидание |
|-----|----------|
| Фильтр «Подписка» | есть, кликается |
| Фильтр «Тип поставки» | есть |
| Колонка «Подписка до» | даты у лидов с `bitrixExtra.subscriptionEnd` |

Пустая колонка у большинства = resync ещё не дошёл — не баг UI.

**Ок** → `ок, шаг 7`

---

## Mass-resync (параллельно)

```bash
cd backend
python -u scripts/resync_bitrix_lead_fields.py --resume --workers 2 --batch-size 20 --delay-ms 100
python scripts/check_bitrix_fields_backfill.py
```

Цель: **3228/3228** b24-лидов, `bitrix_extra` максимально заполнен.

---

## Статус

| Шаг | Код | Данные | Agent DevTools | 👤 Browser |
|-----|-----|--------|----------------|------------|
| 5 карточка | ✅ | 🔄 ~33% | ✅ DevTools | ✅ **оператор 2026-06-24** |
| 7 список | ✅ | 🔄 subscription_end растёт | ✅ DevTools | ✅ **оператор 2026-06-24** |
| календарь | ✅ fix `</div>` | — | ✅ `/leads/calendar` — сетка июнь 2026, задачи по дням | — |
