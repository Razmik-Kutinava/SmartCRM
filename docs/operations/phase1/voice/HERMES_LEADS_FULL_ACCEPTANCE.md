# Полный набор интентов по лидам — acceptance (2026-06-08)

## Scope (PRD_MAP п.4)

История, аналитика лида, расширенные фильтры списка.

## Команда

```powershell
cd backend; python scripts/smoke_hermes_leads_full.py
```

34 pytest (extended rescue + lead_list_view + lead_context + voice_action + базовый rescue).

## Новые / расширенные интенты

| Интент | Пример | UI |
|--------|--------|-----|
| `analyze_lead` | «проанализируй лид ООО Ромашка» | fanout агентов → `voice_action` modal |
| `lead_history` | «покажи историю по лиду Ромашка» | audit/comments/comms → modal + `/leads/{id}` |
| `list_leads` + слоты | `stage`, `industry`, `city` | `voice_action` filter на списке |

## Файлы

| Зона | Путь |
|------|------|
| Фильтры list | `core/hermes/lead_list_view.py` |
| История | `voice/lead_context.py`, `agents/tools.py` (audit API) |
| Hermes | `prompts_data.py`, `rescue.py`, `cache.py`, `slot_normalize.py` |
| Фронт фильтры | `lib/leads/leadListFilter.js`, `leads/list/+page.svelte` |
| Модалка истории | `VoiceActionHost.svelte` |

## Хвост (BACKLOG)

- Извлечение `company` из «по лиду Ромашка» без кавычек в rescue (сейчас LLM / уточнение)
- Голосовой `add_communication` / комментарий к лиду
- Фильтр по динамическим стадиям CRM (fuzzy match с `crm_settings`)
- LLM eval-кейсы для `analyze_lead` / `lead_history`
- Чипы industry/city в UI списка (сейчас только логика фильтра)
- E2E смоук п.5 (`langgraph.md`)
