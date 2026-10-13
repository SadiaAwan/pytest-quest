import random
import pytest

from dungeon.dice import roll, roll_notation


def test_roll_rejects_one_side():
    with pytest.raises(ValueError, match="a die needs at least 2 sides"):
        roll(sides=1)


def test_roll_returns_value_in_range():
    result = roll(sides=6)
    assert 1 <= result <= 6


def test_roll_notation_with_seeded_rng():
    expected_rng = random.Random(7)
    actual_rng = random.Random(7)

    expected = expected_rng.randint(1, 6) + expected_rng.randint(1, 6) + 3
    actual = roll_notation("2d6+3", rng=actual_rng)

    assert actual == expected