"""Ждёт status=done в state, затем --only-missing дожим (workers=1)."""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
STATE_PATH = BACKEND / "data" / "bitrix_fields_resync_state.json"
RESYNC = BACKEND / "scripts" / "resync_bitrix_lead_fields.py"


def _read_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--poll-sec", type=int, default=120, help="Интервал опроса state")
    parser.add_argument("--delay-ms", type=int, default=150)
    args = parser.parse_args()

    print("watch_fields_resync: ждём основной прогон…", flush=True)
    while True:
        st = _read_state()
        status = st.get("status")
        processed = int(st.get("processed") or 0)
        total = int(st.get("total_b24") or 0)
        if status == "done" or (total > 0 and processed >= total):
            print(f"watch_fields_resync: основной прогон завершён ({processed}/{total})", flush=True)
            break
        if status == "failed":
            print(f"watch_fields_resync: основной прогон failed: {st.get('error')}", flush=True)
            return 1
        print(
            f"  … {processed}/{total} errors={st.get('errors', 0)} eta={st.get('eta_sec')}s",
            flush=True,
        )
        time.sleep(max(30, args.poll_sec))

    proc = subprocess.run(
        [
            sys.executable,
            "-u",
            str(RESYNC),
            "--only-missing",
            "--workers",
            "1",
            "--delay-ms",
            str(args.delay_ms),
        ],
        cwd=str(BACKEND),
        check=False,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
