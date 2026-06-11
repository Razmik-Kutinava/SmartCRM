"""Проверка, что CI smoke paths существуют."""
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def test_ci_smoke_paths_exist():
    from scripts.ci_smoke import PYTEST_PATHS, SCRIPT_CHECKS

    for rel in [*PYTEST_PATHS, *SCRIPT_CHECKS]:
        assert (BACKEND / rel).is_file(), rel
