"""Wake-name detection: fuzzy-match the bot's name inside a transcript.

No dedicated wake-word engine is used (existing ones are English-only or
commercial). Instead every utterance is transcribed by faster-whisper and the
transcript text is fuzzy-matched against BOT_NAME, tolerating multilingual
pronunciation/spelling drift ("Bernhard", "Bernárd", "bernard,").
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass

from rapidfuzz import fuzz

_LOOKAHEAD_TOKENS = 4


@dataclass(frozen=True)
class WakeResult:
    detected: bool
    remainder: str = ""


def _normalize_tokens(text: str) -> list[str]:
    stripped = text.translate(str.maketrans("", "", string.punctuation))
    return stripped.casefold().split()


def match_wake(text: str, name: str, threshold: int) -> WakeResult:
    tokens = _normalize_tokens(text)
    name_tokens = _normalize_tokens(name)
    if not tokens or not name_tokens:
        return WakeResult(detected=False)

    name_norm = " ".join(name_tokens)
    name_len = len(name_tokens)
    limit = min(len(tokens), _LOOKAHEAD_TOKENS)

    for i in range(limit):
        candidates = [(tokens[i], 1)]
        if name_len > 1 and i + name_len <= len(tokens):
            candidates.append((" ".join(tokens[i : i + name_len]), name_len))

        for candidate, consumed in candidates:
            if fuzz.ratio(candidate, name_norm) >= threshold:
                # Re-derive remainder from the original text to preserve casing/punctuation.
                remainder = _remainder_from_original(text, i + consumed)
                return WakeResult(detected=True, remainder=remainder)

    return WakeResult(detected=False)


def _remainder_from_original(text: str, skip_tokens: int) -> str:
    """Return the original text with the first `skip_tokens` words removed."""
    if skip_tokens <= 0:
        return text.strip()
    matches = list(re.finditer(r"\S+", text))
    if skip_tokens >= len(matches):
        return ""
    start = matches[skip_tokens].start()
    remainder = text[start:]
    return remainder.lstrip(string.punctuation + " ").strip()
