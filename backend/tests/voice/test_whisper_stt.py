"""Юнит-тесты Groq Whisper STT (voice.whisper, preprocess, settings, pipeline audio)."""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core import voice_settings
from tests.fixtures.voice.make_silent_wav import make_silent_wav
from voice import audio_preprocess


def test_ffmpeg_available_is_bool():
    assert isinstance(audio_preprocess.ffmpeg_available(), bool)


@pytest.mark.asyncio
async def test_normalize_returns_none_on_empty():
    assert await audio_preprocess.normalize_to_wav_16k_mono(b"") is None


def test_voice_settings_defaults_ru_model():
    env = voice_settings._env_defaults()
    assert env["language"] == "ru"
    assert env["model"] in voice_settings._ALLOWED_MODELS


def test_voice_settings_validate_rejects_bad_model():
    out = voice_settings._validate_and_normalize({"model": "ggml-medium", "temperature": 2})
    assert out["model"] in voice_settings._ALLOWED_MODELS
    assert out["temperature"] == 1.0


@pytest.mark.asyncio
async def test_transcribe_calls_groq_with_ru_params():
    captured: dict = {}

    class FakeTranscriptions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return "создай лид ромашка"

    fake_client = MagicMock()
    fake_client.audio.transcriptions.create = FakeTranscriptions().create

    wav = make_silent_wav()
    with patch("voice.whisper._client", fake_client), patch(
        "voice.whisper._runtime_params",
        return_value={
            "model": "whisper-large-v3-turbo",
            "language": "ru",
            "temperature": 0.0,
            "prompt": "тест",
            "ffmpeg_preprocess": False,
        },
    ):
        from voice.whisper import transcribe

        text = await transcribe(wav, "test.wav")

    assert text == "создай лид ромашка"
    assert captured["model"] == "whisper-large-v3-turbo"
    assert captured["language"] == "ru"
    assert captured["temperature"] == 0.0


@pytest.mark.asyncio
async def test_transcribe_raises_without_groq_key():
    with patch("voice.whisper._client", None):
        from voice.whisper import transcribe

        with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
            await transcribe(b"x", "a.webm")


@pytest.mark.asyncio
async def test_process_audio_empty_transcript_returns_noop():
    with patch("voice.pipeline.transcribe", AsyncMock(return_value="")):
        from voice.pipeline import process_audio

        out = await process_audio(b"audio")
    assert out["intent"] == "noop"
    assert "Не удалось распознать" in out["reply"]


@pytest.mark.asyncio
async def test_process_audio_passes_transcript_to_hermes():
    with patch("voice.pipeline.transcribe", AsyncMock(return_value="покажи лиды")), patch(
        "voice.pipeline.parse_intent",
        AsyncMock(return_value={"intent": "list_leads", "agents": ["analyst"], "slots": {}, "reply": "ok"}),
    ), patch(
        "voice.pipeline.traces.new_trace", return_value={"id": "t1"}
    ), patch("voice.pipeline.traces.finish_trace"), patch(
        "agents.orchestrator.run_agents",
        AsyncMock(return_value={"agents_ran": False}),
    ):
        from voice.pipeline import process_audio

        out = await process_audio(b"webm")
    assert out["transcript"] == "покажи лиды"
    assert out["intent"] == "list_leads"


@pytest.mark.asyncio
async def test_live_groq_transcribe_silent_wav():
    key = os.getenv("GROQ_API_KEY", "")
    if not key or key == "test" or len(key) < 20:
        pytest.skip("GROQ_API_KEY не задан — live STT пропущен")

    import importlib

    import voice.whisper as whisper_mod

    importlib.reload(whisper_mod)
    wav = make_silent_wav(0.3)
    text = await whisper_mod.transcribe(wav, "silent.wav")
    assert isinstance(text, str)
