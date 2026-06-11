"""Проверка, что CI smoke paths существуют."""
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def test_ci_smoke_paths_exist():
    from scripts.ci_smoke import PYTEST_PATHS, SCRIPT_CHECKS

    for rel in [*PYTEST_PATHS, *SCRIPT_CHECKS]:
        assert (BACKEND / rel).is_file(), rel


def test_requirements_includes_cryptography():
    text = (BACKEND / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "cryptography" in text
