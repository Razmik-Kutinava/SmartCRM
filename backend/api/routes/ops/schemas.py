"""Ops API — Pydantic-схемы запросов и ответов."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class FeedbackBody(BaseModel):
    trace_id: str
    feedback: str  # "good" | "bad"


class EvalCase(BaseModel):
    text: str
    expected_intent: Optional[str] = None


class EvalBody(BaseModel):
    cases: Optional[list[EvalCase]] = None
    models: list[str] = ["groq", "hermes3"]
    scenario_source: Literal["builtin", "db_approved", "builtin_and_db"] = "builtin"


class SnapshotBody(BaseModel):
    label: str = ""


class BaselineBody(BaseModel):
    snapshot_id: str


class ResolveQueueBody(BaseModel):
    status: str  # done | dismissed
    note: str = ""


class HermesPromptBody(BaseModel):
    prompt: str


class WhisperSettingsBody(BaseModel):
    """Параметры Groq Whisper (сохраняются в backend/data/whisper_settings.json)."""

    model_config = ConfigDict(populate_by_name=True)

    whisper_model: str = Field(
        default="whisper-large-v3-turbo",
        alias="model",
        description="Модель Groq Whisper",
    )
    language: str = "ru"
    temperature: float = 0.0
    prompt: str = ""
    ffmpeg_preprocess: bool = True


class AddExampleBody(BaseModel):
    phrase: str
    intent: str
    slots: dict = {}
    reply: str = ""


class SuggestPromptBody(BaseModel):
    max_bad_traces: int = 10


class AgentPromptBody(BaseModel):
    prompt: str


class AgentRunBody(BaseModel):
    intent: str = "create_lead"
    slots: dict = {}
    transcript: str = ""
    lead_id: Optional[int] = None
    instruction: str = ""


class CrmSettingsUpdate(BaseModel):
    stages: Optional[list[str]] = None
    priority_thresholds: Optional[dict[str, Any]] = None
    score_range: Optional[dict[str, Any]] = None
    default_new_lead_score: Optional[int] = None
    notes: Optional[str] = None
    manager_sets_score: Optional[bool] = None
    agents_may_update_score: Optional[bool] = None
    scoring_advisory_enabled: Optional[bool] = None
    scoring_advisory: Optional[dict[str, Any]] = None
    stage_transition_rules: Optional[list[dict[str, Any]]] = None
