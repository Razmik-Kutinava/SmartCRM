# LangGraph — Оркестрация агентов

## Что это

LangGraph — фреймворк для построения циклических графов агентов. В отличие от простого LangChain позволяет агентам работать параллельно, передавать данные между собой и принимать решения о следующем шаге.

## Как используем

```python
from langgraph.graph import StateGraph, END

# Состояние системы
class AgentState(TypedDict):
    command: str          # голосовая команда
    intent: dict          # распарсенный интент от Hermes
    analyst_result: str
    marketer_result: str
    economist_result: str
    tech_result: str
    strategist_decision: str  # финальное решение

# Граф агентов
graph = StateGraph(AgentState)
graph.add_node("analyst", analyst_agent)
graph.add_node("marketer", marketer_agent)
graph.add_node("economist", economist_agent)
graph.add_node("tech_specialist", tech_agent)
graph.add_node("strategist", strategist_agent)  # последний

# Параллельный запуск → стратег
graph.add_edge("analyst", "strategist")
graph.add_edge("marketer", "strategist")
graph.add_edge("economist", "strategist")
graph.add_edge("tech_specialist", "strategist")
graph.add_edge("strategist", END)
```

## Параллельность

LangGraph поддерживает `Send` API для параллельного запуска нод. Аналитик, Маркетолог, Экономист и Тех. спец работают одновременно. Стратег ждёт всех и синтезирует.
