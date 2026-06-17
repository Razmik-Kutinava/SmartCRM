"""Конфиг краулинга сайтов вендоров → RAG tech_specialist."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_BACKEND = Path(__file__).resolve().parents[1]
CONFIG_PATH = _BACKEND / "data" / "vendor_crawl_config.json"
STATE_PATH = _BACKEND / "data" / "vendor_crawl_state.json"


class VendorCrawlEntry(BaseModel):
    id: str
    name: str
    seed_url: str
    doc_urls: list[str] = Field(default_factory=list)
    enabled: bool = True
    use_sitemap: bool = False
    max_pages: int = Field(default=30, ge=1, le=200)
    max_depth: int = Field(default=2, ge=0, le=4)


class VendorCrawlConfig(BaseModel):
    vendors: list[VendorCrawlEntry] = Field(default_factory=list)
    auto_crawl_enabled: bool = False
    auto_crawl_interval_hours: int = Field(default=168, ge=1, le=720)


def _default_config() -> VendorCrawlConfig:
    return VendorCrawlConfig(
        vendors=[
            VendorCrawlEntry(
                id="demo_vendor",
                name="Demo (выключен)",
                seed_url="https://example.com/docs",
                enabled=False,
                max_pages=3,
                max_depth=1,
            ),
        ]
    )


def load_config() -> VendorCrawlConfig:
    if not CONFIG_PATH.is_file():
        cfg = _default_config()
        save_config(cfg)
        return cfg
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return VendorCrawlConfig.model_validate(raw)
    except Exception as e:
        logger.warning("vendor_crawl_config load: %s", e)
        return _default_config()


def save_config(cfg: VendorCrawlConfig) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(cfg.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_state() -> dict[str, Any]:
    if not STATE_PATH.is_file():
        return {"runs": []}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"runs": []}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
