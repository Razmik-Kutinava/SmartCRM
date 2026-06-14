"""Smoke: апрув отправки email (кнопка + голос)."""
from __future__ import annotations

from pathlib import Path

from voice.voice_action import build_voice_action

_REPO = Path(__file__).resolve().parents[3]
_EMAIL_PAGE = _REPO / "frontend" / "src" / "routes" / "email" / "+page.svelte"
_APPROVE_MODAL = _REPO / "frontend" / "src" / "components" / "EmailApproveModal.svelte"
_VOICE_HOST = _REPO / "frontend" / "src" / "components" / "VoiceActionHost.svelte"


def test_email_approve_modal_testids():
    text = _APPROVE_MODAL.read_text(encoding="utf-8")
    assert 'data-testid="email-approve-confirm"' in text
    assert 'data-testid="email-approve-reject"' in text


def test_email_page_uses_approve_modal():
    text = _EMAIL_PAGE.read_text(encoding="utf-8")
    assert "EmailApproveModal" in text
    assert "requestSendReply" in text
    assert "confirmApproveSend" in text


def test_voice_send_email_approve_with_draft():
    va = build_voice_action(
        intent="send_email",
        slots={"target": "client@test.com", "thread_id": 5},
        reply="Отправить ответ?",
        agents=["marketer"],
        module="email",
        ui_action="approve",
        agent_result={
            "marketer_output": {
                "first_email": {"subject": "Re: Тест", "body": "Черновик"},
            }
        },
    )
    assert va["ui"] == "approve"
    assert va["payload"]["draft_email"]["body"] == "Черновик"
    assert va["payload"]["slots"]["thread_id"] == 5


def test_voice_approve_shows_draft_preview():
    text = _VOICE_HOST.read_text(encoding="utf-8")
    assert "draft_email" in text
