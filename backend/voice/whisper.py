"""
Groq Whisper STT — аудио → текст.
Принимает bytes (webm/wav/mp3), возвращает транскрипцию на русском.

Рекомендации качества (включены по умолчанию):
- модель Groq: whisper-large-v3-turbo или whisper-large-v3 (точнее, медленнее);
- язык ru (без авто-детекта);
- опционально ffmpeg: 16 kHz mono + highpass + loudnorm;
- prompt со словарём CRM + temperature 0.
"""
from __future__ import annotations

import logging
import os
import tempfile

from groq import AsyncGroq

from voice.audio_preprocess import ffmpeg_available, normalize_to_wav_16k_mono

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Groq: только whisper-large-v3 и whisper-large-v3-turbo (ggml-medium из whisper.cpp здесь недоступен)
# Модульные константы — дефолты при импорте; в runtime transcribe() берёт актуальные значения из
# core.voice_settings (файл backend/data/whisper_settings.json) с откатом на env.
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "ru").strip() or "ru"
WHISPER_TEMPERATURE = float(os.getenv("WHISPER_TEMPERATURE", "0"))
_DEFAULT_PROMPT = (
    "SmartCRM, голосовые команды на русском. "
    "Лид, лиды, задача, контакт, компания, этап, воронка, бюджет, сделка. "
    "ООО Ромашка, ООО Вектор, Акме, TechSoft, Техпром, Альфа. "
    "ЛПР, ИТ-директор, менеджер по продажам, ответственный. "
    "Города: Москва, Санкт-Петербург, Казань, Ереван. "
    "Имена: Иван, Мария, Петров, Сидоров. "
    "CRM, API, email, телефон."
)
WHISPER_PROMPT = os.getenv("WHISPER_PROMPT", _DEFAULT_PROMPT).strip() or _DEFAULT_PROMPT
_WHISPER_PRE = os.getenv("WHISPER_FFMPEG_PREPROCESS", "1").strip().lower()
WHISPER_FFMPEG_PREPROCESS = _WHISPER_PRE in ("1", "true", "yes", "on")

_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def _runtime_params() -> dict:
    """Актуальные параметры Whisper (UI / файл или env)."""
    from core.voice_settings import get_resolved_whisper_params

    return get_resolved_whisper_params()


def _suffix_from_filename(filename: str) -> str:
    lower = (filename or "audio.webm").lower()
    for ext in (".webm", ".wav", ".mp3", ".ogg", ".m4a", ".mp4", ".mpeg", ".mpga"):
        if lower.endswith(ext):
            return ext
    return ".webm"


async def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Транскрибирует аудио через Groq Whisper.
    audio_bytes — сырые байты аудиофайла (webm, wav, mp3, ogg).
    Возвращает текст на русском языке.
    """
    if not _client:
        raise RuntimeError("GROQ_API_KEY не задан — Whisper недоступен")

    p = _runtime_params()
    whisper_model = p["model"]
    whisper_lang = p["language"]
    whisper_temp = p["temperature"]
    whisper_prompt = p["prompt"]
    use_ffmpeg = p["ffmpeg_preprocess"]

    work_bytes = audio_bytes
    work_name = filename or "audio.webm"

    if use_ffmpeg and ffmpeg_available():
        suf = _suffix_from_filename(work_name)
        normalized = await normalize_to_wav_16k_mono(work_bytes, suffix=suf)
        if normalized:
            work_bytes = normalized
            work_name = "normalized.wav"
            logger.debug("Whisper: применена ffmpeg-нормализация (16 kHz mono WAV)")
    elif use_ffmpeg and not ffmpeg_available():
        logger.debug("Whisper: ffmpeg не найден — отправляем исходное аудио без нормализации")

    with tempfile.NamedTemporaryFile(suffix=f"_{work_name}", delete=False) as tmp:
        tmp.write(work_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            kwargs = {
                "file": (work_name, audio_file),
                "model": whisper_model,
                "language": whisper_lang,
                "response_format": "text",
                "temperature": whisper_temp,
            }
            if whisper_prompt:
                kwargs["prompt"] = whisper_prompt

            response = await _client.audio.transcriptions.create(**kwargs)

        text = response.strip() if isinstance(response, str) else response.text.strip()
        logger.info(
            f"Whisper транскрибировал: '{text[:80]}...' " if len(text) > 80 else f"Whisper: '{text}'"
        )
        return text

    finally:
        import os as _os

        _os.unlink(tmp_path)


async def health_check() -> bool:
    """Проверяет доступность Groq Whisper."""
    return bool(_client and GROQ_API_KEY)
