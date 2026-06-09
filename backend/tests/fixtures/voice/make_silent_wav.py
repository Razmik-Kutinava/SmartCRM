"""Минимальный WAV 16 kHz mono для тестов STT (тишина)."""
from __future__ import annotations

import io
import wave


def make_silent_wav(duration_sec: float = 0.25, sample_rate: int = 16000) -> bytes:
    nframes = max(1, int(sample_rate * duration_sec))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(b"\x00\x00" * nframes)
    return buf.getvalue()
