"""Deep-merge checko_json / tech_json при PATCH — не затирать UF и паспорт."""
from __future__ import annotations

import json
from typing import Any


def _is_plain_dict(v: Any) -> bool:
    return isinstance(v, dict)


def deep_merge_objects(base: dict[str, Any] | None, overlay: dict[str, Any] | None) -> dict[str, Any]:
    out: dict[str, Any] = dict(base or {})
    if not _is_plain_dict(overlay):
        return out
    for key, val in overlay.items():
        prev = out.get(key)
        if _is_plain_dict(prev) and _is_plain_dict(val):
            out[key] = deep_merge_objects(prev, val)
        elif isinstance(prev, list) and isinstance(val, list):
            if key in ("phones", "emails"):
                merged = list(prev)
                for item in val:
                    if item is not None and item not in merged:
                        merged.append(item)
                out[key] = merged
            else:
                out[key] = val if len(val) >= len(prev) else prev
        elif val is not None and val != "":
            out[key] = val
        elif key not in out:
            out[key] = val
    return out


def merge_checko_json(existing: Any, incoming: Any) -> dict[str, Any]:
    base = existing if _is_plain_dict(existing) else {}
    over = incoming if _is_plain_dict(incoming) else {}
    if not over:
        return dict(base)
    return deep_merge_objects(base, over)


def merge_tech_json(existing: Any, incoming: Any) -> dict[str, Any]:
    base = dict(existing) if _is_plain_dict(existing) else {}
    over = dict(incoming) if _is_plain_dict(incoming) else {}
    if not over:
        return base
    merged = deep_merge_objects(base, over)
    if _is_plain_dict(base.get("bitrix24")):
        if not _is_plain_dict(over.get("bitrix24")):
            merged["bitrix24"] = base["bitrix24"]
        else:
            merged["bitrix24"] = deep_merge_objects(base["bitrix24"], over["bitrix24"])
            base_uf = base["bitrix24"].get("uf")
            over_uf = over["bitrix24"].get("uf")
            if _is_plain_dict(base_uf) and not _is_plain_dict(over_uf):
                merged["bitrix24"] = {**merged["bitrix24"], "uf": base_uf}
            elif _is_plain_dict(base_uf) and _is_plain_dict(over_uf):
                merged["bitrix24"] = {
                    **merged["bitrix24"],
                    "uf": deep_merge_objects(base_uf, over_uf),
                }
    return merged


def parse_json_field(raw: Any) -> dict[str, Any]:
    if _is_plain_dict(raw):
        return dict(raw)
    if not raw:
        return {}
    try:
        parsed = json.loads(str(raw))
        return parsed if _is_plain_dict(parsed) else {}
    except Exception:
        return {}


def merge_lead_json_patch_fields(
    lead: Any,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Мутирует data: checko_json / tech_json сливает с текущими значениями лида."""
    out = dict(data)
    if "checko_json" in out and _is_plain_dict(out["checko_json"]):
        existing = parse_json_field(getattr(lead, "checko_json", None))
        out["checko_json"] = merge_checko_json(existing, out["checko_json"])
    if "tech_json" in out and _is_plain_dict(out["tech_json"]):
        existing = parse_json_field(getattr(lead, "tech_json", None))
        out["tech_json"] = merge_tech_json(existing, out["tech_json"])
    return out
