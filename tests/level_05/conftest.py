import pytest


@pytest.fixture
def hero():
    from dungeon.hero import Hero

    return Hero("Ada")


@pytest.fixture
def rich_hero(hero):
    hero.gold = 100
    return hero


@pytest.fixture
def backpack():
    from dungeon.inventory import Inventory

    return Inventory()


@pytest.fixture
def potion():
    from dungeon.inventory import Item

    return Item("potion", weight=0.5, value=11)


@pytest.fixture
def shop(potion):
    from dungeon.shop import Listing, Shop

    return Shop([Listing(potion, price=8, stock=3)])