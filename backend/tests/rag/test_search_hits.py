"""Тесты нормализации hits → ingest-batch."""

from rag.search_hits import enrich_data_to_docs, web_hit_to_doc, web_hits_to_docs


def test_web_hit_to_doc_with_url():
    doc = web_hit_to_doc({"title": "T", "snippet": "S" * 20, "url": "https://x.ru"})
    assert "Источник: https://x.ru" in doc["text"]
    assert doc["metadata"]["source"] == "https://x.ru"


def test_web_hits_to_docs_count():
    assert len(web_hits_to_docs([{"title": "A", "snippet": "x" * 15}, {"title": "B", "snippet": "y" * 15}])) == 2


def test_enrich_data_to_docs():
    docs = enrich_data_to_docs({"phone": "+7 495", "site": "acme.ru"}, "АКМЕ")
    assert len(docs) == 1
    assert "АКМЕ" in docs[0]["text"]
    assert "phone:" in docs[0]["text"]
