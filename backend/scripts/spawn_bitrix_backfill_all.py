"""Запуск всех фоновых backfill из Битрикс (поля, таймлайн, дела, продукты)."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
PY = sys.executable


def _spawn(name: str, args: list[str]) -> None:
    cmd = [PY, "-u", str(BACKEND / "scripts" / args[0]), *args[1:]]
    print(f"spawn {name}: {' '.join(cmd)}", flush=True)
    subprocess.Popen(
        cmd,
        cwd=str(BACKEND),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Старт mass backfill Битрикс → CRM")
    parser.add_argument("--dry-run", action="store_true", help="Только показать команды")
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
                "80",
            ],
        ),
        (
            "timeline",
            [
                "resync_bitrix_lead_engagement.py",
                "--timeline-only",
                "--resume",
                "--workers",
                "2",
                "--batch-size",
                "30",
                "--delay-ms",
                "100",
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
                "100",
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
        (
            "watch_only_missing",
            [
                "watch_fields_resync_then_retry.py",
                "--poll-sec",
                "120",
            ],
        ),
    ]

    if args.dry_run:
        for name, argv in jobs:
            print(name, argv)
        return 0

    for name, argv in jobs:
        _spawn(name, argv)
    print("OK: 5 фоновых процессов запущены (поля, таймлайн, дела, продукты, watch)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
