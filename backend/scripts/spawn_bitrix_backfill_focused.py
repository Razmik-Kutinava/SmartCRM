"""Backfill B24 → CRM без таймлайна/watch: поля, импорт, задачи, продукты."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
PY = sys.executable
TIMELINE_STATE = BACKEND / "data" / "bitrix_timeline_resync_state.json"


def _spawn(name: str, args: list[str]) -> None:
    cmd = [PY, "-u", str(BACKEND / "scripts" / args[0]), *args[1:]]
    print(f"spawn {name}: {' '.join(cmd)}", flush=True)
    subprocess.Popen(
        cmd,
        cwd=str(BACKEND),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )


def _mark_timeline_done_if_complete() -> None:
    """Не перезапускать таймлайн, если прошлый прогон уже закрыт."""
    if not TIMELINE_STATE.is_file():
        return
    try:
        state = json.loads(TIMELINE_STATE.read_text(encoding="utf-8"))
    except Exception:
        return
    total = int(state.get("total_b24") or 0)
    processed = int(state.get("processed") or 0)
    if state.get("status") == "done" or (total > 0 and processed >= total):
        state["status"] = "done"
        state["processed"] = max(processed, total)
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        TIMELINE_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"timeline: skip (already done {state['processed']}/{total})", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Фокусный backfill B24 (без timeline/watch)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-import", action="store_true", help="Не запускать re-import лидов")
    args = parser.parse_args()

    jobs = [
        (
            "fields",
            [
                "resync_bitrix_lead_fields.py",
                "--only-missing",
                "--workers",
                "2",
                "--batch-size",
                "25",
                "--delay-ms",
                "60",
            ],
        ),
        (
            "tasks",
            [
                "resync_bitrix_lead_tasks.py",
                "--workers",
                "2",
                "--batch-size",
                "30",
                "--delay-ms",
                "80",
                "--require-task-scope",
            ],
        ),
        (
            "products",
            [
                "resync_bitrix_lead_products.py",
                "--workers",
                "1",
                "--batch-size",
                "40",
                "--delay-ms",
                "60",
            ],
        ),
    ]
    if not args.skip_import:
        jobs.append(
            (
                "import_profiles",
                ["resync_bitrix_lead_profiles.py", "--date-from", "2023-01-01"],
            ),
        )

    _mark_timeline_done_if_complete()

    if args.dry_run:
        for name, argv in jobs:
            print(name, argv)
        return 0

    for name, argv in jobs:
        _spawn(name, argv)
    print(
        f"OK: {len(jobs)} процессов (поля, задачи, продукты"
        + (", import" if not args.skip_import else "")
        + "). Таймлайн/watch не запускаются.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
