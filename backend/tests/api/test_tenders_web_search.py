"""Юниты web_search для Serper/Tavily в тендерах."""
from api.routes.tenders.web_search import _map_web_hit


def test_map_web_hit_relevance():
    hit = {"title": "Закупка SIEM 44-ФЗ", "snippet": "госзакупка Москва", "url": "https://zakupki.gov.ru/x", "source": "serper"}
    item = _map_web_hit(hit, "SIEM", "44")
    assert item["web_hint"] is True
    assert item["relevance"] >= 35
    assert item["law"] == "44-ФЗ"
