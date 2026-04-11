"""
Ингест файлов и сырого текста в Chroma с чанкингом и метаданными for_agent.
"""
from __future__ import annotations

import logging
import mimetypes
import uuid
from datetime import datetime, timezone
from typing import Any

from rag.chunking import semantic_chunks
from rag.chroma_store import add_documents
from rag import parsers

logger = logging.getLogger(__name__)

# Для какого агента предназначены чанки (или all — видят все)
RAG_FOR_AGENT_ALLOWED = frozenset({
    "all",
    "analyst",
    "strategist",
    "economist",
    "marketer",
    "tech_specialist",
})

PREVIEW_SNIPPET_CHARS = 240
PREVIEW_MAX_CHUNKS = 35


def normalize_for_agent(raw: str | None) -> str:
    v = (raw or "all").strip().lower()
    return v if v in RAG_FOR_AGENT_ALLOWED else "all"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _snippet(text: str, n: int = PREVIEW_SNIPPET_CHARS) -> str:
    s = text.replace("\n", " ").strip()
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


def build_chunk_previews(
    chunks: list[tuple[str, dict[str, Any]]],
    limit: int = PREVIEW_MAX_CHUNKS,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, (chunk_text, meta) in enumerate(chunks[:limit]):
        out.append({
            "chunk_index": meta.get("chunk_index", i),
            "paragraph_index": meta.get("paragraph_index"),
            "chars": len(chunk_text),
            "for_agent": str(meta.get("for_agent", "all")),
            "sheet": meta.get("sheet"),
            "json_path": meta.get("json_path"),
            "snippet": _snippet(chunk_text),
        })
    return out


def _ingest_plain_text(
    text: str,
    *,
    filename: str,
    source_type: str,
    mime: str,
    tags: str = "",
    for_agent: str = "all",
    extra_base_meta: dict[str, Any] | None = None,
    steps_pre: list[dict[str, Any]] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    source_id = str(uuid.uuid4())
    for_agent = normalize_for_agent(for_agent)
    base: dict[str, Any] = {
        "source_id": source_id,
        "filename": filename,
        "source_type": source_type,
        "mime": mime,
        "uploaded_at": _now_iso(),
        "tags": tags or "",
        "for_agent": for_agent,
    }
    if extra_base_meta:
        base.update(extra_base_meta)

    steps: list[dict[str, Any]] = list(steps_pre or [])
    text = text.strip()
    if not text:
        return {
            "source_id": source_id if not dry_run else None,
            "chunks": 0,
            "filename": filename,
            "for_agent": for_agent,
            "message": "пустой текст",
            "steps": steps,
            "chunk_previews": [],
            "dry_run": dry_run,
        }

    chunks = semantic_chunks(text, base)
    steps.append({
        "stage": "Чанкинг",
        "detail": "Абзацы → предложения → лимит символов и перекрытие предложений",
        "chunks_total": len(chunks),
        "for_agent": for_agent,
    })
    previews = build_chunk_previews(chunks)

    if dry_run:
        return {
            "source_id": None,
            "chunks": len(chunks),
            "filename": filename,
            "for_agent": for_agent,
            "steps": steps,
            "chunk_previews": previews,
            "dry_run": True,
        }

    texts = [c[0] for c in chunks]
    metas = [c[1] for c in chunks]
    ids = [f"{source_id}_{i}" for i in range(len(chunks))]
    n = add_documents(texts, metas, ids)
    logger.info("RAG ingest: %s чанков, source_id=%s file=%s agent=%s", n, source_id, filename, for_agent)
    return {
        "source_id": source_id,
        "chunks": n,
        "filename": filename,
        "for_agent": for_agent,
        "steps": steps,
        "chunk_previews": previews,
        "dry_run": False,
    }


def _looks_like_pdf(data: bytes) -> bool:
    """Распознавание PDF даже если имя файла без .pdf (браузер отдал octet-stream)."""
    return len(data) >= 4 and data.startswith(b"%PDF")


def ingest_bytes(
    data: bytes,
    filename: str,
    content_type: str | None = None,
    tags: str = "",
    for_agent: str = "all",
    dry_run: bool = False,
) -> dict[str, Any]:
    mime = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    fn_lower = filename.lower()
    for_agent = normalize_for_agent(for_agent)

    is_pdf = fn_lower.endswith(".pdf") or mime == "application/pdf" or _looks_like_pdf(data)
    if is_pdf:
        try:
            text = parsers.parse_pdf(data)
        except ImportError as e:
            logger.warning("PDF ImportError: %s", e)
            return {"error": str(e), "chunks": 0, "steps": [], "chunk_previews": []}
        except Exception as e:
            logger.warning("PDF parse error (%s): %s", filename, e)
            return {
                "error": f"PDF не удалось разобрать (повреждён, зашифрован или нестандартный): {e}",
                "chunks": 0,
                "steps": [],
                "chunk_previews": [],
            }
        steps_pre = [{
            "stage": "Извлечение текста",
            "format": "PDF",
            "bytes": len(data),
            "chars_extracted": len(text),
        }]
        if not (text or "").strip():
            logger.warning("PDF без текстового слоя: %s", filename)
            return {
                "error": (
                    "Из PDF не извлечён текст: файл является сканом страниц без текстового слоя. "
                    "Нужен OCR или сохраните документ в .txt / .docx."
                ),
                "chunks": 0,
                "steps": steps_pre,
                "chunk_previews": [],
            }
        return _ingest_plain_text(
            text,
            filename=filename,
            source_type="file",
            mime=mime,
            tags=tags,
            for_agent=for_agent,
            steps_pre=steps_pre,
            dry_run=dry_run,
        )

    if fn_lower.endswith(".docx"):
        try:
            text = parsers.parse_docx(data)
        except ImportError as e:
            logger.warning("DOCX ImportError: %s", e)
            return {"error": str(e), "chunks": 0, "steps": [], "chunk_previews": []}
        except Exception as e:
            logger.warning("DOCX parse error (%s): %s", filename, e)
            return {"error": f"DOCX: {e}", "chunks": 0, "steps": [], "chunk_previews": []}
        steps_pre = [{
            "stage": "Извлечение текста",
            "format": "Word DOCX",
            "bytes": len(data),
            "chars_extracted": len(text),
        }]
        if not (text or "").strip():
            return {"error": "DOCX без текста", "chunks": 0, "steps": steps_pre, "chunk_previews": []}
        return _ingest_plain_text(
            text,
            filename=filename,
            source_type="file",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            tags=tags,
            for_agent=for_agent,
            steps_pre=steps_pre,
            dry_run=dry_run,
        )

    if fn_lower.endswith(".csv"):
        try:
            blocks = parsers.parse_csv(data)
        except Exception as e:
            logger.warning("CSV parse error (%s): %s", filename, e)
            return {"error": f"CSV: {e}", "chunks": 0, "steps": [], "chunk_previews": []}
        if not blocks:
            return {"error": "CSV без данных", "chunks": 0, "steps": [], "chunk_previews": []}
        steps_pre = [{
            "stage": "Извлечение текста",
            "format": "CSV",
            "bytes": len(data),
            "sheets_blocks": len(blocks),
        }]
        source_id_csv = str(uuid.uuid4()) if not dry_run else None
        uploaded_csv = _now_iso()
        all_texts_csv: list[str] = []
        all_metas_csv: list[dict[str, Any]] = []
        all_ids_csv: list[str] = []
        g_csv = 0
        cp_csv: list[tuple[str, dict[str, Any]]] = []
        for sheet_name, block in blocks:
            base = {
                "source_id": source_id_csv or "preview",
                "filename": filename,
                "source_type": "file",
                "mime": "text/csv",
                "uploaded_at": uploaded_csv,
                "sheet": sheet_name,
                "tags": tags or "",
                "for_agent": for_agent,
            }
            for chunk_text, meta in semantic_chunks(block, base):
                cp_csv.append((chunk_text, {**meta, "chunk_index": g_csv}))
                if not dry_run:
                    all_texts_csv.append(chunk_text)
                    all_metas_csv.append({**meta, "chunk_index": g_csv})
                    all_ids_csv.append(f"{source_id_csv}_{g_csv}")
                g_csv += 1
        steps_csv = list(steps_pre)
        steps_csv.append({"stage": "Чанкинг", "chunks_total": len(cp_csv), "for_agent": for_agent})
        previews_csv = build_chunk_previews(cp_csv)
        if dry_run:
            return {"source_id": None, "chunks": len(cp_csv), "filename": filename,
                    "for_agent": for_agent, "steps": steps_csv, "chunk_previews": previews_csv, "dry_run": True}
        assert source_id_csv is not None
        n_csv = add_documents(all_texts_csv, all_metas_csv, all_ids_csv)
        logger.info("RAG ingest csv: %s чанков source_id=%s", n_csv, source_id_csv)
        return {"source_id": source_id_csv, "chunks": n_csv, "filename": filename,
                "for_agent": for_agent, "steps": steps_csv, "chunk_previews": previews_csv, "dry_run": False}

    if fn_lower.endswith(".xlsx") or fn_lower.endswith(".xlsm"):
        try:
            blocks = parsers.parse_xlsx(data)
        except ImportError as e:
            logger.warning("Excel ImportError: %s", e)
            return {"error": str(e), "chunks": 0, "steps": [], "chunk_previews": []}
        if not blocks:
            return {"error": "Excel без данных", "chunks": 0, "steps": [], "chunk_previews": []}
        steps_pre = [{
            "stage": "Извлечение текста",
            "format": "Excel",
            "bytes": len(data),
            "sheets_blocks": len(blocks),
        }]
        source_id = str(uuid.uuid4()) if not dry_run else None
        uploaded = _now_iso()
        all_texts: list[str] = []
        all_metas: list[dict[str, Any]] = []
        all_ids: list[str] = []
        global_idx = 0
        chunk_pairs: list[tuple[str, dict[str, Any]]] = []
        for sheet_name, block in blocks:
            base = {
                "source_id": source_id or "preview",
                "filename": filename,
                "source_type": "file",
                "mime": mime,
                "uploaded_at": uploaded,
                "sheet": sheet_name,
                "tags": tags or "",
                "for_agent": for_agent,
            }
            for chunk_text, meta in semantic_chunks(block, base):
                chunk_pairs.append((chunk_text, {**meta, "chunk_index": global_idx}))
                if not dry_run:
                    all_texts.append(chunk_text)
                    all_metas.append({**meta, "chunk_index": global_idx})
                    all_ids.append(f"{source_id}_{global_idx}")
                global_idx += 1
        steps = list(steps_pre)
        steps.append({
            "stage": "Чанкинг",
            "detail": "По листам и строкам, затем смысловые границы",
            "chunks_total": len(chunk_pairs),
            "for_agent": for_agent,
        })
        previews = build_chunk_previews(chunk_pairs)
        if dry_run:
            return {
                "source_id": None,
                "chunks": len(chunk_pairs),
                "filename": filename,
                "for_agent": for_agent,
                "steps": steps,
                "chunk_previews": previews,
                "dry_run": True,
            }
        assert source_id is not None
        n = add_documents(all_texts, all_metas, all_ids)
        logger.info("RAG ingest xlsx: %s чанков source_id=%s", n, source_id)
        return {
            "source_id": source_id,
            "chunks": n,
            "filename": filename,
            "for_agent": for_agent,
            "steps": steps,
            "chunk_previews": previews,
            "dry_run": False,
        }

    if fn_lower.endswith(".json") or "json" in mime:
        try:
            pairs = parsers.parse_json_bytes(data)
        except Exception as e:
            return {"error": f"JSON: {e}", "chunks": 0, "steps": [], "chunk_previews": []}
        steps_pre = [{
            "stage": "Разбор JSON",
            "bytes": len(data),
            "logical_fragments": len(pairs),
        }]
        source_id = str(uuid.uuid4()) if not dry_run else None
        uploaded = _now_iso()
        all_texts: list[str] = []
        all_metas: list[dict[str, Any]] = []
        all_ids: list[str] = []
        g = 0
        chunk_pairs: list[tuple[str, dict[str, Any]]] = []
        for path_hint, fragment in pairs:
            base = {
                "source_id": source_id or "preview",
                "filename": filename,
                "source_type": "file",
                "mime": mime,
                "uploaded_at": uploaded,
                "json_path": path_hint[:500],
                "tags": tags or "",
                "for_agent": for_agent,
            }
            for chunk_text, meta in semantic_chunks(fragment, base):
                chunk_pairs.append((chunk_text, {**meta, "chunk_index": g}))
                if not dry_run:
                    all_texts.append(chunk_text)
                    all_metas.append({**meta, "chunk_index": g})
                    all_ids.append(f"{source_id}_{g}")
                g += 1
        if not chunk_pairs:
            return {"error": "JSON пустой", "chunks": 0, "steps": steps_pre, "chunk_previews": []}
        steps = list(steps_pre)
        steps.append({
            "stage": "Чанкинг",
            "chunks_total": len(chunk_pairs),
            "for_agent": for_agent,
        })
        previews = build_chunk_previews(chunk_pairs)
        if dry_run:
            return {
                "source_id": None,
                "chunks": len(chunk_pairs),
                "filename": filename,
                "for_agent": for_agent,
                "steps": steps,
                "chunk_previews": previews,
                "dry_run": True,
            }
        assert source_id is not None
        n = add_documents(all_texts, all_metas, all_ids)
        return {
            "source_id": source_id,
            "chunks": n,
            "filename": filename,
            "for_agent": for_agent,
            "steps": steps,
            "chunk_previews": previews,
            "dry_run": False,
        }

    if fn_lower.endswith(".txt") or fn_lower.endswith(".md") or mime.startswith("text/"):
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("cp1251", errors="replace")
        steps_pre = [{
            "stage": "Извлечение текста",
            "format": "текст",
            "bytes": len(data),
            "chars_extracted": len(text),
        }]
        return _ingest_plain_text(
            text,
            filename=filename,
            source_type="file",
            mime=mime,
            tags=tags,
            for_agent=for_agent,
            steps_pre=steps_pre,
            dry_run=dry_run,
        )

    # Fallback — пытаемся прочитать любой файл как текст
    try:
        text_fb = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text_fb = data.decode("cp1251", errors="replace")
        except Exception:
            text_fb = ""
    if text_fb.strip():
        logger.info("RAG ingest fallback plaintext: %s", filename)
        steps_pre = [{
            "stage": "Извлечение текста",
            "format": "текст (fallback)",
            "bytes": len(data),
            "chars_extracted": len(text_fb),
        }]
        return _ingest_plain_text(
            text_fb,
            filename=filename,
            source_type="file",
            mime=mime,
            tags=tags,
            for_agent=for_agent,
            steps_pre=steps_pre,
            dry_run=dry_run,
        )
    return {"error": f"Неподдерживаемый формат: {mime} ({fn_lower})", "chunks": 0, "steps": [], "chunk_previews": []}


def ingest_manual_text(
    text: str,
    title: str = "manual",
    tags: str = "",
    for_agent: str = "all",
    dry_run: bool = False,
) -> dict[str, Any]:
    steps_pre = [{"stage": "Ввод", "format": "текст вручную", "chars": len(text)}]
    return _ingest_plain_text(
        text.strip(),
        filename=title or "manual",
        source_type="manual",
        mime="text/plain",
        tags=tags,
        for_agent=for_agent,
        steps_pre=steps_pre,
        dry_run=dry_run,
    )


def ingest_json_object(
    obj: Any,
    title: str = "data.json",
    tags: str = "",
    for_agent: str = "all",
    dry_run: bool = False,
) -> dict[str, Any]:
    pairs = parsers.json_obj_to_chunks(obj)
    if not pairs:
        return {"error": "Пустой JSON", "chunks": 0, "steps": [], "chunk_previews": []}
    for_agent = normalize_for_agent(for_agent)
    steps_pre = [{"stage": "Разбор JSON", "logical_fragments": len(pairs)}]
    source_id = str(uuid.uuid4()) if not dry_run else None
    uploaded = _now_iso()
    mime = "application/json"
    all_texts: list[str] = []
    all_metas: list[dict[str, Any]] = []
    all_ids: list[str] = []
    g = 0
    chunk_pairs: list[tuple[str, dict[str, Any]]] = []
    for path_hint, fragment in pairs:
        base = {
            "source_id": source_id or "preview",
            "filename": title,
            "source_type": "manual_json",
            "mime": mime,
            "uploaded_at": uploaded,
            "json_path": path_hint[:500],
            "tags": tags or "",
            "for_agent": for_agent,
        }
        for chunk_text, meta in semantic_chunks(fragment, base):
            chunk_pairs.append((chunk_text, {**meta, "chunk_index": g}))
            if not dry_run:
                all_texts.append(chunk_text)
                all_metas.append({**meta, "chunk_index": g})
                all_ids.append(f"{source_id}_{g}")
            g += 1
    steps = list(steps_pre)
    steps.append({"stage": "Чанкинг", "chunks_total": len(chunk_pairs), "for_agent": for_agent})
    previews = build_chunk_previews(chunk_pairs)
    if dry_run:
        return {
            "source_id": None,
            "chunks": len(chunk_pairs),
            "filename": title,
            "for_agent": for_agent,
            "steps": steps,
            "chunk_previews": previews,
            "dry_run": True,
        }
    assert source_id is not None
    n = add_documents(all_texts, all_metas, all_ids)
    return {
        "source_id": source_id,
        "chunks": n,
        "filename": title,
        "for_agent": for_agent,
        "steps": steps,
        "chunk_previews": previews,
        "dry_run": False,
    }
