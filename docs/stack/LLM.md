# LLM — Groq + Ollama (Qwen + Hermes)

## Схема fallback

```
Запрос → Groq API (быстро, бесплатные токены)
              ↓ если токены кончились / недоступен
         Ollama / Qwen локально (всегда работает)
```

## Модели

| Модель | Где | Для чего |
|--------|-----|----------|
| Groq (llama-3.1-8b / mixtral) | Облако | Основные агентные задачи |
| Qwen2.5:14b | Ollama локально | Fallback, сложные задачи |
| Hermes 3 (Qwen base) | Ollama локально | Роутинг интентов — ВСЕГДА локально |

## Hermes как роутер

Hermes работает локально через Ollama. Он принимает текст команды и возвращает строгий JSON с интентом. Никогда не идёт в облако — приватность данных.

```python
HERMES_SYSTEM_PROMPT = """
Ты — роутер команд CRM системы. 
Получаешь текстовую команду на русском языке.
Возвращаешь ТОЛЬКО JSON без лишнего текста.

Доступные интенты:
- create_lead, update_lead, delete_lead, list_leads
- search_web, add_to_rag
- run_analysis, create_report
- write_email, create_touch_sequence

Формат ответа:
{"intent": "...", "agents": [...], "slots": {...}, "parallel": true/false}
"""
```

## Конфигурация

```env
GROQ_API_KEY=gsk_...
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b
HERMES_MODEL=hermes3:latest
```
