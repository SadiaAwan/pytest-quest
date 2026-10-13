import pytest

from dungeon.hero import Hero
from dungeon.inventory import Inventory, Item
from dungeon.shop import Listing, OutOfStockError, Shop


@pytest.mark.parametrize("price, stock", [(-1, 1), (10, -1)])
def test_shop_rejects_negative_price_or_stock(price, stock):
    item = Item(name="potion", weight=1.0, value=10)
    shop = Shop()

    with pytest.raises(ValueError, match="price and stock must be non-negative"):
        shop.add_listing(Listing(item=item, price=price, stock=stock))

    assert shop.stock_of("potion") == 0


def test_price_of_unknown_item_raises():
    shop = Shop()

    with pytest.raises(OutOfStockError, match="doesn't sell"):
        shop.price_of("sword")


def test_sell_unlisted_item_pays_without_adding_listing():
    hero = Hero(name="Sadia", gold=10)
    inventory = Inventory()
    item = Item(name="gem", weight=1.0, value=11)
    inventory.add(item)
    shop = Shop()

    payout = shop.sell(hero, inventory, "gem")

    assert payout == 5
    assert hero.gold == 15
    assert inventory.count("gem") == 0
    assert inventory.find("gem") is None
    assert shop.stock_of("gem") == 0

    with pytest.raises(OutOfStockError):
        shop.price_of("gem")