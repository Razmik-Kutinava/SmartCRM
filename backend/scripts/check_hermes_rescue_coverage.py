#!/usr/bin/env python3
"""Покрытие eval/cases.jsonl правилами rescue."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent

_REPO = Path(__file__).resolve().parents[2]
CASES = _REPO / "eval" / "cases.jsonl"


def main() -> int:
    cases = [json.loads(l) for l in CASES.read_text(encoding="utf-8").splitlines() if l.strip()]
    ok = fail = 0
    fails: list[tuple[str, str | None, str]] = []
    for c in cases:
        raw = rescue_route(c["text"])
        if raw:
            got = normalize_parsed_intent(c["text"], raw)["intent"]
            if got == c["expected_intent"]:
                ok += 1
            else:
                fail += 1
                fails.append((c["id"], got, c["expected_intent"]))
        else:
            fail += 1
            fails.append((c["id"], None, c["expected_intent"]))
    print(f"rescue ok={ok} fail={fail} total={len(cases)}")
    for item in fails:
        print(item)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
