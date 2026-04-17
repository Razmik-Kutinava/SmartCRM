# SmartCRM — Агенты

Все агенты работают параллельно через LangGraph. Уровень компетенций — PhD эксперт в своей области.

---

## Архитектура

```
Intent + Slots (от Hermes или UI)
    ↓
Оркестратор (orchestrator.py)
    ├→ Аналитик   ─┐
    ├→ Экономист   ├─ параллельно (asyncio.gather)
    ├→ Маркетолог  │
    └→ Тех. спец  ─┘
    ↓
Стратег (ждёт всех, синтезирует)
    ↓
final_reply + decision + next_action
```

**LLM провайдер (агенты):** Groq (`GROQ_MODEL`, по умолчанию `llama-3.1-8b-instant`) → Ollama (`OLLAMA_MODEL`, например `qwen2.5:0.5b`) fallback — см. `core/llm.py`, `docs/stack/LLM.md`  
**Агентный state:** `AgentState` TypedDict (base.py) — общий контейнер через весь pipeline

**Тендерный поиск** вынесен в отдельный модуль API/UI (**`/api/tenders`**, вкладка «Тендеры»), это не отдельный узел LangGraph. Описание источников, лимитов и env: `docs/TENDERS.md`.

---

## Агенты

### Аналитик (`analyst.py`)

**Роль:** BANT-анализ лидов, скоринг 0–100, следующие шаги, риски.

**Интенты:** `create_lead`, `update_lead`, `delete_lead`, `analyze_lead`, `list_leads`

**Инструменты:** `read_leads`, `read_lead_by_company`, `update_lead_score`, `compute_lead_score`, `read_tasks`

**Логика по интентам:**
- `create_lead` — анализирует по слотам (лид ещё не в БД), считает эвристический скор + LLM
- `update_lead` — загружает полный лид из БД по company, подтягивает задачи, обновляет скор в БД
- `analyze_lead` — то же что update_lead, но инициируется вручную (с `lead_id`)
- `list_leads` — быстрая сводка без LLM (total, by_stage, avg_score, hot_count)

**Скоринг:** двойной — эвристика (`compute_lead_score`) + LLM, финальный = среднее двух

---

### Экономист (`economist.py`)

**Роль:** ROI / LTV / CAC, оценка бюджета, вероятность сделки, ценообразование.

**Интенты:** `create_lead`, `update_lead`, `list_leads`, `analyze_lead`

**Инструменты:** `read_leads`, `read_tasks`, `read_lead_by_company`

**Ключевые поля ответа:** `budget_estimate`, `deal_segment` (smb/mid_market/enterprise), `ltv_estimate`, `deal_probability_pct`, `pricing_strategy`, `discount_ceiling`

---

### Маркетолог (`marketer.py`)

**Роль:** ABM-стратегия, персональное письмо, план касаний, психология клиента.

**Интенты:** `create_lead`, `write_email`, `analyze_lead`

**Инструменты:** `read_lead_by_company` (для write_email и analyze_lead)

**Ключевые поля ответа:** `buyer_profile`, `value_hook`, `first_email` (subject+body), `touch_sequence`, `industry_insight`

---

### Технический специалист (`tech_specialist.py`)

**Роль:** IT-стек клиента, зрелость, интеграционные риски, пресейл-вопросы.

**Интенты:** `create_lead`, `update_lead`, `analyze_lead`

**Инструменты:** `read_lead_by_company` (для update_lead)

**Ключевые поля ответа:** `likely_stack`, `it_maturity` (basic/developing/advanced/enterprise), `technical_risks`, `implementation_complexity`, `presale_questions`

---

### Стратег (`strategist.py`)

**Роль:** Синтез решений от всех агентов, финальный ответ оператору.

**Запускается:** всегда последним, после параллельных агентов (кроме `list_leads`)

**Видит:** полный output аналитика, экономиста, маркетолога, тех. спеца

**Ключевые поля ответа:** `decision`, `priority` (high/medium/low), `urgency` (today/this_week/next_week/nurture), `next_action`, `final_reply`, `coach_tip`

---

## Оркестратор (`orchestrator.py`)

| Интент | Параллельные агенты | Стратег |
|---|---|---|
| `create_lead` | Аналитик + Экономист + Маркетолог + Тех. спец | да |
| `update_lead` | Аналитик + Экономист + Маркетолог + Тех. спец | да |
| `analyze_lead` | Аналитик + Экономист + Маркетолог + Тех. спец | да |
| `delete_lead` | Аналитик | да |
| `list_leads` | Аналитик | нет |

---

## API для агентов (`/api/ops/agents`)

| Метод | Endpoint | Описание |
|---|---|---|
| `GET` | `/api/ops/agents` | Список агентов + статус + промпт |
| `GET` | `/api/ops/agents/{id}/prompt` | Получить промпт (builtin или override) |
| `PUT` | `/api/ops/agents/{id}/prompt` | Сохранить кастомный промпт |
| `DELETE` | `/api/ops/agents/{id}/prompt` | Сбросить к встроенному |
| `POST` | `/api/ops/agents/{id}/run` | Тест-запуск одного агента |

**Промпты:** хранятся в `/backend/data/agent_prompt_{id}.txt` (override). Редактируются через UI `/ops/agents` без рестарта бэкенда.

---

## Changelog

### Апрель 2026 — Усиление агентов (без смены модели)

**Аналитик (`analyst.py`):**
- Добавлен импорт и вызов `read_tasks` — загружает историю задач по лиду (до 8 задач) и передаёт в контекст промпта
- Добавлен тренд скора: показывает предыдущий скор из CRM → текущая эвристика → направление (вырос/упал на N пт)
- Добавлен chain-of-thought в user-message: модель рассуждает пошагово (сначала BANT, потом история задач, потом скор)
- Добавлен few-shot пример хорошего анализа прямо в system prompt — задаёт паттерн качественного ответа
- Увеличен `max_tokens` для `analyze_lead`: 1024 → 1400

**Экономист (`economist.py`):**
- Добавлен импорт `read_lead_by_company`
- Для `update_lead` и `analyze_lead`: обогащает данные из БД (industry, employees, description) — ранее работал только по слотам
- Добавлен chain-of-thought: сначала сегмент/бюджет → потом LTV/вероятность → потом ценообразование

**Маркетолог (`marketer.py`):**
- Добавлен chain-of-thought: сначала профиль покупателя → крючок внимания → письмо

**Технический специалист (`tech_specialist.py`):**
- Добавлен chain-of-thought: сначала стек по отрасли → IT-зрелость → риски → пресейл-вопросы

**Оркестратор (`orchestrator.py`):**
- `update_lead` теперь запускает полный набор агентов: Аналитик + Экономист + Маркетолог + Тех. спец (ранее только Аналитик + Тех. спец)

---

## Hermes — Роутер (не агент)

**Роль:** Парсит текст команды в структурированный JSON (`intent`, `agents`, `slots`, `parallel`, `reply`). Роутит в оркестратор LangGraph.

**Реализация:** `core/hermes.py` → `parse_intent()`.

**LLM:** не привязан «только к Ollama». При наличии `GROQ_API_KEY` используется **Groq** и **Ollama** в порядке, заданном `HERMES_ROUTING_POLICY` (`default` | `local_first`). Локальные модели: `HERMES_MODEL`, `HERMES_FALLBACK` (например `qwen2.5:0.5b` → `qwen2.5:3b`). Дополнительно: fastpath, кэш, post-verify, при отказе LLM — **rescue**-эвристики (CPU-only сценарии). Подробно: `docs/stack/LLM.md`, `docs/RUNBOOK.md`.

**Output формат:**
```json
{
  "intent": "create_lead",
  "agents": ["analyst", "marketer"],
  "slots": {"company": "ACME", "contact": "Иван"},
  "parallel": true,
  "reply": "Краткий ответ пользователю по-русски"
}
```

---

## Dr. QA — эксперименты над Hermes (`core/qa_agent.py`)

**Роль:** методология A/B, гипотезы, статистика и канареечные выкладки для NLU (Hermes), не замена продуктовым агентам CRM.

**Данные:** `backend/data/qa_lab.sqlite3`.

**Связь:** использует те же метрики и скрипты, что описаны в `docs/stack/LLM.md` (rollout, gate). Подробнее — docstring и константы в `qa_agent.py`.
