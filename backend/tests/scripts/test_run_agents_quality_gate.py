"""CLI run_agents_quality_gate — log-file и gate logger без live Ollama."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[2]
_SCRIPT = _BACKEND / "scripts" / "run_agents_quality_gate.py"


def test_set_gate_logger_routes_to_callback():
    from core.agent_eval import gate as gate_module

    seen: list[str] = []
    gate_module.set_gate_logger(seen.append)
    gate_module._gate_logger("ping")
    assert seen == ["ping"]
    gate_module.set_gate_logger(gate_module._gate_log)


def test_cli_log_file_writes_lines(tmp_path, monkeypatch):
    log = tmp_path / "gate.log"
    fake_report = {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "ollama": {},
        "agents": {"analyst": {"summary": {"gate": "pass"}}},
        "overall_gate": "pass",
        "gaps": [],
    }

    async def fake_run(**_kwargs):
        from core.agent_eval import gate as gate_module

        gate_module._gate_logger("[gate] fake agent ...")
        return fake_report

    monkeypatch.setattr("core.agent_eval.gate.run_agents_quality_gate", fake_run)
    monkeypatch.setattr(
        "core.agent_eval.gate.save_gate_artifact",
        lambda report: tmp_path / "out.json",
    )

    from scripts import run_agents_quality_gate as cli

    cli._LOG_FH = open(log, "w", encoding="utf-8", buffering=1)
    try:
        code = __import__("asyncio").run(
            cli._main(
                cli.argparse.Namespace(
                    check_only=False,
                    hermes_limit=0,
                    agent_limit=1,
                    hermes_only=False,
                    agents_only=True,
                    write_acceptance=False,
                    log_file=str(log),
                )
            )
        )
    finally:
        cli._LOG_FH.close()
        cli._LOG_FH = None
    assert code == 0
    text = log.read_text(encoding="utf-8")
    assert "Quality gate:" in text
    assert "[gate] fake agent" in text
    assert "Overall gate: pass" in text


def test_check_only_subprocess():
    r = subprocess.run(
        [sys.executable, str(_SCRIPT), "--check-only"],
        cwd=str(_BACKEND),
        capture_output=True,
        text=True,
        timeout=30,
        env={**__import__("os").environ, "GROQ_API_KEY": ""},
    )
    if r.returncode == 2:
        pytest.skip("Ollama not available")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data.get("ok") is True
