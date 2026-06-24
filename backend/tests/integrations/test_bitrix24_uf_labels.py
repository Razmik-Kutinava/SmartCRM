"""bitrix24_uf_labels — индекс подписей UF полей."""
from integrations.bitrix24_uf_labels import BitrixUfLabelIndex


def test_label_index_matches_numeric_uf_by_russian_label():
    index = BitrixUfLabelIndex(
        [
            {
                "FIELD_NAME": "UF_CRM_1684590906",
                "EDIT_FORM_LABEL": {"ru": "Подписка до"},
            },
            {
                "FIELD_NAME": "UF_CRM_1684590938",
                "EDIT_FORM_LABEL": {"ru": "Тип поставки"},
            },
        ]
    )
    row = {
        "UF_CRM_1684590906": "10.01.2025",
        "UF_CRM_1684590938": "Продление поддержки",
    }
    assert index.by_hint(row, "подписк") == "10.01.2025"
    assert index.by_hint(row, "поставк") == "Продление поддержки"
