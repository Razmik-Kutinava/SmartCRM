"""Тесты WS voice_action событий."""
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.routes.voice import _voice_events


def test_voice_events_includes_voice_action():
    result = {
        "intent": "delete_lead",
        "reply": "Удаляю.",
        "agents": ["analyst"],
        "slots": {"company": "X"},
        "transcript": "удали X",
        "trace_id": "t1",
        "agent_result": {},
        "voice_action": {
            "type": "voice_action",
            "ui": "approve",
            "title": "Удалить?",
            "payload": {},
            "reply": "Удаляю.",
        },
    }
    events = _voice_events(result)
    assert len(events) == 2
    assert events[0]["type"] == "intent"
    assert events[1]["type"] == "voice_action"
    assert events[1]["ui"] == "approve"


def test_voice_events_without_voice_action():
    result = {
        "intent": "noop",
        "reply": "",
        "agents": [],
        "slots": {},
        "transcript": "хм",
        "trace_id": None,
        "agent_result": {},
        "voice_action": None,
    }
    events = _voice_events(result)
    assert len(events) == 1
    assert events[0]["type"] == "intent"
