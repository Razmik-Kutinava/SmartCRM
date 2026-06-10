#!/usr/bin/env python3
"""Смоук PRD_MAP «Лидогенерация» — автосохранение в CRM при скор ≥ порога."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
_REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
OUT = BACKEND / "data" / "artifacts" / "leadgen" / "autosave_smoke.json"

PYTEST = [
    "tests/leadgen/test_autosave.py",
    "tests/api/test_leadgen_autosave_api.py",
]


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
        load_dotenv(_REPO_ROOT / ".env", override=True)
    except ImportError:
        pass


def _probe(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _config_threshold() -> int:
    from leadgen.crm_threshold import get_crm_score_threshold

    return get_crm_score_threshold()


def main() -> int:
    _load_env()
    print("SmartCRM smoke — leadgen автосохранение в CRM\n")

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST, "-q", "--tb=short"],
        cwd=BACKEND,
    )
    if proc.returncode != 0:
        print("\nsmoke_leadgen_autosave: FAIL (pytest)")
        return 1

    threshold = _config_threshold()
    payload: dict = {
        "pytest": True,
        "crm_score_threshold": threshold,
        "backend": _probe("http://127.0.0.1:8000/docs"),
        "frontend_leadgen": _probe("http://127.0.0.1:5173/leadgen"),
        "gaps": [],
    }
    if not payload["backend"]:
        payload["gaps"].append("backend :8000 не отвечает — live E2E вручную")
    if not payload["frontend_leadgen"]:
        payload["gaps"].append("frontend :5173/leadgen не отвечает — DevTools E2E вручную")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nПорог автосейва: {threshold}")
    print(f"Артефакт: {OUT.relative_to(_REPO_ROOT)}")
    print("smoke_leadgen_autosave: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
