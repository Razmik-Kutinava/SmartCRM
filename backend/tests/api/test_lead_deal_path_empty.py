"""Путь сделки: не показывать «всё пройдено» при пустом dealPath (0/0).

GET /api/leads/{id} при пустом/отсутствующем dealPath должен возвращать
dealPath: null или [] (ключ не отсутствует), а не фейковый 0/0 «всё пройдено».
"""
import pytest


@pytest.mark.asyncio
async def test_lead_deal_path_empty_is_null_or_empty(client):
    """При пустых полях лида dealPath = null или [], не отсутствующий ключ."""
    create_r = await client.post("/api/leads", json={"company": "Пустой путь"})
    assert create_r.status_code == 201
    lead_id = create_r.json()["id"]

    get_r = await client.get(f"/api/leads/{lead_id}")
    assert get_r.status_code == 200
    data = get_r.json()

    assert "dealPath" in data, "dealPath не должен отсутствовать в ответе API"
    dp = data["dealPath"]

    # Путь не задан → null или пустой список (не groups с фейковым 0/0 «всё пройдено»)
    assert dp is None or dp == [] or (
        isinstance(dp, dict) and not dp.get("groups")
    ), f"dealPath при пустых полях должен быть null/[]/пуст, получено: {dp!r}"
