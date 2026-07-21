# Операционка SmartCRM

Журналы сессий, acceptance по фазам, baselines. **Код и layout репо** — отдельный долг: [`debt/REPO_LAYOUT_DEBT.md`](debt/REPO_LAYOUT_DEBT.md).

## С чего начать (агент / новая сессия)

| Порядок | Файл | Зачем |
|---------|------|--------|
| 1 | [`session/HANDOFF.md`](session/HANDOFF.md) | Текущая задача, следующий шаг |
| 2 | [`session/SESSION_STATE.md`](session/SESSION_STATE.md) | Журнал шагов (pre-commit) |
| 3 | [`session/ISSUES.md`](session/ISSUES.md) | Баги 🔴 |
| 4 | [`session/BACKLOG.md`](session/BACKLOG.md) | Хвосты по пунктам чеклистов |
| 5 | [`phase4/CHECKLIST.md`](phase4/CHECKLIST.md) | Чеклист активной фазы (Ф4) |

## Дерево

```
docs/operations/
├── README.md                 ← вы здесь
├── session/                  # Живые журналы (обновляются каждый шаг)
├── baselines/                # Coverage, CI, матрица правил
├── phase1/                   # CHECKLIST.md + acceptance Фазы 1 (закрыта)
├── phase2/                   # CHECKLIST.md + acceptance Фазы 2 (закрыта)
├── phase3/                   # CHECKLIST.md + acceptance Фазы 3 (закрыта)
├── phase4/                   # CHECKLIST.md + тюнинг / доводка до MVP — текущая
└── debt/                     # Отложенная уборка (не блокер)
```

**Чеклист фазы** — `phase{N}/CHECKLIST.md`: рабочие пункты `[ ]`/`[x]`, управление фазой. Активная фаза — **Ф4**. Результаты (acceptance) — в папках областей той же фазы (`phase4/leads/`, `phase4/agents/`, …).

### `session/` — каждый шаг агента

| Файл | Назначение |
|------|------------|
| `HANDOFF.md` | Спринт, статус, следующий `go` |
| `SESSION_STATE.md` | Строки «что сделано + hash коммита» |
| `CHANGELOG.md` | История изменений (канон хронологии) |
| `ISSUES.md` | Инциденты и баги |
| `BACKLOG.md` | Отложено по пунктам чеклистов фаз |

### `baselines/` — сквозные метрики

| Файл | Назначение |
|------|------------|
| `COVERAGE_BASELINE.md` | % pytest-cov, команда замера |
| `CI_BASELINE.md` | GitHub Actions, required checks |
| `RULES_MATRIX.md` | Матрица правил + регрессия по зонам |

### `phase1/` — acceptance закрытых блоков Ф1

См. [`phase1/README.md`](phase1/README.md) — лиды, голос, поиск, лидоген, ops, аналитика, тендеры, email.

### `phase2/` — acceptance Ф2

См. [`phase2/README.md`](phase2/README.md) — quality gates агентов; новые acceptance — в подпапку по домену.

### `phase4/` — тюнинг и доводка до MVP (после Ф3)

См. [`phase4/README.md`](phase4/README.md) — не блокер Ф3; vendor crawl tuning → `phase4/rag/`.

### `debt/`

| Файл | Назначение |
|------|------------|
| `REPO_LAYOUT_DEBT.md` | Уборка `backend/`/`frontend/` — отдельный go, не смешивать с ops |

## Правила

- Новый **acceptance Ф1** (редко) → `phase1/{домен}/`
- Новый **acceptance Ф2** → `phase2/{домен}/`
- **Тюнинг после Ф3** → `phase4/{домен}/` (см. `phase4/README.md`)
- **Не** класть acceptance в корень `operations/` — только в фазу + домен
- Операционные записи (handoff, backlog) — только `session/`

Канон layout репо: [`docs/dev/REPO_LAYOUT.md`](../dev/REPO_LAYOUT.md)
