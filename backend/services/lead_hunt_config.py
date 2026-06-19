"""Конфиг автономного поиска лидов агентами (Ф3 Платформа)."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_BACKEND = Path(__file__).resolve().parents[1]
CONFIG_PATH = _BACKEND / "data" / "lead_hunt_config.json"
STATE_PATH = _BACKEND / "data" / "lead_hunt_state.json"


class LeadHuntConfig(BaseModel):
    hunt_enabled: bool = False
    hunt_interval_hours: int = Field(default=24, ge=1, le=168)
    candidates_per_run: int = Field(default=5, ge=1, le=20)
    min_score_threshold: int = Field(default=30, ge=0, le=100)
    won_sample_limit: int = Field(default=50, ge=1, le=200)
    autosave_above_threshold: bool = False
    notify_ops_queue: bool = True


def _env_bool(name: str) -> bool | None:
    raw = (os.getenv(name) or "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return None


def _apply_env(cfg: LeadHuntConfig) -> LeadHuntConfig:
    enabled = _env_bool("LEAD_HUNT_ENABLED")
    if enabled is not None:
        cfg.hunt_enabled = enabled
    iv = (os.getenv("LEAD_HUNT_INTERVAL_HOURS") or "").strip()
    if iv.isdigit():
        cfg.hunt_interval_hours = max(1, min(168, int(iv)))
    return cfg


def _default_config() -> LeadHuntConfig:
    return LeadHuntConfig()


def load_config() -> LeadHuntConfig:
    if not CONFIG_PATH.is_file():
        cfg = _apply_env(_default_config())
        save_config(cfg)
        return cfg
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cfg = LeadHuntConfig.model_validate(raw)
    except Exception as e:
        logger.warning("lead_hunt_config load: %s", e)
        cfg = _default_config()
    return _apply_env(cfg)


def save_config(cfg: LeadHuntConfig) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(cfg.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_state() -> dict[str, Any]:
    if not STATE_PATH.is_file():
        return {"runs": [], "scheduler": {}}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"runs": [], "scheduler": {}}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
