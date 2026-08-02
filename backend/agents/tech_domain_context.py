"""Сайт/домен и BuiltWith+WhoIs для техспеца (не парсит сам HTML — API research)."""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_FREE_MAIL = frozenset({
    "gmail.com", "googlemail.com", "mail.ru", "bk.ru", "inbox.ru", "list.ru",
    "yandex.ru", "ya.ru", "yandex.com", "outlook.com", "hotmail.com",
    "live.com", "icloud.com", "me.com", "proton.me", "protonmail.com",
    "yahoo.com", "aol.com", "example.com",
})


def domain_from_email(email: str = "") -> str:
    """Домен после @; пусто для free-mail / мусора."""
    raw = (email or "").strip().lower()
    if "@" not in raw:
        return ""
    dom = raw.rsplit("@", 1)[-1].strip().strip(".")
    if not dom or "." not in dom or dom in _FREE_MAIL:
        return ""
    if any(c for c in dom if not (c.isalnum() or c in ".-")):
        return ""
    return dom


def _clean_host(value: str = "") -> str:
    text = (value or "").strip()
    if not text or text in ("—", "-", "n/a"):
        return ""
    try:
        from leadgen.modules.builtwith import _clean_domain

        return _clean_domain(text) or ""
    except Exception:
        text = re.sub(r"^https?://", "", text, flags=re.I)
        text = text.split("/")[0].split("?")[0].strip().lower()
        if text.startswith("www."):
            text = text[4:]
        return text if "." in text else ""


def resolve_site_and_domain(slots: dict[str, Any]) -> dict[str, Any]:
    """Сайт и домен из карточки; домен также из email после @."""
    website = str(slots.get("website") or "").strip()
    if website in ("—", "-"):
        website = ""
    email = str(slots.get("email") or "").strip()
    email_dom = domain_from_email(email)
    host_from_site = _clean_host(website)
    domain = host_from_site or email_dom
    sources: list[str] = []
    if website or host_from_site:
        sources.append("website")
    if email_dom:
        sources.append("email")
    if not website and email_dom:
        website = email_dom
    return {
        "website": website,
        "domain": domain,
        "email_domain": email_dom,
        "sources": sources,
    }


def tech_has_signals(tech: Any) -> bool:
    if not isinstance(tech, dict) or not tech:
        return False
    if tech.get("_skipped") or tech.get("_error"):
        return False
    return bool(
        tech.get("all_technologies")
        or tech.get("cms")
        or tech.get("by_category")
        or tech.get("maturity_level")
        or tech.get("crm")
    )


def dns_has_signals(dns: Any) -> bool:
    if not isinstance(dns, dict) or not dns:
        return False
    if dns.get("_skipped"):
        return False
    return bool(dns.get("summary") or dns.get("has_mx") or dns.get("mx") or dns.get("spf"))


def _dns_from_slots(slots: dict[str, Any]) -> dict[str, Any]:
    tech = slots.get("tech") if isinstance(slots.get("tech"), dict) else {}
    dns = tech.get("domain_signals") if isinstance(tech.get("domain_signals"), dict) else {}
    if dns_has_signals(dns):
        return dns
    checko = slots.get("checko") if isinstance(slots.get("checko"), dict) else {}
    analyses = checko.get("analyses") if isinstance(checko.get("analyses"), dict) else {}
    wr = analyses.get("web_research") if isinstance(analyses.get("web_research"), dict) else {}
    dns2 = wr.get("domain_signals") if isinstance(wr.get("domain_signals"), dict) else {}
    return dns2 if isinstance(dns2, dict) else {}


async def ensure_domain_enrich(slots: dict[str, Any]) -> dict[str, Any]:
    """Если сайт/домен есть, а стек/DNS пусты — дергает BuiltWith+WhoIs (как 🔍)."""
    out = dict(slots or {})
    resolved = resolve_site_and_domain(out)
    domain = resolved["domain"]
    website = resolved["website"] or domain
    out["observed_website"] = resolved["website"]
    out["observed_domain"] = domain
    out["domain_sources"] = resolved["sources"]

    tech = out.get("tech") if isinstance(out.get("tech"), dict) else {}
    dns = _dns_from_slots(out)
    need_tech = bool(domain) and not tech_has_signals(tech)
    need_dns = bool(domain) and not dns_has_signals(dns)

    if domain and (need_tech or need_dns):
        try:
            from rag.search.domain_enrich import enrich_domain_signals, tech_brief, dns_brief

            pack = await enrich_domain_signals(website or domain)
            new_tech = pack.get("tech") if isinstance(pack.get("tech"), dict) else {}
            new_dns = (
                pack.get("domain_signals")
                if isinstance(pack.get("domain_signals"), dict)
                else {}
            )
            if tech_has_signals(new_tech):
                merged = dict(tech)
                merged.update(new_tech)
                if dns_has_signals(new_dns):
                    merged["domain_signals"] = new_dns
                out["tech"] = merged
                tech = merged
                dns = new_dns or dns
            elif dns_has_signals(new_dns):
                merged = dict(tech) if tech else {}
                merged["domain_signals"] = new_dns
                out["tech"] = merged
                dns = new_dns
            brief = tech_brief(tech) if tech_has_signals(tech) else ""
            dbrief = dns_brief(dns) if dns_has_signals(dns) else ""
            parts = [p for p in (brief, dbrief) if p]
            if parts:
                out["tech_stack_brief"] = " | ".join(parts)[:600]
            out["_domain_enrich_providers"] = list(pack.get("providers_used") or [])
        except Exception as e:
            logger.warning("tech ensure_domain_enrich: %s", e)

    if not out.get("tech_stack_brief"):
        from rag.search.domain_enrich import tech_brief, dns_brief

        tech = out.get("tech") if isinstance(out.get("tech"), dict) else {}
        dns = _dns_from_slots(out)
        parts = [p for p in (tech_brief(tech), dns_brief(dns)) if p]
        out["tech_stack_brief"] = " | ".join(parts)[:600]

    out["_dns_signals"] = _dns_from_slots(out)
    return out


def build_tech_context_lines(slots: dict[str, Any]) -> list[str]:
    """Явные строки для user-промпта техспеца (сайт/домен/стек/DNS)."""
    lines: list[str] = []
    website = str(slots.get("observed_website") or slots.get("website") or "").strip()
    domain = str(slots.get("observed_domain") or "").strip()
    sources = slots.get("domain_sources") or []
    email = str(slots.get("email") or "").strip()
    email_dom = domain_from_email(email)

    if website:
        lines.append(f"Сайт (указан): {website}")
    else:
        lines.append("Сайт: не указан")
    if domain:
        src = ", ".join(sources) if sources else "карточка"
        lines.append(f"Домен для парсинга технологий: {domain} (источник: {src})")
    else:
        lines.append("Домен: не определён")
    if email:
        if email_dom:
            lines.append(f"Email: {email} → домен после @: {email_dom} (можно брать для BuiltWith/WhoIs)")
        else:
            lines.append(f"Email: {email} (free-mail / домен для стека не берём)")

    brief = str(slots.get("tech_stack_brief") or "").strip()
    if brief:
        lines.append(f"ТЕХНОЛОГИИ / DNS (BuiltWith+WhoIs): {brief}")
    else:
        lines.append(
            "ТЕХНОЛОГИИ / DNS: нет данных — если домен есть, стек нужно оценить по отрасли "
            "и указать в missing_data необходимость 🔍 / ключа BuiltWith"
        )

    providers = slots.get("_domain_enrich_providers") or []
    if providers:
        lines.append(f"Провайдеры обогащения в этом запуске: {', '.join(providers)}")

    return lines


def attach_observed_to_output(data: dict[str, Any], slots: dict[str, Any]) -> dict[str, Any]:
    """Гарантирует website/domain в конце отчёта агента."""
    out = dict(data or {})
    website = str(slots.get("observed_website") or slots.get("website") or "").strip()
    domain = str(slots.get("observed_domain") or "").strip()
    sources = list(slots.get("domain_sources") or [])
    brief = str(slots.get("tech_stack_brief") or "").strip()
    if website:
        out["observed_website"] = website
    if domain:
        out["observed_domain"] = domain
    if sources:
        out["domain_sources"] = sources
    if brief:
        out["stack_evidence"] = brief[:500]
    dns = slots.get("_dns_signals") if isinstance(slots.get("_dns_signals"), dict) else {}
    if dns.get("summary"):
        out["dns_evidence"] = str(dns["summary"])[:280]
    return out
