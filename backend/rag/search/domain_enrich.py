"""Обогащение домена для 🔍: BuiltWith (стек) + WhoIs/DNS (MX/SPF)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _usable_tech(tech: Any) -> dict[str, Any]:
    if not isinstance(tech, dict) or not tech:
        return {}
    if tech.get("_skipped") or tech.get("_error"):
        return {}
    # Есть хоть один полезный сигнал
    if (
        tech.get("all_technologies")
        or tech.get("cms")
        or tech.get("by_category")
        or tech.get("maturity_level")
        or tech.get("domain")
    ):
        return tech
    return {}


def _usable_dns(dns: Any) -> dict[str, Any]:
    if not isinstance(dns, dict) or not dns:
        return {}
    if dns.get("_skipped"):
        return {}
    return dns


async def enrich_domain_signals(website: str = "", **_kw: Any) -> dict[str, Any]:
    """Параллельно BuiltWith + DNS/WhoIs по сайту лида.

    Возвращает:
      tech — стек BuiltWith (для tech_json / checko.tech)
      domain_signals — MX/SPF/возраст домена
      providers_used, raw_results
    """
    site = (website or "").strip()
    if not site or site in ("—", "-"):
        return {
            "tech": {},
            "domain_signals": {},
            "providers_used": [],
            "raw_results": [],
        }

    from leadgen.modules.builtwith import _clean_domain, fetch_tech_stack
    from leadgen.modules.whois_dns import fetch_dns_signals

    domain = _clean_domain(site)
    if not domain:
        return {
            "tech": {},
            "domain_signals": {},
            "providers_used": [],
            "raw_results": [],
        }

    tech_res, dns_res = await asyncio.gather(
        fetch_tech_stack(domain),
        fetch_dns_signals(domain),
        return_exceptions=True,
    )

    providers: list[str] = []
    raw: list[dict[str, Any]] = []
    tech: dict[str, Any] = {}
    dns: dict[str, Any] = {}

    if isinstance(tech_res, Exception):
        logger.warning("BuiltWith domain enrich: %s", tech_res)
    else:
        tech = _usable_tech(tech_res)
        if tech:
            providers.append("builtwith")
            cats = tech.get("all_technologies") or tech.get("cms") or []
            raw.append(
                {
                    "title": f"BuiltWith: {domain}",
                    "snippet": f"Стек: {', '.join(str(c) for c in cats[:12])}"
                    f"; maturity={tech.get('maturity_level') or '—'}",
                    "url": f"https://builtwith.com/{domain}",
                    "date": "",
                    "source": "builtwith",
                }
            )

    if isinstance(dns_res, Exception):
        logger.warning("WhoIs/DNS domain enrich: %s", dns_res)
    else:
        dns = _usable_dns(dns_res)
        if dns:
            providers.append("whois_dns")
            raw.append(
                {
                    "title": f"DNS/WhoIs: {domain}",
                    "snippet": dns.get("summary") or "",
                    "url": "",
                    "date": "",
                    "source": "whois_dns",
                }
            )

    return {
        "tech": tech,
        "domain_signals": dns,
        "providers_used": providers,
        "raw_results": raw,
    }


def tech_brief(tech: dict[str, Any] | None, *, max_chars: int = 500) -> str:
    """Короткая выжимка стека для слотов агента."""
    if not tech or not isinstance(tech, dict):
        return ""
    parts: list[str] = []
    domain = tech.get("domain")
    if domain:
        parts.append(f"домен {domain}")
    mat = tech.get("maturity_level")
    if mat:
        parts.append(f"зрелость {mat}")
    for key, label in (
        ("cms", "CMS"),
        ("crm", "CRM"),
        ("analytics", "analytics"),
        ("hosting", "hosting"),
        ("ecommerce", "ecom"),
    ):
        vals = tech.get(key) or []
        if vals:
            parts.append(f"{label}: {', '.join(str(v) for v in vals[:5])}")
    all_t = tech.get("all_technologies") or []
    if all_t and len(parts) < 3:
        parts.append("стек: " + ", ".join(str(v) for v in all_t[:10]))
    text = "; ".join(parts)
    return text[:max_chars]


def dns_brief(dns: dict[str, Any] | None, *, max_chars: int = 280) -> str:
    if not dns or not isinstance(dns, dict):
        return ""
    return str(dns.get("summary") or "")[:max_chars]
