"""Handoff interface between the voice pipeline and the (future) AI agent.

The voice pipeline only depends on `PromptRequest` and `AgentCallback` below,
so the real agent can replace `handle_prompt` without touching any voice
code.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import discord


@dataclass(frozen=True)
class PromptRequest:
    user_id: int
    user_name: str
    guild_id: int
    text_channel: discord.abc.Messageable | None
    prompt: str
    language: str | None
    timestamp: float


AgentCallback = Callable[[PromptRequest], Awaitable[str | None]]


async def handle_prompt(request: PromptRequest) -> str | None:
    # TODO: replace with the real agent.
    return f'{request.user_name} asked: "{request.prompt}"'
