"""POST /api/leads/{id}/raw-inbox — сырьё → поля / паспорт / RAG."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.lead_contacts import apply_contacts_patch
from core.raw_inbox import process_raw_inbox_chunk
from db.models import Lead
from db.session import get_db
from rag.ingest import ingest_manual_text

logger = logging.getLogger(__name__)

router = APIRouter()


class RawInboxBody(BaseModel):
    text: str = Field(..., min_length=1)
    ingest_rag: bool = True
    use_llm: bool = True


def _empty_val(val: Any) -> bool:
    text = str(val or "").strip()
    return not text or text in ("—", "-", "n/a", "None", "null")


def _lead_as_dict(lead: Lead) -> dict[str, Any]:
    d = lead.to_dict()
    d["checko_json"] = d.get("checko") or {}
    return d


@router.post("/{lead_id}/raw-inbox")
async def post_raw_inbox(
    lead_id: int,
    body: RawInboxBody,
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, detail="Текст сырья пуст")

    try:
        result = await process_raw_inbox_chunk(
            _lead_as_dict(lead), text, use_llm=body.use_llm
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc

    patch = dict(result.get("patch") or {})
    if "contacts" in patch:
        sync = apply_contacts_patch(lead, patch["contacts"])
        patch["contacts"] = sync["contacts"]
        for k, v in sync.items():
            if k in ("contacts", "approvals"):
                continue
            if k in patch and not _empty_val(patch.get(k)):
                continue
            if k in ("phone", "email", "contact", "position") and not _empty_val(
                getattr(lead, k, None)
            ):
                continue
            patch[k] = v
        if sync.get("approvals"):
            from core.lead_approvals import merge_approvals_payload

            patch["approvals"] = merge_approvals_payload(
                getattr(lead, "approvals", None), sync["approvals"]
            )

    if "checko_json" in patch and isinstance(patch["checko_json"], dict):
        lead.checko_json = json.dumps(patch["checko_json"], ensure_ascii=False, default=str)
        del patch["checko_json"]

    for key, val in patch.items():
        if hasattr(lead, key):
            setattr(lead, key, val)

    await db.commit()
    await db.refresh(lead)

    rag_info: dict[str, Any] = {"chunks": 0, "skipped": not body.ingest_rag}
    if body.ingest_rag:
        company = (lead.company or "lead").strip() or "lead"
        summary = result.get("summary") or ""
        excerpt = result.get("rag_excerpt") or text[:12_000]
        rag_text = f"{summary}\n\n---\nИсходный текст:\n{excerpt}"
        try:
            rag_info = ingest_manual_text(
                rag_text,
                title=f"raw_inbox:{lead_id}:{company[:40]}",
                tags="raw_inbox,lead",
                for_agent="all",
                dry_run=False,
                extra_metadata={
                    "lead_id": str(lead_id),
                    "company": company,
                    "source_type": "raw_inbox",
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("raw_inbox RAG ingest failed lead=%s: %s", lead_id, exc)
            rag_info = {"chunks": 0, "error": str(exc)[:200]}

    return {
        "summary": result.get("summary"),
        "filled_keys": result.get("filled_keys") or [],
        "extract": result.get("extract") or {},
        "rag": {
            "chunks": rag_info.get("chunks", 0),
            "error": rag_info.get("error"),
            "skipped": rag_info.get("skipped"),
        },
        "lead": lead.to_dict(),
    }
