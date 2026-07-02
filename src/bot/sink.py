"""Custom py-cord sink that streams raw PCM into an asyncio queue.

py-cord 2.8.0 rewrote voice receive (see discord/voice/receive/). The
PacketRouter calls sink.write(data, data.source) from a background thread and
requires sink.is_opus(), sink.walk_children(), sink.__sink_listeners__, and a
truthy sink.client (backed by sink.vc). AudioReader never calls sink.init(vc)
(that call is commented out upstream), so callers must set `sink.vc = vc`
themselves before start_recording().
"""

from __future__ import annotations

import asyncio
import time

import discord


class StreamingSink(discord.sinks.Sink):
    __sink_listeners__: list[tuple[str, str]] = []

    def __init__(self, loop: asyncio.AbstractEventLoop, audio_queue: asyncio.Queue) -> None:
        super().__init__()
        self._loop = loop
        self._queue = audio_queue

    def is_opus(self) -> bool:
        return False

    def walk_children(self):
        return []

    def write(self, data, user) -> None:
        # Runs on the PacketRouter thread — must not touch asyncio state directly.
        user_id = getattr(user, "id", None)
        if user_id is None or not data.pcm:
            return
        self._loop.call_soon_threadsafe(
            self._queue.put_nowait, (user_id, data.pcm, time.monotonic())
        )

    def cleanup(self) -> None:
        # Never called by AudioReader (upstream cleanup call is commented out);
        # kept idempotent in case that changes.
        self.finished = True
