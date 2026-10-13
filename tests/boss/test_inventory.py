import pytest

from dungeon.inventory import Inventory, Item


@pytest.mark.parametrize("max_weight", [0, -1])
def test_inventory_rejects_non_positive_capacity(max_weight):
    with pytest.raises(ValueError, match="max_weight must be positive"):
        Inventory(max_weight=max_weight)

@pytest.mark.parametrize("quantity", [0, -1])
def test_add_rejects_non_positive_quantity(quantity):
    inventory = Inventory()
    item = Item(name="potion", weight=1.0, value=10)

    with pytest.raises(ValueError):
        inventory.add(item, quantity=quantity)

    assert inventory.as_dict() == {}


def test_remove_one_keeps_remaining_items():
    inventory = Inventory()
    item = Item(name="potion", weight=1.0, value=10)
    inventory.add(item, quantity=3)

    removed = inventory.remove("potion", quantity=1)

    assert removed == item
    assert inventory.count("potion") == 2
    assert inventory.find("potion") == item
    assert inventory.total_weight == pytest.approx(2.0)
    assert inventory.total_value == 20
    assert len(inventory) == 2
    assert "potion" in inventory
    assert "sword" not in inventory


def test_remove_too_many_preserves_inventory():
    inventory = Inventory()
    item = Item(name="potion", weight=1.0, value=10)
    inventory.add(item, quantity=2)

    with pytest.raises(LookupError, match="not enough"):
        inventory.remove("potion", quantity=3)

    assert inventory.count("potion") == 2
    assert inventory.find("potion") == item