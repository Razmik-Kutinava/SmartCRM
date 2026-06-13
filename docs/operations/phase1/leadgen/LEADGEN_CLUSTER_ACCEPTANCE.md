# Смоук лидогена — кластер / холдинг (2026-06-10)

PRD_MAP: **«Лидогенерация `/leadgen`» — Кластер / холдинг** (перепроход)

## Команда

```bash
cd backend && python scripts/smoke_leadgen_cluster.py
```

5 pytest + live `run_cluster(inn=5040048921)` (Хохланд) + probe `/leadgen`.

**ИНН:** live-якорь `5040048921` (`leadgen/inn_constants.py`).

---

## Пайплайн

1. **Якорь** — Checko `fetch_company(inn)` → учредители, СвязУчред (дочки)
2. **Уровень 1** — материнские юрлица, дочерние якоря
3. **Уровень 2** — физлица `/person`, сестринские через родителя
4. **Финансы** — `fetch_finances` якоря, суммарный оборот группы
5. **Группы** — subsidiaries, parents, siblings, person_companies, ips

---

## ✅ СДЕЛАНО и ПРОВЕРЕНО

| # | Шаг | Результат |
|---|-----|-----------|
| 1 | API `/cluster` | 3 теста `test_leadgen_cluster_api.py` |
| 2 | Integration mock | дочка + материнская `test_cluster.py` |
| 3 | Live smoke Хохланд | якорь + связи, `total_companies` ≥ 1 |
| 4 | UI режим «Кластер / Холдинг» | форма ИНН + дерево групп |
| 5 | DevTools E2E 2026-06-10 (**user-chrome-devtools**) | ИНН `5040048921` → POST `/api/leadgen/cluster` **200**, якорь **ХОХЛАНД**, **4** субъекта, 3 дочки |

**testid:** `leadgen-mode-cluster`, `leadgen-cluster-inn`, `leadgen-cluster-results`, `leadgen-cluster-anchor`, `leadgen-cluster-total`

---

## ⚠️ Хвосты (не блокер MAP)

| Пробел | Примечание |
|--------|------------|
| Крупные холдинги (Сбер, Газпром) | много Checko-запросов, долго |
| Нет progress UI | как у portrait — отложено |
