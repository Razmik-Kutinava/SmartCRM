"""core/bitrix_error_detail.py — detail для ответа, когда Битрикс недоступен."""
from __future__ import annotations

from core.bitrix_error_detail import bitrix_unavailable_detail

_REAL_MYSQL_DOWN = (
    "Битрикс24 crm.lead.list: ответ не JSON (HTTP 500): <pre>"
    "[Bitrix\\Main\\DB\\ConnectionException]  Mysql connect error [localhost]: "
    "(2002) Connection refused (400) /home/bitrix/www/bitrix/modules/main/lib/db/"
    "mysqliconnection.php:86 #0: Bitrix\\Main\\DB\\MysqliConnection->connectInternal() "
    "\t/home/bitrix/www/bitrix/modules/main/lib/Data/Connection.php:53"
)


def test_mysql_down_gives_plain_reason():
    detail = bitrix_unavailable_detail(_REAL_MYSQL_DOWN)
    assert "База данных Битрикс24 не отвечает" in detail
    assert "/home/bitrix/" not in detail
    assert "#0:" not in detail


def test_scope_error_names_the_cause():
    detail = bitrix_unavailable_detail("tasks.task.list 401 insufficient_scope")
    assert "прав" in detail


def test_unknown_error_is_trimmed_and_stripped():
    long_html = "<pre>" + "деталь " * 80 + "C:\\inetpub\\wwwroot\\x.php</pre>"
    detail = bitrix_unavailable_detail(long_html)
    assert "<pre>" not in detail
    assert "C:\\inetpub" not in detail
    assert len(detail) < 260


def test_empty_error_still_explains():
    assert bitrix_unavailable_detail("").strip()
    assert "логах" in bitrix_unavailable_detail("")
