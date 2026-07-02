"""Per-guild voice pipeline: buffers raw PCM per speaker, segments utterances
on silence gaps, transcribes them, and routes wake-name matches to the agent.

Discord clients only transmit audio packets while a user is actively
speaking, so a gap in packet arrival is a natural utterance boundary — no
local streaming VAD is needed here (faster-whisper's own vad_filter trims any
residual noise inside an utterance).
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

import numpy as np
from scipy.signal import resample_poly

import discord
import settings
from src.ai.agent import AgentCallback, PromptRequest, handle_prompt
from src.ai.transcriber import Transcriber
from src.ai.wake import match_wake

_log = logging.getLogger(__name__)

_SAMPLE_RATE = 48000
_FRAME_BYTES = 4  # 16-bit stereo
_BYTES_PER_SECOND = _SAMPLE_RATE * _FRAME_BYTES
_WATCHER_INTERVAL_S = 0.15
_MAX_CONCURRENT_JOBS = 2


@dataclass
class _UtteranceBuffer:
    chunks: list[bytes] = field(default_factory=list)
    last_packet_t: float = 0.0

    def append(self, pcm: bytes, t: float) -> None:
        self.chunks.append(pcm)
        self.last_packet_t = t

    def duration_s(self) -> float:
        total_bytes = sum(len(c) for c in self.chunks)
        return total_bytes / _BYTES_PER_SECOND

    def pcm_bytes(self) -> bytes:
        return b"".join(self.chunks)


def _pcm_to_audio(pcm: bytes) -> np.ndarray:
    usable = len(pcm) - (len(pcm) % _FRAME_BYTES)
    stereo = np.frombuffer(pcm[:usable], dtype=np.int16).reshape(-1, 2)
    mono = stereo.astype(np.float32).mean(axis=1)
    resampled = resample_poly(mono, 1, 3)  # 48kHz -> 16kHz
    return (resampled / 32768.0).astype(np.float32)


class VoicePipeline:
    def __init__(
        self,
        guild: discord.Guild,
        text_channel: discord.abc.Messageable | None,
        agent_cb: AgentCallback = handle_prompt,
    ) -> None:
        self.queue: asyncio.Queue[tuple[int, bytes, float]] = asyncio.Queue()
        self._guild = guild
        self._text_channel = text_channel
        self._agent_cb = agent_cb
        self._transcriber = Transcriber()

        self._buffers: dict[int, _UtteranceBuffer] = {}
        self._attention_until: dict[int, float] = {}
        self._pending_jobs = 0
        self._tasks: set[asyncio.Task] = set()

        self._consumer_task: asyncio.Task | None = None
        self._watcher_task: asyncio.Task | None = None

    def start(self) -> None:
        self._consumer_task = asyncio.create_task(self._consume())
        self._watcher_task = asyncio.create_task(self._watch())

    async def stop(self) -> None:
        for task in (self._consumer_task, self._watcher_task):
            if task is not None:
                task.cancel()
        for task in list(self._tasks):
            task.cancel()
        await asyncio.gather(
            *(t for t in (self._consumer_task, self._watcher_task) if t is not None),
            return_exceptions=True,
        )
        self._buffers.clear()
        self._attention_until.clear()
        self._transcriber.shutdown()

    async def _consume(self) -> None:
        while True:
            uid, pcm, t = await self.queue.get()
            buf = self._buffers.setdefault(uid, _UtteranceBuffer())
            buf.append(pcm, t)
            if buf.duration_s() >= settings.MAX_UTTERANCE_S:
                self._schedule_flush(uid)

    async def _watch(self) -> None:
        while True:
            await asyncio.sleep(_WATCHER_INTERVAL_S)
            now = time.monotonic()
            silence_timeout_s = settings.SILENCE_TIMEOUT_MS / 1000
            for uid, buf in list(self._buffers.items()):
                if now - buf.last_packet_t > silence_timeout_s:
                    self._schedule_flush(uid)

    def _schedule_flush(self, uid: int) -> None:
        buf = self._buffers.pop(uid, None)
        if buf is None:
            return
        if buf.duration_s() * 1000 < settings.MIN_UTTERANCE_MS:
            return
        if self._pending_jobs >= _MAX_CONCURRENT_JOBS:
            _log.warning("Transcription backlog full, dropping utterance from user %s", uid)
            return

        self._pending_jobs += 1
        task = asyncio.create_task(self._process(uid, buf.pcm_bytes()))
        self._tasks.add(task)
        task.add_done_callback(self._on_task_done)

    def _on_task_done(self, task: asyncio.Task) -> None:
        self._tasks.discard(task)
        self._pending_jobs -= 1
        if not task.cancelled() and task.exception():
            _log.exception("Voice pipeline task failed", exc_info=task.exception())

    async def _process(self, uid: int, pcm: bytes) -> None:
        audio = _pcm_to_audio(pcm)
        result = await self._transcriber.transcribe(audio)
        text = result.text.strip()
        if not text:
            return

        now = time.monotonic()
        attention_deadline = self._attention_until.get(uid)
        if attention_deadline is not None and now < attention_deadline:
            self._attention_until.pop(uid, None)
            prompt = text
        else:
            wake = match_wake(text, settings.BOT_NAME, settings.WAKE_FUZZ_THRESHOLD)
            if not wake.detected:
                return
            if not wake.remainder:
                self._attention_until[uid] = now + settings.ATTENTION_WINDOW_S
                return
            prompt = wake.remainder

        member = self._guild.get_member(uid)
        user_name = member.display_name if member else f"user {uid}"

        request = PromptRequest(
            user_id=uid,
            user_name=user_name,
            guild_id=self._guild.id,
            text_channel=self._text_channel,
            prompt=prompt,
            language=result.language,
            timestamp=time.time(),
        )
        reply = await self._agent_cb(request)
        if reply and self._text_channel is not None:
            await self._text_channel.send(reply)
