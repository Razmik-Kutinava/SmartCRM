"""Фильтр URL и приоритеты для краулинга вендоров."""
from __future__ import annotations

import re
from urllib.parse import urlparse

_HREF_RE = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.I)
_JUNK_EXT = re.compile(
    r"\.(woff2?|ttf|eot|ico|svg|webp|mp4|webm|mp3|gz|tar|dmg)(\?|$)",
    re.I,
)
_JUNK_PATH = re.compile(
    r"/_next/static/|/static/media/|/assets/fonts/|/favicon",
    re.I,
)
_SKIP_EXT = re.compile(r"\.(jpg|jpeg|png|gif|zip|exe|css|js)(\?|$)", re.I)
_DOC_HINTS = (
    "documentation",
    "docs",
    "datasheet",
    "whitepaper",
    "products",
    "product",
    "solutions",
    "download",
    "manual",
    "guide",
    "spec",
    "brochure",
)


def normalize_url(url: str) -> str:
    return url.split("#")[0].rstrip("/")


def is_pdf_url(url: str) -> bool:
    low = url.lower()
    path = urlparse(low).path
    if path.endswith(".pdf") or ".pdf?" in low:
        return True
    if "/pdf/" in path or path.rstrip("/").endswith("/pdf"):
        return True
    return False


def is_junk_url(url: str) -> bool:
    if not url.startswith("http"):
        return True
    path = urlparse(url).path.lower()
    if _JUNK_EXT.search(path):
        return True
    if _JUNK_PATH.search(path):
        return True
    if _SKIP_EXT.search(path):
        return True
    return False


def link_priority(url: str) -> int:
    low = url.lower()
    score = 0
    if is_pdf_url(url):
        score += 120
    for hint in _DOC_HINTS:
        if hint in low:
            score += 18
    if "/doc" in low:
        score += 12
    return score


def seed_priority(url: str, *, from_doc_list: bool) -> int:
    base = link_priority(url)
    if from_doc_list:
        return base + 90
    return base + 60


def _same_netloc(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def extract_page_links(html: str, page_url: str) -> list[str]:
    """Ссылки с той же доменной зоны; мусор отфильтрован."""
    out: list[str] = []
    seen: set[str] = set()
    for href in _HREF_RE.findall(html):
        href = href.strip()
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue
        from urllib.parse import urljoin

        full = normalize_url(urljoin(page_url, href))
        if not full.startswith("http"):
            continue
        if not _same_netloc(full, page_url):
            continue
        if is_junk_url(full):
            continue
        if full in seen:
            continue
        seen.add(full)
        out.append(full)
    out.sort(key=link_priority, reverse=True)
    return out
