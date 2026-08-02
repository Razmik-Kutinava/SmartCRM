# todo — микро-чеклист текущей фичи

## Заказ (дословно)

> «да, теперь делай эти шаги и добавь эти две возможности»
> (BuiltWith для теха как данные + WhoIs/DNS в 🔍; не тулзы у агентов)

**Как понял:** в шаге 🔍 дотянуть BuiltWith в `tech_json`/слоты теха + добавить WhoIs/DNS (MX/SPF/домен) в исследование; агенты только читают.

## Чеклист фазы

- [ ] **🔍 BuiltWith + WhoIs/DNS** · проводка в research → passport/tech → слоты · (пункт `[x]` — после «ок»)

## Чеклист микро

- [x] WhoIs/DNS модуль (DoH + RDAP, без ключа)
- [x] BuiltWith при наличии сайта даже без ИНН (через domain_enrich в research)
- [x] Merge tech + domain_signals в passport / web_research / techJson
- [x] Слоты/gaps теха видят стек и DNS-сигналы
- [x] Тесты + регрессия rag/agents + ops

## Не вошло

Hunter в этом шаге. DDG. Тендеры.
