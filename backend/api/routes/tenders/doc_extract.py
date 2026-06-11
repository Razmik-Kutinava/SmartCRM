"""Извлечение текста из тендерных документов (PDF/DOCX/XLSX) без RAG."""
from __future__ import annotations

import mimetypes
import os

from rag import parsers
from rag.ingest import _looks_like_pdf

MAX_CHARS = int(os.getenv("TENDER_DOC_MAX_CHARS", "80000"))


def _truncate(text: str) -> tuple[str, bool]:
    t = (text or "").strip()
    if len(t) <= MAX_CHARS:
        return t, False
    return t[:MAX_CHARS] + "\n\n[… текст обрезан …]", True


def extract_document_text(
    data: bytes,
    filename: str,
    content_type: str | None = None,
) -> dict:
    """Возвращает {filename, format, text, chars, truncated} или {error}."""
    if not data:
        return {"error": "Пустой файл"}
    mime = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    fn_lower = (filename or "upload").lower()

    try:
        if fn_lower.endswith(".pdf") or mime == "application/pdf" or _looks_like_pdf(data):
            text = parsers.parse_pdf(data)
            fmt = "PDF"
        elif fn_lower.endswith(".docx"):
            text = parsers.parse_docx(data)
            fmt = "DOCX"
        elif fn_lower.endswith(".xlsx"):
            blocks = parsers.parse_xlsx(data)
            text = "\n\n".join(f"### Лист: {name}\n{body}" for name, body in blocks)
            fmt = "XLSX"
        elif fn_lower.endswith((".txt", ".md")):
            text = data.decode("utf-8-sig", errors="replace")
            fmt = "TEXT"
        elif fn_lower.endswith(".doc"):
            return {"error": "Формат .doc не поддерживается — сохраните как .docx или .pdf"}
        else:
            return {"error": f"Неподдерживаемый формат: {filename}"}
    except ImportError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Не удалось извлечь текст: {e}"}

    if not (text or "").strip():
        return {
            "error": (
                "Текст не извлечён (скан без OCR или пустой документ). "
                "Попробуйте .docx или текстовый PDF."
            ),
            "format": fmt,
        }

    text, truncated = _truncate(text)
    return {
        "filename": filename,
        "format": fmt,
        "text": text,
        "chars": len(text),
        "truncated": truncated,
    }
