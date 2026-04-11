"""
Разбор файлов для датасетов fine-tune: CSV, JSON, JSONL, PDF (текст → сырые чанки).
"""
from __future__ import annotations

import csv
import io
import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Максимум символов на один PDF-чанк
PDF_CHUNK_CHARS = 4000


def _norm_output(obj: Any) -> dict[str, Any] | None:
    """Приводит output к объекту Hermes-подобного JSON."""
    if obj is None:
        return None
    if isinstance(obj, str):
        try:
            obj = json.loads(obj)
        except json.JSONDecodeError:
            return None
    if not isinstance(obj, dict):
        return None
    # Минимальная валидация
    if "intent" not in obj:
        return None
    out = {
        "intent": obj.get("intent"),
        "agents": obj.get("agents") or ["analyst"],
        "slots": obj.get("slots") if isinstance(obj.get("slots"), dict) else {},
        "parallel": bool(obj.get("parallel", False)),
        "reply": str(obj.get("reply", "")),
    }
    return out


def parse_jsonl(content: bytes) -> tuple[list[tuple[str, dict[str, Any] | None, str]], list[str]]:
    """Возвращает (список (input, output_dict, notes), ошибки построчно)."""
    rows: list[tuple[str, dict[str, Any] | None, str]] = []
    errors: list[str] = []
    text = content.decode("utf-8-sig", errors="replace")
    for i, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"Строка {i}: JSON — {e}")
            continue
        inp = obj.get("input") or obj.get("text") or obj.get("phrase") or obj.get("user")
        out_raw = obj.get("output") or obj.get("expected") or obj.get("assistant")
        if not inp or not str(inp).strip():
            errors.append(f"Строка {i}: нет поля input/text/phrase")
            continue
        notes = str(obj.get("notes", ""))
        out = _norm_output(out_raw)
        if out is None:
            errors.append(f"Строка {i}: невалидный output (нужен JSON с intent)")
            continue
        rows.append((str(inp).strip(), out, notes))
    return rows, errors


def parse_json_array(content: bytes) -> tuple[list[tuple[str, dict[str, Any] | None, str]], list[str]]:
    text = content.decode("utf-8-sig", errors="replace")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return [], [f"JSON: {e}"]
    if not isinstance(data, list):
        return [], ["Ожидается JSON-массив объектов"]
    rows: list[tuple[str, dict[str, Any] | None, str]] = []
    errors: list[str] = []
    for i, obj in enumerate(data, 1):
        if not isinstance(obj, dict):
            errors.append(f"Элемент {i}: не объект")
            continue
        inp = obj.get("input") or obj.get("text") or obj.get("phrase")
        out_raw = obj.get("output") or obj.get("expected")
        if not inp:
            errors.append(f"Элемент {i}: нет input")
            continue
        out = _norm_output(out_raw)
        if out is None:
            errors.append(f"Элемент {i}: невалидный output")
            continue
        rows.append((str(inp).strip(), out, str(obj.get("notes", ""))))
    return rows, errors


def parse_csv(content: bytes) -> tuple[list[tuple[str, dict[str, Any] | None, str]], list[str]]:
    """Колонки: input, output (JSON-строка) или intent + slots_json + reply."""
    text = content.decode("utf-8-sig", errors="replace")
    f = io.StringIO(text)
    reader = csv.DictReader(f)
    if not reader.fieldnames:
        return [], ["Пустой CSV"]
    fields = [h.strip().lower() if h else "" for h in reader.fieldnames]
    rows: list[tuple[str, dict[str, Any] | None, str]] = []
    errors: list[str] = []
    for i, row in enumerate(reader, 1):
        if not row:
            continue
        # нормализуем ключи
        r = { (k or "").strip().lower(): v for k, v in row.items() if k }
        inp = r.get("input") or r.get("text") or r.get("phrase") or r.get("user")
        if not inp or not str(inp).strip():
            errors.append(f"CSV строка {i}: нет input")
            continue
        out: dict[str, Any] | None = None
        if "output" in r and r["output"]:
            out = _norm_output(r["output"])
        elif r.get("intent"):
            slots = {}
            if r.get("slots_json"):
                try:
                    slots = json.loads(r["slots_json"])
                except json.JSONDecodeError:
                    slots = {}
            elif r.get("slots"):
                try:
                    slots = json.loads(r["slots"]) if r["slots"].strip().startswith("{") else {}
                except json.JSONDecodeError:
                    slots = {}
            out = {
                "intent": r["intent"].strip(),
                "agents": ["analyst"],
                "slots": slots if isinstance(slots, dict) else {},
                "parallel": False,
                "reply": (r.get("reply") or "").strip(),
            }
        if out is None:
            errors.append(f"CSV строка {i}: нет output или intent")
            continue
        rows.append((str(inp).strip(), out, r.get("notes", "") or ""))
    return rows, errors


def parse_pdf_raw_chunks(content: bytes) -> tuple[list[tuple[str, dict[str, Any] | None, str]], list[str]]:
    """
    Извлекает текст из PDF, режет на чанки — как raw-записи (без output).
    Пользователь позже размечает или грузит пары отдельным JSONL.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return [], ["Установите пакет pypdf: pip install pypdf"]

    errors: list[str] = []
    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception as e:
        return [], [f"PDF: {e}"]

    full_text: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
            full_text.append(t)
        except Exception as e:
            errors.append(f"Страница: {e}")
    blob = "\n\n".join(full_text).strip()
    if not blob:
        return [], errors + ["В PDF не извлечён текст (скан?)"]

    rows: list[tuple[str, dict[str, Any] | None, str]] = []
    parts = re.split(r"\n{2,}", blob)
    buf = ""
    idx = 0
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(buf) + len(p) > PDF_CHUNK_CHARS and buf:
            idx += 1
            rows.append((buf.strip(), None, f"pdf_chunk_{idx}"))
            buf = p
        else:
            buf = (buf + "\n\n" + p).strip() if buf else p
        while len(buf) > PDF_CHUNK_CHARS:
            idx += 1
            rows.append((buf[:PDF_CHUNK_CHARS].strip(), None, f"pdf_chunk_{idx}"))
            buf = buf[PDF_CHUNK_CHARS:].strip()
    if buf:
        idx += 1
        rows.append((buf.strip(), None, f"pdf_chunk_{idx}"))

    return rows, errors


def detect_format(filename: str) -> str:
    lower = (filename or "").lower()
    if lower.endswith(".pdf"):
        return "pdf"
    if lower.endswith(".jsonl") or lower.endswith(".ndjson"):
        return "jsonl"
    if lower.endswith(".json"):
        return "json"
    if lower.endswith(".csv"):
        return "csv"
    return "unknown"
