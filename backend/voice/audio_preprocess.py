"""
Нормализация аудио перед Whisper: 16 kHz mono WAV, highpass + loudnorm.
Улучшает распознавание при шуме и тихом сигнале (ffmpeg должен быть в PATH).
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

FFMPEG_BIN = os.getenv("WHISPER_FFMPEG_PATH", "ffmpeg")
# Фильтр: срез НЧ-гула, выравнивание громкости (однопроходный loudnorm)
_AFFILTER_DEFAULT = os.getenv(
    "WHISPER_FFMPEG_AF",
    "highpass=f=80,loudnorm=I=-16:TP=-1.5:LRA=11",
)


def ffmpeg_available() -> bool:
    if os.path.isfile(FFMPEG_BIN):
        return True
    return shutil.which(FFMPEG_BIN) is not None


async def normalize_to_wav_16k_mono(audio_bytes: bytes, suffix: str = ".webm") -> Optional[bytes]:
    """
    Конвертирует произвольный формат в 16 kHz mono WAV.
    При ошибке возвращает None — вызывающий код подставит исходные байты.
    """
    if not audio_bytes:
        return None

    in_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
            tmp_in.write(audio_bytes)
            in_path = tmp_in.name

        proc = await asyncio.create_subprocess_exec(
            FFMPEG_BIN,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            in_path,
            "-af",
            _AFFILTER_DEFAULT,
            "-ar",
            "16000",
            "-ac",
            "1",
            "-f",
            "wav",
            "pipe:1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = (stderr or b"").decode("utf-8", errors="replace")[-400:]
            logger.warning("ffmpeg нормализация не удалась: %s", err)
            return None
        if not stdout:
            return None
        return stdout
    except FileNotFoundError:
        logger.warning("ffmpeg не найден (%s) — пропускаем нормализацию", FFMPEG_BIN)
        return None
    except Exception as e:
        logger.warning("Ошибка нормализации аудио: %s", e)
        return None
    finally:
        if in_path:
            try:
                os.unlink(in_path)
            except OSError:
                pass
