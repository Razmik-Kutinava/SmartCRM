# Data — runtime-файлы и кэши

Локальные данные сервера. **Не секреты** — секреты только в `.env`.

---

## Подпапки

| Папка | За что |
|-------|--------|
| `artifacts/` | Вывод скриптов (бенчмарки, eval JSON). В git — только `.gitkeep` |
| `moy_zakupki_cache/` | Кэш ответов API «Мои закупки» |
| `rag_seed/` | Стартовые документы для RAG (`sample.json`, playbook) |

---

## Частые файлы в корне `data/`

| Файл | За что |
|------|--------|
| `api_stats.json` | Счётчики вызовов API |
| `traces.json` | Трейсы Hermes (ops) |
| `checko_cache.json` | Кэш Checko |
| `agent_memory.sqlite3` | Память агента |
| `whisper_settings.json` | Настройки Whisper |
| `hermes_system_prompt.txt` | Копия системного промпта |
| `ops_queue.json` / `ops_snapshots.json` | Очередь ops |
| `tender_sources_*.json` | Бенчмарки источников тендеров |
| `parse_rollout_*.json` | Артефакты rollout Hermes |
| `hermes_kpi_gate_*.json` | KPI-гейты Hermes |

Новый артефакт скрипта → `artifacts/{домен}/`, не сюда в корень без причины.
