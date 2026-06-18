# Ф4 — Контур.Закупки API (gate)

**Откуда:** раньше пункт Ф3 MAP; перенесён в Ф4 после окупаемости.

**Зачем gate:** не платить за API, пока нет первой тендерной сделки через SmartCRM.

---

## Когда подключать

- [ ] Закрыта минимум **одна крупная** тендерная сделка через систему
- [ ] Окупаемость API (смета vs TenderGuru+Gosplan)
- [ ] Явный **go** оператора

---

## Что даст Контур сверх текущего (legacy)

| Сейчас (legacy) | Контур |
|-----------------|--------|
| Gosplan free/prod, шум без keyword | Стабильный поиск ЕИС |
| TenderGuru агрегатор | Официальные карточки + доки |
| Ручной PDF upload | Документы из API |
| `TENDER_PROVIDER=legacy` | `TENDER_PROVIDER=kontur` |

---

## Как переключиться (1 шаг после gate)

1. Договор + ключ → `.env`: `KONTUR_ZAKUPKI_API_KEY`, `TENDER_PROVIDER=kontur`
2. Реализовать `services/tender_sources/kontur.py` (адаптер к тому же контракту, что `legacy`)
3. UI и `/api/tenders/*` **не менять** — поля `title`, `deadline`, `budget`, `customer`, `customer_inn`, `url`
4. Smoke: search + monitor + карточка + enrich
5. Откат: `TENDER_PROVIDER=legacy`

---

## Связанные файлы

- `services/tender_sources/__init__.py` — `search_for_monitor()`
- `services/tender_sources/kontur.py` — заглушка до gate
- `GET /api/tenders/provider/status`

---

## Не делать до gate

- Платная подписка Контур
- Стабилизация парсеров zakupki.gov.ru «вместо» Контура
