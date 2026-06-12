from core.agent_eval.acceptance_sync import acceptance_rows, build_gaps, patch_acceptance_md


def _fake_report():
    return {
        "generated_at": "2026-06-12T12:00:00+00:00",
        "overall_gate": "fail",
        "agents": {
            "hermes": {
                "summary": {
                    "passed": 25,
                    "failed": 11,
                    "total": 36,
                    "pass_rate_pct": 69.4,
                    "threshold_pct": 85,
                    "gate": "fail",
                    "min_cases": 30,
                },
                "results": [{"passed": False, "error": "ReadTimeout: x"}],
            },
            "analyst": {
                "summary": {
                    "passed": 12,
                    "failed": 3,
                    "total": 15,
                    "pass_rate_pct": 80.0,
                    "threshold_pct": 75,
                    "gate": "pass",
                    "min_cases": 15,
                },
                "results": [],
            },
        },
    }


def test_acceptance_rows():
    rows = acceptance_rows(_fake_report(), "gate.json")
    assert len(rows) == 2
    assert rows[0]["gate"] == "🔴"
    assert rows[1]["gate"] == "✅"


def test_build_gaps():
    gaps = build_gaps(_fake_report())
    assert any("Hermes" in g for g in gaps)
    assert any("MAP" in g for g in gaps)


def test_patch_acceptance_md(tmp_path):
    src = tmp_path / "acc.md"
    src.write_text(
        "before\n<!-- GATE_STATUS_START -->\nold\n<!-- GATE_STATUS_END -->\n"
        "<!-- GATE_GAPS_START -->\nold gaps\n<!-- GATE_GAPS_END -->\nafter\n",
        encoding="utf-8",
    )
    patch_acceptance_md(_fake_report(), "t.json", path=src)
    out = src.read_text(encoding="utf-8")
    assert "69.4%" in out
    assert "Hermes" in out
    assert "old\n" not in out or "old gaps" not in out
