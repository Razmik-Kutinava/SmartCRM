# HANDOFF

`Спринт:[Фаза 1] | Задача:[PRD_MAP перепроход /leads] | Статус:п.7 закрыт → п.8`

**Следующий шаг:** **п.8 «Аудит полей»** — перепроход. Ждём `go`.

**Сделано (п.7):**
- Баг: локальная `postLeadComment` вызывала себя (рекурсия) — переименована в `submitComment`
- `frontend/src/lib/leads/leadComments.js` — fetch/create через apiFetch
- API: 400 на пустой/пробельный body после strip
- pytest 7 passed (comments + engagement)

**Коммит:** `ef67ed8`

**Блокеры:** нет 🔴

---
