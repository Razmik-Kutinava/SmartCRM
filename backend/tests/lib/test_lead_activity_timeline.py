"""Зеркало merge задач в leadActivityTimeline.js."""


def _marker(note: str) -> str:
    import re

    m = re.match(r"^\[b24:(\w+):(\d+)\]", note or "")
    return f"{m.group(1)}:{m.group(2)}" if m else ""


def test_skip_act_task_when_in_comms():
    comms = [{"content": "[b24:act:10] встреча", "communicationType": "meeting"}]
    tasks = [{"id": 1, "title": "Встреча: x", "note": "[b24:act:10] x", "due": "01.01.2025"}]
    act_markers = {_marker(c["content"]) for c in comms}
    task_markers = [_marker(t.get("note", "")) for t in tasks]
    merged_tasks = [t for t, m in zip(tasks, task_markers) if not m or m not in act_markers]
    assert merged_tasks == []
