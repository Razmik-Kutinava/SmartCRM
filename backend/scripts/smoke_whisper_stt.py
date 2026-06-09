#!/usr/bin/env python3
"""Смоук PRD_MAP «Whisper (Groq STT) → текст»."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = BACKEND_ROOT.parent


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND_ROOT / ".env")
        load_dotenv(_REPO_ROOT / ".env", override=True)
    except ImportError:
        pass


PYTEST_PATHS = [
    "tests/voice/test_whisper_stt.py",
    "tests/smoke/test_whisper_stt_smoke.py",
]


def main() -> int:
    _load_env()
    print("SmartCRM smoke — Whisper STT\n")
    cmd = [sys.executable, "-m", "pytest", *PYTEST_PATHS, "-q", "--tb=short"]
    proc = subprocess.run(cmd, cwd=BACKEND_ROOT)
    if proc.returncode != 0:
        print("\nWhisper STT smoke: FAIL")
        return 1

    key = os.getenv("GROQ_API_KEY", "")
    if key and key != "test" and len(key) >= 20:
        live = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/voice/test_whisper_stt.py::test_live_groq_transcribe_silent_wav", "-q"],
            cwd=BACKEND_ROOT,
        )
        if live.returncode != 0:
            print("\nWhisper STT live Groq: FAIL (проверь GROQ_API_KEY / сеть)")
            return 1
        print("Whisper STT live Groq: OK")
    else:
        print("Whisper STT live Groq: SKIP (нет GROQ_API_KEY в окружении)")

    print("\nWhisper STT smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
