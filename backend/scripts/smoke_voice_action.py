#!/usr/bin/env python3
"""Смоук voice_action: build + pipeline mock."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from voice.voice_action import build_voice_action


def main() -> int:
    cases = [
        ("delete_lead", {"company": "Test"}, "approve"),
        ("list_leads", {"filter": "hot"}, "filter"),
        ("create_lead", {"company": "A"}, "navigate"),
    ]
    for intent, slots, ui in cases:
        va = build_voice_action(intent=intent, slots=slots, reply="ok", agents=["analyst"])
        assert va and va["ui"] == ui, (intent, va)
        print(f"PASS {intent} -> ui={ui}")
    print("smoke_voice_action: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
