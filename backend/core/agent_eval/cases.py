"""Загрузка eval-кейсов Hermes и продуктовых агентов."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[3]
HERMES_CASES_PATH = _REPO / "eval" / "cases.jsonl"
AGENTS_DIR = _REPO / "eval" / "agents"

AGENT_IDS = ("analyst", "economist", "marketer", "strategist", "tech_specialist")

HERMES_MIN_CASES = 30
AGENT_MIN_CASES = 15

_REQUIRED_KEYS = frozenset({"id", "agent", "intent", "slots", "must_contain", "must_not_contain"})


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_hermes_cases() -> list[dict[str, Any]]:
    return _read_jsonl(HERMES_CASES_PATH)


def agent_cases_path(agent_id: str) -> Path:
    if agent_id not in AGENT_IDS:
        raise ValueError(f"unknown agent: {agent_id}")
    return AGENTS_DIR / f"{agent_id}.jsonl"


def load_agent_cases(agent_id: str) -> list[dict[str, Any]]:
    return _read_jsonl(agent_cases_path(agent_id))


def load_all_agent_cases() -> dict[str, list[dict[str, Any]]]:
    return {aid: load_agent_cases(aid) for aid in AGENT_IDS}


def validate_agent_case(case: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    missing = _REQUIRED_KEYS - set(case.keys())
    if missing:
        errs.append(f"missing keys: {sorted(missing)}")
    if case.get("agent") not in AGENT_IDS:
        errs.append(f"bad agent: {case.get('agent')}")
    if not isinstance(case.get("must_contain"), list) or not case["must_contain"]:
        errs.append("must_contain empty")
    if not isinstance(case.get("must_not_contain"), list):
        errs.append("must_not_contain not list")
    return errs
