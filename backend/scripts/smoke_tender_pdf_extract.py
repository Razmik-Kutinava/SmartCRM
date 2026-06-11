#!/usr/bin/env python3
"""Live-смоук POST /api/tenders/documents/extract (PDF → текст)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
FIXTURE = BACKEND / "tests" / "fixtures" / "tenders" / "sample_tz.pdf"
DEFAULT_API = "http://127.0.0.1:8000"


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
        load_dotenv(REPO_ROOT / ".env", override=True)
    except ImportError:
        pass


def _api_key() -> str:
    return (os.getenv("SMARTCRM_API_KEY") or "").strip()


def _post_extract(api_base: str, key: str) -> dict:
    if not FIXTURE.is_file():
        raise FileNotFoundError(f"fixture missing: {FIXTURE}")

    boundary = "----SmartCRMPdfSmoke"
    pdf_bytes = FIXTURE.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{FIXTURE.name}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + pdf_bytes + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{api_base.rstrip('/')}/api/tenders/documents/extract",
        data=body,
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-API-Key": key,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    _load_env()
    api = os.environ.get("TENDERS_SMOKE_API_URL", DEFAULT_API).rstrip("/")
    key = _api_key()
    if not key:
        print("smoke_tender_pdf_extract: skip (SMARTCRM_API_KEY не задан в корневом .env)")
        return 0

    try:
        data = _post_extract(api, key)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        print(f"smoke_tender_pdf_extract: FAIL HTTP {e.code}: {detail}")
        return 1
    except OSError as e:
        print(f"smoke_tender_pdf_extract: skip API недоступен ({e})")
        return 0

    if not data.get("ok"):
        print(f"smoke_tender_pdf_extract: FAIL body={data}")
        return 1
    text = str(data.get("text") or "")
    if "SMARTCRM_TZ_MARKER" not in text:
        print(f"smoke_tender_pdf_extract: FAIL unexpected text={text!r}")
        return 1

    print(
        f"pdf extract OK: {data.get('filename')} · {data.get('chars')} симв. · "
        f"text={text[:40]!r}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
