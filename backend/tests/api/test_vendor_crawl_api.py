"""API /api/rag/vendor-crawl."""
from __future__ import annotations

import pytest


@pytest.fixture
def isolated_chroma(monkeypatch, tmp_path):
    import rag.chroma_store as chroma_store

    chroma_store._client = None
    d = tmp_path / "chroma_vc"
    d.mkdir()
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(d))
    yield d
    chroma_store._client = None


@pytest.fixture
def isolated_vendor_config(monkeypatch, tmp_path):
    import rag.vendor_crawl_config as vcfg

    monkeypatch.setattr(vcfg, "CONFIG_PATH", tmp_path / "vendor_crawl_config.json")
    monkeypatch.setattr(vcfg, "STATE_PATH", tmp_path / "vendor_crawl_state.json")
    vcfg.save_config(vcfg._default_config())


@pytest.mark.asyncio
async def test_vendor_crawl_config_get(client, isolated_vendor_config):
    r = await client.get("/api/rag/vendor-crawl/config")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert len(data["config"]["vendors"]) >= 1


@pytest.mark.asyncio
async def test_vendor_crawl_config_put_schedule(client, isolated_vendor_config):
    body = {
        "vendors": [
            {
                "id": "pt",
                "name": "PT",
                "seed_url": "https://example.com",
                "enabled": True,
                "max_pages": 5,
                "max_depth": 1,
            }
        ],
        "auto_crawl_enabled": True,
        "auto_crawl_interval_hours": 24,
    }
    r = await client.put("/api/rag/vendor-crawl/config", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["config"]["auto_crawl_enabled"] is True
    assert data["config"]["auto_crawl_interval_hours"] == 24


@pytest.mark.asyncio
async def test_vendor_crawl_status_includes_scheduler(client, isolated_vendor_config):
    r = await client.get("/api/rag/vendor-crawl/status")
    assert r.status_code == 200
    data = r.json()
    assert "auto_crawl_enabled" in data
    assert "scheduler" in data


@pytest.mark.asyncio
async def test_vendor_crawl_run_dry_run(client, isolated_chroma, isolated_vendor_config, monkeypatch):
    sample = "<html><body><p>" + (
        "Positive Technologies firewall documentation product overview service "
        "enterprise deployment architecture integration guide specifications "
    ) * 10 + "</p></body></html>"

    async def fake_fetch(_url: str):
        return sample, "https://example.com/docs"

    monkeypatch.setattr("rag.vendor_crawl._fetch_html", fake_fetch)

    async def empty_pdf_search(*_a, **_k):
        return []

    monkeypatch.setattr("rag.vendor_crawl.discover_pdf_urls_via_search", empty_pdf_search)

    r = await client.post(
        "/api/rag/vendor-crawl/run",
        json={"vendor_id": "demo_vendor", "dry_run": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["dry_run"] is True
    assert body["total_chunks"] >= 1
