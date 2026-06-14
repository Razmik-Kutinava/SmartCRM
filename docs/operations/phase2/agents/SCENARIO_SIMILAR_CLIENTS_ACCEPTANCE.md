# Сценарий similar clients — acceptance (Ф2 §2 п.396)

**PRD_MAP:** «Сценарий: похожие клиенты» · **закрывает §2 Оркестрация**

## Было

- «Найди похожих клиентов» шло в leadgen navigate или один analyst без fanout
- Нет modal со списком кандидатов + стратегией захода + апрувом
- Lookalike из won-сделок не был именованным сценарием оркестрации

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `scenarios/similar_clients.py` | intent `find_similar_clients`, analyst+marketer |
| `scenarios/similar_context.py` | портрет из won/эталона + `search_by_portrait` |
| `supervisor` + `rescue` | parallel fanout + CPU «найди похожих клиентов» |
| `analyst` / `marketer` | lookalike + стратегия касаний |
| `strategist` | рекомендация каких лидов добавить |
| `voice_action` | modal `similar_leads`, actions add/reject, route `/leadgen` |
| `VoiceActionHost` | список похожих + кнопка «В лидоген» |

## Критерии

- [x] «найди похожих клиентов» → `find_similar_clients`, analyst+marketer, parallel
- [x] Strategist → modal `payload.synthesis`
- [x] Список `payload.similar_leads` + маркетинговая секция
- [x] pytest зелёный
- [x] Approve «В лидоген» → `POST /api/leads/lookalike-import` (`source: lookalike`)

## Не в scope

- live Checko/Tavily в CI

## Коммит

См. CHANGELOG текущего шага.
