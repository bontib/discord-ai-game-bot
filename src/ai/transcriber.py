"""Multilingual speech-to-text via faster-whisper.

Runs on CPU (int8) or GPU (CUDA) depending on settings. The model is loaded
lazily on first use inside a dedicated single-worker executor so the ~1-2GB
load never blocks the asyncio event loop / Discord gateway heartbeat.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import numpy as np
from faster_whisper import WhisperModel

import settings


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str
    duration: float


class Transcriber:
    def __init__(self) -> None:
        self._model: WhisperModel | None = None
        self._executor = ThreadPoolExecutor(max_workers=1)

    def _load(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(
                settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE,
                cpu_threads=settings.WHISPER_CPU_THREADS,
                download_root=settings.MODELS_DIR,
            )
        return self._model

    async def transcribe(self, audio: np.ndarray) -> TranscriptionResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._transcribe_blocking, audio)

    def _transcribe_blocking(self, audio: np.ndarray) -> TranscriptionResult:
        model = self._load()
        segments, info = model.transcribe(
            audio,
            language=settings.WHISPER_LANGUAGE,
            vad_filter=True,
            beam_size=1,
            condition_on_previous_text=False,
        )
        # segments is a lazy generator tied to the model's internal state;
        # it must be fully consumed here, on the executor thread.
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return TranscriptionResult(text=text, language=info.language, duration=info.duration)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False)
