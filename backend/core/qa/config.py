"""Dr. QA — пути и константы."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "qa_lab.sqlite3"
SCRIPTS_DIR = ROOT / "scripts"

VALID_STATUSES = ("draft", "running", "canary", "accepted", "rejected", "killed")
VALID_METHODS = ("aa", "ab", "mvt", "bandit", "canary", "fake_door", "blue_green")
