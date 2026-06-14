# Ф2 §2 п.1 — LangGraph supervisor (выборочный fanout)

## Scope

Supervisor выбирает **подмножество** агентов по `Hermes.agents[]` или дефолту intent.  
LangGraph: `supervisor → fanout → strategist`.

## Команда

```bash
cd backend
python -m pytest tests/agents/test_supervisor.py tests/test_voice_pipeline.py -q
```

## Не в scope (следующие пункты §2)

- Именованные сценарии (анализ+письмо, тендер, отчёт, похожие клиенты)
- Синтез в модалку voice_action (п.392 MAP)
- LLM-supervisor (выбор агентов через отдельный LLM-вызов)
