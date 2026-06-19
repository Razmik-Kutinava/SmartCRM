#!/usr/bin/env python3
"""Смоук P3: экспорт отчёта по баллам и воронке (pytest + live HTTP xlsx)."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent

PYTEST_PATHS = [
    "tests/core/test_scoring_funnel_report.py",
    "tests/core/test_export_reports.py",
    "tests/api/test_leads_scoring_export_api.py",
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


def _live_xlsx_smoke() -> bool:
    key = _api_key()
    if not key:
        print("live HTTP skip: нет SMARTCRM_API_KEY в .env")
        return True
    url = f"{_api_base()}/api/leads/scoring/export?format=xlsx"
    req = Request(url, headers={"X-API-Key": key})
    try:
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
    except HTTPError as e:
        print(f"live HTTP FAIL: {e.code} {e.reason}")
        return False
    except URLError as e:
        print(f"live HTTP FAIL: {e.reason}")
        return False
    if data[:2] != b"PK":
        print("live HTTP FAIL: ответ не похож на xlsx (нет PK)")
        return False
    try:
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(data), read_only=True)
        names = set(wb.sheetnames)
        need = {"KPI", "FunnelScores", "Leads"}
        if not need.issubset(names):
            print(f"live HTTP FAIL: листы {names}, ожидали {need}")
            return False
        ws = wb["Leads"]
        header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
        if "managerScore" not in header:
            print(f"live HTTP FAIL: заголовок Leads без managerScore: {header}")
            return False
    except Exception as e:
        print(f"live HTTP FAIL: openpyxl — {e}")
        return False
    print(f"live HTTP OK: xlsx {len(data)} bytes, листы KPI/FunnelScores/Leads")
    return True


def _frontend_url() -> str | None:
    if os.environ.get("SCORING_EXPORT_SMOKE_FRONTEND_URL"):
        return os.environ["SCORING_EXPORT_SMOKE_FRONTEND_URL"].rstrip("/")
    for port in (5173, 5174, 4173):
        base = f"http://127.0.0.1:{port}"
        try:
            with urlopen(Request(f"{base}/leads/analytics", method="GET"), timeout=2) as r:
                if r.status in (200, 308):
                    return base
        except OSError:
            continue
    return None


def main() -> int:
    _load_env()
    print("SmartCRM smoke — экспорт баллов и воронки\n")
    cmd = [sys.executable, "-m", "pytest", *PYTEST_PATHS, "-q", "--tb=short"]
    if subprocess.run(cmd, cwd=BACKEND).returncode != 0:
        print("\nScoring export smoke: FAIL (pytest)")
        return 1
    if not _live_xlsx_smoke():
        print("\nScoring export smoke: FAIL (live HTTP)")
        return 1
    base = _frontend_url()
    if base:
        print(f"frontend OK: {base}/leads/analytics (кнопка «Баллы»)")
    else:
        print("frontend skip (Vite не запущен — UI smoke отдельно)")
    print("\nScoring export smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
