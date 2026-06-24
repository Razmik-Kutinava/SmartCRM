"""Зеркало фильтра менеджера в leadManager.js."""


def _matches(lead, filter_name):
    if not filter_name or filter_name == "all":
        return True
    key = " ".join(str(filter_name).lower().split())
    names = lead.get("managerNames") or []
    return any(" ".join(str(n).lower().split()) == key for n in names)


def test_manager_filter_by_manager_names():
    leads = [
        {"id": 1, "managerNames": ["Гюрджян Размик"]},
        {"id": 2, "managerNames": ["Иванов"]},
    ]
    out = [l for l in leads if _matches(l, "Гюрджян Размик")]
    assert [l["id"] for l in out] == [1]
