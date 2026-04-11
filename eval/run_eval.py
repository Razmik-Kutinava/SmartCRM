"""
Прогон eval-кейсов против Hermes (parse_intent).
Запуск из корня репозитория: python eval/run_eval.py
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path

# Корень репозитория → импорт backend
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

os.chdir(ROOT)
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

logging.basicConfig(level=logging.WARNING)

from core.hermes import parse_intent  # noqa: E402


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def _normalize_phone(s: str) -> str:
    d = _digits(s)
    if len(d) == 11 and d[0] == "8":
        d = "7" + d[1:]
    return d


def _normalize_slot_value(key: str, value: str) -> str:
    v = (value or "").strip().lower()
    if key in ("phone", "contact_phone"):
        return _normalize_phone(v)
    return v


def _slot_match(expected_key: str, gold: str, actual: str) -> float:
    """1.0 полное, 0.5 частичное, 0.0 нет."""
    g = _normalize_slot_value(expected_key, gold)
    a = _normalize_slot_value(expected_key, actual)
    if not g:
        return 1.0
    if not a:
        return 0.0
    # телефон в поле value / произвольном ключе
    dg, da = _digits(g), _digits(a)
    if len(dg) >= 10 and len(da) >= 10 and dg == da:
        return 1.0
    if g == a:
        return 1.0
    if g in a or a in g:
        return 0.5
    # одно слово совпало
    gw = set(g.split())
    aw = set(a.split())
    if gw and aw and (gw & aw):
        return 0.5
    return 0.0


def _score_case(expected_intent: str, expected_slots: dict, got: dict) -> tuple[float, dict]:
    gi = (got.get("intent") or "").strip()
    got_slots = got.get("slots") or {}
    if not isinstance(got_slots, dict):
        got_slots = {}

    intent_ok = 1.0 if gi == expected_intent else 0.0

    slot_scores: dict[str, float] = {}
    for k, gold_val in expected_slots.items():
        if gold_val is None or gold_val == "":
            continue
        av = got_slots.get(k)
        if av is None:
            slot_scores[k] = 0.0
            continue
        slot_scores[k] = _slot_match(k, str(gold_val), str(av))

    if not slot_scores:
        slot_avg = 1.0
    else:
        slot_avg = sum(slot_scores.values()) / len(slot_scores)

    # 40% интент + 60% слоты; при неверном интенте слоты всё же считаются с понижением
    if intent_ok:
        total = 0.4 * intent_ok + 0.6 * slot_avg
    else:
        total = 0.4 * 0.0 + 0.6 * slot_avg * 0.35

    return total, {"intent_ok": bool(intent_ok), "slot_scores": slot_scores, "slot_avg": slot_avg}


async def run_eval(cases_path: Path, verbose: bool) -> None:
    lines = [ln.strip() for ln in cases_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    results: list[tuple[str, float]] = []
    by_tag: dict[str, list[float]] = {}

    for raw in lines:
        row = json.loads(raw)
        cid = row["id"]
        text = row["text"]
        exp_intent = row["expected_intent"]
        exp_slots = row.get("expected_slots") or {}
        tags = row.get("tags") or []

        got = await parse_intent(text)
        total, detail = _score_case(exp_intent, exp_slots, got)
        results.append((cid, total))
        for t in tags:
            by_tag.setdefault(t, []).append(total)

        if verbose:
            print(f"\n=== {cid} ===")
            print("input:", text)
            print("expected:", exp_intent, exp_slots)
            print("got:", json.dumps(got, ensure_ascii=False, indent=2))
            print("score:", round(total, 3), detail)

    n = len(results)
    mean = sum(s for _, s in results) / n if n else 0.0
    print("\n" + "=" * 50)
    print(f"Кейсов: {n}")
    print(f"Средний балл: {mean:.3f} ({mean * 100:.1f}%)")
    print("=" * 50)
    for tag, vals in sorted(by_tag.items()):
        m = sum(vals) / len(vals)
        print(f"  по тегу [{tag}]: {m:.3f} (n={len(vals)})")


def main() -> None:
    ap = argparse.ArgumentParser(description="Прогон eval Hermes")
    ap.add_argument("--cases", type=Path, default=ROOT / "eval" / "cases.jsonl")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    asyncio.run(run_eval(args.cases, args.verbose))


if __name__ == "__main__":
    main()
