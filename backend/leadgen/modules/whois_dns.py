"""DNS/WhoIs сигналы домена без API-ключа.

DNS: Cloudflare DNS-over-HTTPS (MX, TXT/SPF, A).
WhoIs: RDAP (дата регистрации / регистратор), best-effort.
"""
from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

_DOH_URL = "https://cloudflare-dns.com/dns-query"
_RDAP_BOOTSTRAP = "https://rdap.org/domain/{domain}"


def clean_domain(url_or_host: str) -> str:
    raw = (url_or_host or "").strip().lower()
    if not raw or raw in ("—", "-", "n/a"):
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    try:
        host = urlparse(raw).hostname or ""
    except Exception:
        host = ""
    host = host.removeprefix("www.")
    if not host or "." not in host or len(host) > 100:
        return ""
    return host


async def _doh_query(domain: str, rtype: str) -> list[dict[str, Any]]:
    """Cloudflare DoH → список Answer-записей."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                _DOH_URL,
                params={"name": domain, "type": rtype},
                headers={"Accept": "application/dns-json"},
            )
            if r.status_code != 200:
                return []
            data = r.json()
            answers = data.get("Answer") or []
            return [a for a in answers if isinstance(a, dict)]
    except Exception as e:
        logger.debug("DoH %s %s: %s", domain, rtype, e)
        return []


async def _rdap_domain(domain: str) -> dict[str, Any]:
    """RDAP: дата регистрации и регистратор (может не сработать для .ru)."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            r = await client.get(
                _RDAP_BOOTSTRAP.format(domain=domain),
                headers={"Accept": "application/rdap+json, application/json"},
            )
            if r.status_code != 200:
                return {}
            data = r.json()
            if not isinstance(data, dict):
                return {}
            registered_at = ""
            for ev in data.get("events") or []:
                if not isinstance(ev, dict):
                    continue
                if (ev.get("eventAction") or "").lower() in (
                    "registration",
                    "registered",
                ):
                    registered_at = str(ev.get("eventDate") or "")[:10]
                    break
            registrar = ""
            for ent in data.get("entities") or []:
                if not isinstance(ent, dict):
                    continue
                roles = [str(x).lower() for x in (ent.get("roles") or [])]
                if "registrar" in roles:
                    vcard = ent.get("vcardArray") or []
                    # vcardArray: ["vcard", [[ "fn", {}, "text", "Name"], ...]]
                    if isinstance(vcard, list) and len(vcard) >= 2:
                        for row in vcard[1] if isinstance(vcard[1], list) else []:
                            if isinstance(row, list) and row and row[0] == "fn":
                                registrar = str(row[-1] or "")
                                break
                    break
            out: dict[str, Any] = {}
            if registered_at:
                out["registered_at"] = registered_at
            if registrar:
                out["registrar"] = registrar
            return out
    except Exception as e:
        logger.debug("RDAP %s: %s", domain, e)
        return {}


def _txt_data(answers: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for a in answers:
        raw = str(a.get("data") or "").strip().strip('"')
        if raw:
            out.append(raw)
    return out


def _mx_data(answers: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for a in answers:
        raw = str(a.get("data") or "").strip()
        if raw:
            out.append(raw.rstrip("."))
    return out


async def fetch_dns_signals(website_or_domain: str) -> dict[str, Any]:
    """Сигналы домена: MX/SPF/DMARC/A + RDAP (если доступен)."""
    domain = clean_domain(website_or_domain)
    if not domain:
        return {"_skipped": True, "reason": "no_domain"}

    import asyncio

    mx_a, txt_a, a_a, rdap = await asyncio.gather(
        _doh_query(domain, "MX"),
        _doh_query(domain, "TXT"),
        _doh_query(domain, "A"),
        _rdap_domain(domain),
    )

    mx = _mx_data(mx_a)
    txts = _txt_data(txt_a)
    a_records = [str(x.get("data") or "") for x in a_a if x.get("data")]

    has_mx = bool(mx)
    has_spf = any(re.search(r"\bv=spf1\b", t, re.I) for t in txts)
    has_dmarc = False
    try:
        dmarc_ans = await _doh_query(f"_dmarc.{domain}", "TXT")
        has_dmarc = any("v=DMARC1" in t.upper() for t in _txt_data(dmarc_ans))
    except Exception:
        has_dmarc = False

    email_ready = has_mx  # MX достаточно для «почта живая?»
    registered_at = (rdap or {}).get("registered_at") or ""
    registrar = (rdap or {}).get("registrar") or ""

    bits = [domain]
    bits.append("MX+" if has_mx else "no-MX")
    bits.append("SPF" if has_spf else "no-SPF")
    if has_dmarc:
        bits.append("DMARC")
    if registered_at:
        bits.append(f"reg {registered_at}")
    summary = ": ".join([bits[0], ", ".join(bits[1:])])

    return {
        "domain": domain,
        "mx": mx[:8],
        "has_mx": has_mx,
        "has_spf": has_spf,
        "has_dmarc": has_dmarc,
        "a_records": a_records[:5],
        "email_ready": email_ready,
        "registered_at": registered_at or None,
        "registrar": registrar or None,
        "summary": summary,
    }
