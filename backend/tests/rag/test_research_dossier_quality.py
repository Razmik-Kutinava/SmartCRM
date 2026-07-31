"""Тест: мусорный ответ LLM не считается досье."""
from rag.search.research_dossier import is_error_summary, is_usable_dossier


def test_refusal_is_error_summary():
    assert is_error_summary(
        "Извините, но я не могу перевести текст в русский язык. Предоставьте текст."
    )


def test_usable_dossier_requires_sections():
    assert not is_usable_dossier("Короткая фраза без структуры")
    good = (
        "## 1. Профиль компании\nСыры.\n\n"
        "## 2. Продукты и услуги\nЛинейки.\n\n"
        "## 9. Источники\n[1] https://x"
    )
    assert is_usable_dossier(good)
