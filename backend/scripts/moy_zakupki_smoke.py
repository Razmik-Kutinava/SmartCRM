#!/usr/bin/env python3
"""Смок-тест Мои-Закупки: список ОКПД-2 (1 стр.) и поиск КТРУ по ключевому слову.

Запуск из каталога backend с загруженным MOY_ZAKUPKI_API_KEY:

    cd backend && python scripts/moy_zakupki_smoke.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# корень репо + backend/.env
_root = Path(__file__).resolve().parents[2]
_backend = Path(__file__).resolve().parents[1]
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv(_backend / ".env")
    load_dotenv(_root / ".env", override=True)


async def main() -> int:
    if not (os.getenv("MOY_ZAKUPKI_API_KEY") or "").strip():
        print("MOY_ZAKUPKI_API_KEY не задан — пропуск.")
        return 1

    sys.path.insert(0, str(_backend))

    from services.moy_zakupki import ktru_search, okpd2_list, search_hints_for_query

    print("1) okpd2_list per_page=2 …")
    ok = await okpd2_list(page=1, per_page=2, level=5)
    print("   count=", ok.get("count"), "results=", len(ok.get("results") or []))
    if ok.get("results"):
        r0 = ok["results"][0]
        print("   первая строка:", r0.get("code"), r0.get("name"))

    print("2) ktru_search characteristics=['ноутбук'] …")
    ks = await ktru_search({
        "characteristics": ["ноутбук"],
        "status": "Включено в КТРУ",
        "is_enlarged": False,
    })
    if isinstance(ks, dict):
        rs = ks.get("results") or []
    else:
        rs = ks if isinstance(ks, list) else []
    print("   позиций:", len(rs))
    for row in rs[:3]:
        if isinstance(row, dict):
            print("  ·", row.get("code"), row.get("name") or row.get("shortname"))

    print("3) search_hints_for_query('26.20.11') …")
    hints = await search_hints_for_query("справка по коду 26.20.11", 5)
    print("   сниппетов:", len(hints))
    for h in hints:
        print("  ·", h.get("title")[:80], "…")

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
