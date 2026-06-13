# Операционка SmartCRM

Журналы сессий, acceptance по фазам, baselines. **Код и layout репо** — отдельный долг: [`debt/REPO_LAYOUT_DEBT.md`](debt/REPO_LAYOUT_DEBT.md).

## С чего начать (агент / новая сессия)

| Порядок | Файл | Зачем |
|---------|------|--------|
| 1 | [`session/PHASE2_ENTRY.md`](session/PHASE2_ENTRY.md) | Вход в Ф2: git, gate, очередь MAP |
| 2 | [`session/HANDOFF.md`](session/HANDOFF.md) | Текущая задача, следующий шаг |
| 3 | [`session/SESSION_STATE.md`](session/SESSION_STATE.md) | Журнал шагов (pre-commit) |
| 4 | [`session/ISSUES.md`](session/ISSUES.md) | Баги 🔴 |
| 5 | [`session/BACKLOG.md`](session/BACKLOG.md) | Хвосты по PRD_MAP |

## Дерево

```
docs/operations/
├── README.md                 ← вы здесь
├── session/                  # Живые журналы (обновляются каждый шаг)
├── baselines/                # Coverage, CI, матрица правил
├── phase1/                   # Acceptance Фазы 1 (закрытые блоки MAP)
├── phase2/                   # Acceptance Фазы 2 (в работе)
└── debt/                     # Отложенная уборка (не блокер)
```

### `session/` — каждый шаг агента

| Файл | Назначение |
|------|------------|
| `HANDOFF.md` | Спринт, статус, следующий `go` |
| `SESSION_STATE.md` | Строки «что сделано + hash коммита» |
| `CHANGELOG.md` | История изменений (канон хронологии) |
| `ISSUES.md` | Инциденты и баги |
| `BACKLOG.md` | Отложено по пунктам PRD_MAP |
| `PHASE2_ENTRY.md` | Handoff Ф1→Ф2 для следующего агента |

### `baselines/` — сквозные метрики

| Файл | Назначение |
|------|------------|
| `COVERAGE_BASELINE.md` | % pytest-cov, команда замера |
| `CI_BASELINE.md` | GitHub Actions, required checks |
| `RULES_MATRIX.md` | Матрица правил + регрессия по зонам |

### `phase1/` — acceptance закрытых блоков Ф1

См. [`phase1/README.md`](phase1/README.md) — лиды, голос, поиск, лидоген, ops, аналитика, тендеры, email.

### `phase2/` — acceptance Ф2

См. [`phase2/README.md`](phase2/README.md) — quality gates агентов; новые acceptance — в подпапку по домену MAP.

### `debt/`

| Файл | Назначение |
|------|------------|
| `REPO_LAYOUT_DEBT.md` | Уборка `backend/`/`frontend/` — отдельный go, не смешивать с ops |

## Правила

- Новый **acceptance Ф1** (редко) → `phase1/{домен}/`
- Новый **acceptance Ф2** → `phase2/{домен}/`
- **Не** класть acceptance в корень `operations/` — только в фазу + домен
- Операционные записи (handoff, backlog) — только `session/`

Канон layout репо: [`docs/dev/REPO_LAYOUT.md`](../dev/REPO_LAYOUT.md)
