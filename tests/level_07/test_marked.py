"""Level 07: custom markers, skipif and strict xfail."""

import sys

import pytest

from dungeon import dice, oracle, portal


@pytest.mark.slow
def test_goblin_oracle_returns_a_known_prophecy():
    answer = oracle.consult("Will the goblin find treasure?")
    assert answer in oracle.PROPHECIES


def test_oracle_rejects_question_without_question_mark():
    with pytest.raises(ValueError):
        oracle.consult("This is not a question")


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Portal magic is not supported on Windows",
)
def test_portal_description_contains_destination():
    destination = "Stockholm"
    description = portal.open_portal(destination)
    assert destination in description


@pytest.mark.xfail(
    strict=True,
    reason="Bug #13: dice.parse drops the minus sign",
)
def test_dice_preserves_negative_modifier():
    assert dice.parse("1d6-2") == (1, 6, -2)