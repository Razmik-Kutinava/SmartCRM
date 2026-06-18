"""Конфиг фонового мониторинга тендеров (Тех. спец)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_BACKEND = Path(__file__).resolve().parents[1]
CONFIG_PATH = _BACKEND / "data" / "tender_monitor_config.json"
STATE_PATH = _BACKEND / "data" / "tender_monitor_state.json"


class TenderWatchEntry(BaseModel):
    id: str
    name: str
    keywords: str = ""
    okpd_codes: list[str] = Field(default_factory=list)
    law: str = "all"
    region: str | None = None
    price_min: int | None = None
    price_max: int | None = None
    enabled: bool = True


class TenderMonitorConfig(BaseModel):
    watches: list[TenderWatchEntry] = Field(default_factory=list)
    monitor_enabled: bool = False
    monitor_interval_hours: int = Field(default=6, ge=1, le=168)
    notify_ops_queue: bool = True
    deadline_scan_interval_hours: int = Field(default=6, ge=1, le=168)
    search_min_relevance: int = Field(default=20, ge=0, le=99)


def _default_config() -> TenderMonitorConfig:
    return TenderMonitorConfig(
        watches=[
            TenderWatchEntry(
                id="demo_watch",
                name="Demo (выключен)",
                keywords="SIEM",
                enabled=False,
            ),
        ],
    )


def load_config() -> TenderMonitorConfig:
    if not CONFIG_PATH.is_file():
        cfg = _default_config()
        save_config(cfg)
        return cfg
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return TenderMonitorConfig.model_validate(raw)
    except Exception as e:
        logger.warning("tender_monitor_config load: %s", e)
        return _default_config()


def save_config(cfg: TenderMonitorConfig) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(cfg.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_state() -> dict[str, Any]:
    if not STATE_PATH.is_file():
        return {"seen": {}, "runs": []}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"seen": {}, "runs": []}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
