"""
Тесты для критических фиксов из CODE_REVIEW.md (апрель 2026).
Каждый тест соответствует пункту в таблице "Исправлено".
"""
import os
import sys
import importlib

import pytest


# ── #2 core/auth.py: timing-safe сравнение и dev/prod режимы ──────────


@pytest.mark.asyncio
async def test_auth_dev_mode_passes_without_key(monkeypatch):
    monkeypatch.delenv("SMARTCRM_API_KEY", raising=False)
    monkeypatch.delenv("SMARTCRM_REQUIRE_AUTH", raising=False)
    sys.modules.pop("core.auth", None)
    auth = importlib.import_module("core.auth")
    # В dev mode dependency возвращает None и не падает.
    assert await auth.require_api_key(x_api_key=None) is None


@pytest.mark.asyncio
async def test_auth_rejects_wrong_key(monkeypatch):
    monkeypatch.setenv("SMARTCRM_API_KEY", "secret-token")
    sys.modules.pop("core.auth", None)
    auth = importlib.import_module("core.auth")
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await auth.require_api_key(x_api_key="wrong")
    assert exc.value.status_code == 401
    # И принимает правильный
    assert await auth.require_api_key(x_api_key="secret-token") is None


def test_auth_fail_fast_when_required(monkeypatch):
    monkeypatch.delenv("SMARTCRM_API_KEY", raising=False)
    monkeypatch.setenv("SMARTCRM_REQUIRE_AUTH", "1")
    sys.modules.pop("core.auth", None)
    with pytest.raises(RuntimeError, match="SMARTCRM_API_KEY"):
        importlib.import_module("core.auth")


# ── #3/#4 core/crypto.py: Fernet, не глотать чужие исключения ─────────


def test_crypto_decrypt_returns_legacy_plaintext(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "")
    sys.modules.pop("core.crypto", None)
    crypto = importlib.import_module("core.crypto")
    # Legacy plaintext возвращается как есть, но не шифротекст с MemoryError.
    assert crypto.decrypt("plaintext-pass") == "plaintext-pass"
    assert crypto.decrypt(None) is None
    # roundtrip
    enc = crypto.encrypt("hello")
    assert enc != "hello"
    assert crypto.decrypt(enc) == "hello"


def test_crypto_invalid_secret_key_raises(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "not-a-fernet-key")
    sys.modules.pop("core.crypto", None)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        importlib.import_module("core.crypto")


# ── #5/#7 core/llm.py: lazy client, content=None, health не жжёт токены ─


def test_llm_lazy_client_picks_up_env(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "")
    sys.modules.pop("core.llm", None)
    llm = importlib.import_module("core.llm")
    # Без ключа — клиент None.
    assert llm._get_groq_client() is None
    # Меняем env и фабрика подхватывает.
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    llm._groq_client = None  # сброс
    client = llm._get_groq_client()
    assert client is not None


@pytest.mark.asyncio
async def test_llm_health_check_no_token_burn(monkeypatch):
    """health_check не должен делать платный chat-вызов на Groq."""
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    sys.modules.pop("core.llm", None)
    llm = importlib.import_module("core.llm")

    # Подкидываем фейковый клиент, который упадёт если его дёрнут.
    class _Boom:
        class chat:
            class completions:
                @staticmethod
                async def create(**_):
                    raise AssertionError("health_check не должен звонить в Groq API")

    llm._groq_client = _Boom()
    # Ollama тоже недоступна → status вернётся, ошибки не будет.
    res = await llm.health_check()
    assert "groq" in res and "ollama" in res and "active" in res


# ── #28/#29 voice.py: невалидный JSON и сокрытие str(e) ────────────────


def test_voice_handles_bad_json_in_text_message():
    """Структурный тест: код пытается распарсить JSON в try/except."""
    src = open(
        os.path.join(os.path.dirname(__file__), "..", "api", "routes", "voice.py"),
        encoding="utf-8",
    ).read()
    assert "_json.loads(message[\"text\"])" in src
    assert "except (ValueError, TypeError)" in src
    # И не утекаем str(e) в WS
    assert 'message": str(e)' not in src


# ── #15 main.py: CORS из env ───────────────────────────────────────────


def test_main_cors_reads_env():
    src = open(
        os.path.join(os.path.dirname(__file__), "..", "main.py"),
        encoding="utf-8",
    ).read()
    assert "SMARTCRM_CORS_ORIGINS" in src


# ── #31 tenders.py: невалидная дата → 400 ───────────────────────────────


def test_tenders_invalid_date_is_caught():
    src = open(
        os.path.join(os.path.dirname(__file__), "..", "api", "routes", "tenders", "search_routes.py"),
        encoding="utf-8",
    ).read()
    assert "Невалидная дата" in src


# ── #10/#11 ops.py: AsyncGroq клиент закрывается ───────────────────────


def test_ops_closes_groq_client():
    ops_dir = os.path.join(os.path.dirname(__file__), "..", "api", "routes", "ops")
    src = ""
    for name in os.listdir(ops_dir):
        if name.endswith(".py"):
            with open(os.path.join(ops_dir, name), encoding="utf-8") as f:
                src += f.read()
    assert src.count("await client.close()") >= 2
    assert "максимум 200 фраз" in src


# ── #45/#8 email.py: validate_certs и SMTP-traceback не утекает ────────


def test_email_smtp_validate_certs_and_sanitized():
    src = open(
        os.path.join(os.path.dirname(__file__), "..", "api", "routes", "email.py"),
        encoding="utf-8",
    ).read()
    assert "validate_certs=True" in src
    assert "from None" in src  # raise … from None — обрезаем причину


# ── #12 tenders.py: при отмене — таски отменяются ──────────────────────


def test_tenders_cancels_scheduled_on_abort():
    src = open(
        os.path.join(os.path.dirname(__file__), "..", "api", "routes", "tenders", "search_routes.py"),
        encoding="utf-8",
    ).read()
    assert "_t.cancel()" in src
