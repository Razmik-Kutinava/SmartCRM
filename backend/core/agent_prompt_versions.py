"""Git-like версии override-промптов агентов (backend/data/prompt_versions/)."""

from __future__ import annotations

import difflib
import hashlib
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_DATA = Path(__file__).resolve().parent.parent / "data" / "prompt_versions"
_MAX_VERSIONS = 50


def _agent_dir(agent_id: str) -> Path:
    d = _DATA / agent_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _manifest_path(agent_id: str) -> Path:
    return _agent_dir(agent_id) / "manifest.json"


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _load_manifest(agent_id: str) -> list[dict[str, Any]]:
    path = _manifest_path(agent_id)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("prompt_versions manifest %s: %s", agent_id, e)
    return []


def _save_manifest(agent_id: str, manifest: list[dict[str, Any]]) -> None:
    _manifest_path(agent_id).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=0),
        encoding="utf-8",
    )


def _prune_old(agent_id: str, manifest: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(manifest) <= _MAX_VERSIONS:
        return manifest
    drop = manifest[: len(manifest) - _MAX_VERSIONS]
    for entry in drop:
        vid = entry.get("id")
        if vid:
            p = _agent_dir(agent_id) / f"{vid}.txt"
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass
    return manifest[-_MAX_VERSIONS:]


def list_versions(agent_id: str) -> list[dict[str, Any]]:
    with _LOCK:
        manifest = _load_manifest(agent_id)
    out: list[dict[str, Any]] = []
    for entry in reversed(manifest):
        ts = float(entry.get("ts") or 0)
        out.append({
            "id": entry.get("id"),
            "ts": ts,
            "chars": entry.get("chars", 0),
            "note": entry.get("note", ""),
            "preview": entry.get("preview", ""),
            "age_min": round((time.time() - ts) / 60) if ts else 0,
        })
    return out


def save_version(agent_id: str, text: str, *, note: str = "save") -> str | None:
    text = (text or "").strip()
    if len(text) < 50:
        return None
    h = _content_hash(text)
    with _LOCK:
        manifest = _load_manifest(agent_id)
        if manifest and manifest[-1].get("hash") == h:
            return str(manifest[-1]["id"])
        vid = f"v{len(manifest) + 1:06d}"
        (_agent_dir(agent_id) / f"{vid}.txt").write_text(text, encoding="utf-8")
        manifest.append({
            "id": vid,
            "ts": time.time(),
            "chars": len(text),
            "hash": h,
            "note": note,
            "preview": text[:120],
        })
        manifest = _prune_old(agent_id, manifest)
        _save_manifest(agent_id, manifest)
    logger.info("prompt version %s/%s (%s симв., %s)", agent_id, vid, len(text), note)
    return vid


def get_version_text(agent_id: str, version_id: str) -> str | None:
    path = _agent_dir(agent_id) / f"{version_id}.txt"
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def compare_texts(left: str, right: str, *, left_label: str = "left", right_label: str = "right") -> dict[str, Any]:
    left_lines = (left or "").splitlines()
    right_lines = (right or "").splitlines()
    diff = list(
        difflib.unified_diff(
            left_lines,
            right_lines,
            fromfile=left_label,
            tofile=right_label,
            lineterm="",
        )
    )
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    return {
        "left_chars": len(left or ""),
        "right_chars": len(right or ""),
        "left_lines": len(left_lines),
        "right_lines": len(right_lines),
        "added_lines": added,
        "removed_lines": removed,
        "diff": diff[:300],
    }
