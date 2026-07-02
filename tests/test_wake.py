import sys
from os.path import abspath, dirname, join

sys.path.insert(0, abspath(join(dirname(__file__), "..")))

from src.ai.wake import match_wake

NAME = "Bernard"
THRESHOLD = 80


def test_name_with_command():
    result = match_wake("Bernard, roll a d20", NAME, THRESHOLD)
    assert result.detected
    assert result.remainder == "roll a d20"


def test_fuzzy_pronunciation():
    result = match_wake("Bernhard, what's the weather", NAME, THRESHOLD)
    assert result.detected
    assert result.remainder == "what's the weather"


def test_name_only():
    result = match_wake("Bernard", NAME, THRESHOLD)
    assert result.detected
    assert result.remainder == ""


def test_no_match():
    result = match_wake("hello world how are you", NAME, THRESHOLD)
    assert not result.detected


def test_name_mid_utterance_ignored_if_beyond_lookahead():
    result = match_wake(
        "so anyway I was thinking yesterday about Bernard maybe helping",
        NAME,
        THRESHOLD,
    )
    assert not result.detected


def test_empty_text():
    result = match_wake("", NAME, THRESHOLD)
    assert not result.detected


def test_transliteration_case():
    result = match_wake("bernárd can you help", NAME, THRESHOLD)
    assert result.detected
    assert result.remainder == "can you help"
