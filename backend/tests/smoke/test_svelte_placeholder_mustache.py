"""Регрессия: в Svelte-атрибутах нельзя писать {{company}} в обычных кавычках — парсится как переменная."""
from __future__ import annotations

import re
from pathlib import Path

_FRONTEND = Path(__file__).resolve().parents[3] / "frontend" / "src"
# placeholder="...{{var}}..." или placeholder='...{{var}}...' без обёртки {...}
_BAD = re.compile(
    r"""placeholder\s*=\s*["'][^"'{}]*\{\{[a-zA-Z_]""",
)


def test_no_unescaped_mustache_in_placeholder_attrs():
    bad = []
    for path in _FRONTEND.rglob("*.svelte"):
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if _BAD.search(line):
                bad.append(f"{path.relative_to(_FRONTEND.parent.parent)}:{i}")
    assert not bad, "Svelte парсит {{x}} в placeholder= как переменную x; оберни в {'…{{x}}…'}:\n" + "\n".join(bad)
