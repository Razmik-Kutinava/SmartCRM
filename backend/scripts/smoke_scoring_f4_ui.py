#!/usr/bin/env python3
"""Смоук Ф4 баллы: сортировка списка, флаги API, UI-страницы (pytest + live HTTP)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent

PYTEST_PATHS = [
    "tests/lib/test_lead_list_filter.py",
    "tests/core/test_lead_score_list_flags.py",
    "tests/api/test_leads_api.py::test_list_leads_includes_score_advisory_flags",
    "tests/smoke/test_lead_card_page.py",
]


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(BACKEND / ".env")
    load_dotenv(REPO_ROOT / ".env", override=True)


def _api_base() -> str:
    return (os.getenv("SMARTCRM_API_BASE") or "http://127.0.0.1:8000").rstrip("/")


def _api_key() -> str:
    return (os.getenv("SMARTCRM_API_KEY") or os.getenv("PUBLIC_SMARTCRM_API_KEY") or "").strip()


def _frontend_base() -> str | None:
    if os.environ.get("SCORING_F4_SMOKE_FRONTEND_URL"):
        return os.environ["SCORING_F4_SMOKE_FRONTEND_URL"].rstrip("/")
    for port in (5173, 5174, 4173):
        base = f"http://127.0.0.1:{port}"
        try:
            with urlopen(Request(f"{base}/leads/list", method="GET"), timeout=2) as r:
                if r.status in (200, 308):
                    return base
        except OSError:
            continue
    return None


def _live_api_smoke() -> bool:
    key = _api_key()
    if not key:
        print("live API skip: нет SMARTCRM_API_KEY в .env")
        return True
    url = f"{_api_base()}/api/leads"
    req = Request(url, headers={"X-API-Key": key})
    try:
        with urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        print(f"live API FAIL: {e.code} {e.reason}")
        return False
    except URLError as e:
        print(f"live API FAIL: {e.reason}")
        return False
    if not isinstance(data, list):
        print("live API FAIL: ожидали массив лидов")
        return False
    if data:
        row = data[0]
        need = ("hasScoreWarnings", "scoreDivergent", "scoreDelta", "suggestedScore")
        missing = [k for k in need if k not in row]
        if missing:
            print(f"live API FAIL: в лиде нет полей {missing}")
            return False
    print(f"live API OK: GET /api/leads ({len(data)} rows, флаги advisory)")
    return True


def _live_ops_crm_smoke() -> bool:
    key = _api_key()
    if not key:
        return True
    url = f"{_api_base()}/api/ops/crm-settings"
    req = Request(url, headers={"X-API-Key": key})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError) as e:
        print(f"live ops FAIL: {e}")
        return False
    settings = data.get("settings") or {}
    if "scoring_advisory_enabled" not in settings:
        print("live ops FAIL: нет scoring_advisory_enabled в settings")
        return False
    print("live ops OK: GET /api/ops/crm-settings (scoring_advisory)")
    return True


def _frontend_pages_smoke() -> bool:
    base = _frontend_base()
    if not base:
        print("frontend skip (Vite не запущен — DevTools smoke отдельно)")
        return True
    pages = (
        "/leads/list",
        "/ops/crm",
    )
    for path in pages:
        try:
            with urlopen(Request(f"{base}{path}", method="GET"), timeout=5) as r:
                html = r.read(512).decode("utf-8", errors="replace")
        except OSError as e:
            print(f"frontend FAIL {path}: {e}")
            return False
        if r.status not in (200, 308):
            print(f"frontend FAIL {path}: HTTP {r.status}")
            return False
        if len(html) < 50:
            print(f"frontend FAIL {path}: пустой ответ")
            return False
    print(f"frontend OK: {base}/leads/list + /ops/crm (HTTP 200)")
    return True


def _frontend_lead_card_smoke() -> bool:
    base = _frontend_base()
    key = _api_key()
    if not base or not key:
        return True
    url = f"{_api_base()}/api/leads"
    try:
        with urlopen(Request(url, headers={"X-API-Key": key}), timeout=20) as resp:
            rows = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError) as e:
        print(f"frontend lead card FAIL: API leads — {e}")
        return False
    if not rows:
        print("frontend lead card skip: нет лидов")
        return True
    lid = rows[0].get("id")
    if not lid:
        print("frontend lead card FAIL: нет id у первого лида")
        return False
    path = f"/leads/{lid}"
    try:
        with urlopen(Request(f"{base}{path}", method="GET"), timeout=8) as r:
            html = r.read(1024).decode("utf-8", errors="replace")
    except OSError as e:
        print(f"frontend lead card FAIL {path}: {e}")
        return False
    if r.status not in (200, 308):
        print(f"frontend lead card FAIL {path}: HTTP {r.status}")
        return False
    if len(html) < 50:
        print(f"frontend lead card FAIL {path}: пустой ответ")
        return False
    print(f"frontend OK: {base}{path} (HTTP 200)")
    return True


def main() -> int:
    _load_env()
    print("SmartCRM smoke — Ф4 баллы (сортировка + UI)\n")
    cmd = [sys.executable, "-m", "pytest", *PYTEST_PATHS, "-q", "--tb=short"]
    if subprocess.run(cmd, cwd=BACKEND).returncode != 0:
        print("\nScoring F4 UI smoke: FAIL (pytest)")
        return 1
    if not _live_api_smoke():
        print("\nScoring F4 UI smoke: FAIL (live API)")
        return 1
    if not _live_ops_crm_smoke():
        print("\nScoring F4 UI smoke: FAIL (live ops)")
        return 1
    if not _frontend_pages_smoke():
        print("\nScoring F4 UI smoke: FAIL (frontend)")
        return 1
    if not _frontend_lead_card_smoke():
        print("\nScoring F4 UI smoke: FAIL (frontend lead card)")
        return 1
    print("\nScoring F4 UI smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
