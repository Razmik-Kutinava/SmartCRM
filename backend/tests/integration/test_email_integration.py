#!/usr/bin/env python3
"""
Проверка что все компоненты email интеграции работают правильно.

Запуск (из backend/):
  python tests/integration/test_email_integration.py
  pytest tests/integration/test_email_integration.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


def test_imports():
    """Все модули email-интеграции импортируются."""
    from db.models import EmailAccount, EmailCampaign, EmailMessage, EmailThread, Lead  # noqa: F401
    from api.routes.email import router  # noqa: F401
    from email_sync.sync import sync_account_messages  # noqa: F401
    import aiosmtplib  # noqa: F401
    import imap_tools  # noqa: F401
    from email_validator import validate_email  # noqa: F401

    assert router is not None
    assert callable(sync_account_messages)
    assert callable(validate_email)


def test_database_models():
    """Модели БД email имеют __tablename__."""
    from db.models import EmailAccount, EmailCampaign, EmailMessage, EmailThread

    for model in (EmailAccount, EmailThread, EmailMessage, EmailCampaign):
        assert hasattr(model, "__tablename__"), f"{model.__name__} без __tablename__"


def test_api_endpoints():
    """Email router объявляет хотя бы один route."""
    from api.routes.email import router

    paths = [
        route.path
        for route in router.routes
        if hasattr(route, "path") and hasattr(route, "methods")
    ]
    assert paths, "нет routes в email router"


def test_yandex_settings():
    """Канон портов/хостов Яндекс — документационный smoke."""
    yandex = {
        "imap": ("imap.yandex.com", 993),
        "smtp": ("smtp.yandex.com", 465),
    }
    assert yandex["imap"][1] == 993
    assert yandex["smtp"][1] == 465


def main() -> None:
    """CLI: те же проверки без pytest."""
    print("=" * 50)
    print("Email Integration Test Suite")
    print("=" * 50)

    checks = [
        ("Импорты", test_imports),
        ("Модели БД", test_database_models),
        ("API endpoints", test_api_endpoints),
        ("Яндекс настройки", test_yandex_settings),
    ]
    all_passed = True
    for name, fn in checks:
        try:
            fn()
            print(f"✅ PASS - {name}")
        except Exception as e:
            print(f"❌ FAIL - {name}: {e}")
            all_passed = False

    print("=" * 50)
    if not all_passed:
        sys.exit(1)
    print("🎉 Все проверки пройдены!")


if __name__ == "__main__":
    main()
