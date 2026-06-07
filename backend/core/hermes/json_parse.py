"""Hermes — парсинг JSON из ответа модели."""
import json


def parse_json(text: str) -> dict | None:
    """Пытается распарсить JSON из ответа модели."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            parsed = parsed[0] if parsed else None
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception:
                pass
    return None
