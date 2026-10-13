import pytest

from dungeon.hero import Hero


@pytest.mark.parametrize("max_hp", [0, -1])
def test_hero_rejects_non_positive_max_hp(max_hp):
    with pytest.raises(ValueError, match="max_hp must be positive"):
        Hero(name="Sadia", max_hp=max_hp)


def test_negative_healing_preserves_hp():
    hero = Hero(name="Sadia", hp=50)

    with pytest.raises(ValueError, match="healing cannot be negative"):
        hero.heal(-1)

    assert hero.hp == 50


def test_negative_xp_preserves_progress():
    hero = Hero(name="Sadia", level=2, xp=30)

    with pytest.raises(ValueError, match="xp cannot be negative"):
        hero.gain_xp(-1)

    assert hero.level == 2
    assert hero.xp == 30