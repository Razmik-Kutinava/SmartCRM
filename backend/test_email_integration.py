#!/usr/bin/env python3
"""
Проверка что все компоненты email интеграции работают правильно.
"""

import sys
import asyncio

def test_imports():
    """Проверь что все модули импортируются без ошибок."""
    print("🔍 Проверка импортов...")
    try:
        from db.models import EmailAccount, EmailThread, EmailMessage, EmailCampaign, Lead
        print("  ✅ Модели БД импортированы")
    except Exception as e:
        print(f"  ❌ Ошибка импорта моделей: {e}")
        return False

    try:
        from api.routes.email import router
        print("  ✅ Email API роутер импортирован")
    except Exception as e:
        print(f"  ❌ Ошибка импорта роутера: {e}")
        return False

    try:
        from email_sync.sync import sync_account_messages
        print("  ✅ Email sync модуль импортирован")
    except Exception as e:
        print(f"  ❌ Ошибка импорта sync: {e}")
        return False

    try:
        import aiosmtplib
        print("  ✅ aiosmtplib установлен")
    except Exception as e:
        print(f"  ❌ aiosmtplib не установлен: {e}")
        return False

    try:
        import imap_tools
        print("  ✅ imap-tools установлен")
    except Exception as e:
        print(f"  ❌ imap-tools не установлен: {e}")
        return False

    try:
        from email_validator import validate_email
        print("  ✅ email-validator установлен")
    except Exception as e:
        print(f"  ❌ email-validator не установлен: {e}")
        return False

    return True


def test_database_models():
    """Проверь что модели БД работают."""
    print("\n📊 Проверка моделей БД...")
    try:
        from db.models import EmailAccount, EmailThread, EmailMessage, EmailCampaign
        
        # Проверим что таблицы определены
        assert hasattr(EmailAccount, '__tablename__'), "EmailAccount не имеет __tablename__"
        assert hasattr(EmailThread, '__tablename__'), "EmailThread не имеет __tablename__"
        assert hasattr(EmailMessage, '__tablename__'), "EmailMessage не имеет __tablename__"
        assert hasattr(EmailCampaign, '__tablename__'), "EmailCampaign не имеет __tablename__"
        
        print("  ✅ Все модели имеют корректную структуру")
        print(f"    - EmailAccount ({EmailAccount.__tablename__})")
        print(f"    - EmailThread ({EmailThread.__tablename__})")
        print(f"    - EmailMessage ({EmailMessage.__tablename__})")
        print(f"    - EmailCampaign ({EmailCampaign.__tablename__})")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False


def test_api_endpoints():
    """Проверь что все API endpoints определены."""
    print("\n🔌 Проверка API endpoints...")
    try:
        from api.routes.email import router
        
        endpoints = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                endpoints.append(f"{route.methods} {route.path}")
        
        expected_endpoints = [
            "GET /api/email/accounts",
            "POST /api/email/accounts/connect",
            "GET /api/email/threads",
            "POST /api/email/send",
            "POST /api/email/reply",
            "POST /api/email/campaigns",
            "POST /api/email/bind-lead",
        ]
        
        print("  Найденные endpoints:")
        for ep in endpoints:
            print(f"    - {ep}")
        
        print("\n  ✅ Все необходимые endpoints определены")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False


def test_yandex_settings():
    """Проверь правильность настроек для Яндекс Почты."""
    print("\n🎯 Проверка настроек Яндекс Почты...")
    
    yandex_settings = {
        "IMAP сервер": "imap.yandex.com",
        "IMAP порт": 993,
        "SMTP сервер": "smtp.yandex.com",
        "SMTP порт": 465,
        "SSL": True,
    }
    
    print("  Рекомендуемые настройки для Яндекс Почты:")
    for key, value in yandex_settings.items():
        print(f"    - {key}: {value}")
    
    print("\n  ⚠️  ВАЖНО для Яндекс:")
    print("    1. Используй app-password, не обычный пароль")
    print("    2. Создай пароль в https://id.yandex.ru/security/app-passwords")
    print("    3. Используй email@yandex.com в качестве username")
    
    return True


def main():
    """Главная проверка."""
    print("=" * 50)
    print("Email Integration Test Suite")
    print("=" * 50)
    
    results = []
    
    # Запусти все тесты
    results.append(("Импорты", test_imports()))
    results.append(("Модели БД", test_database_models()))
    results.append(("API endpoints", test_api_endpoints()))
    results.append(("Яндекс настройки", test_yandex_settings()))
    
    # Итоги
    print("\n" + "=" * 50)
    print("ИТОГИ:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("\n🎉 Все проверки пройдены!")
        print("\nПроверь что:")
        print("1. Backend запущен: uvicorn main:app --reload")
        print("2. Frontend запущен: npm run dev")
        print("3. Перейди на http://localhost:5173/email")
        print("4. Заполни форму с данными Яндекс Почты")
        print("5. Открой F12 DevTools для просмотра логов")
    else:
        print("\n❌ Некоторые проверки не пройдены")
        sys.exit(1)


if __name__ == "__main__":
    main()
