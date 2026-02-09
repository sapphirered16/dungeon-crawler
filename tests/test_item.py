"""Unit tests for item class."""

import unittest
from classes.item import Item
from classes.base import ItemType


class TestItem(unittest.TestCase):
    def setUp(self):
        self.item = Item(
            name="Test Sword",
            item_type=ItemType.WEAPON,
            value=100,
            description="A test sword",
            attack_bonus=5,
            defense_bonus=2,
            status_effect="burn",
            status_chance=0.3,
            status_damage=3
        )

    def test_item_initialization(self):
        """Test that item initializes correctly."""
        self.assertEqual(self.item.name, "Test Sword")
        self.assertEqual(self.item.item_type, ItemType.WEAPON)
        self.assertEqual(self.item.value, 100)
        self.assertEqual(self.item.description, "A test sword")
        self.assertEqual(self.item.attack_bonus, 5)
        self.assertEqual(self.item.defense_bonus, 2)
        self.assertEqual(self.item.status_effect, "burn")
        self.assertEqual(self.item.status_chance, 0.3)
        self.assertEqual(self.item.status_damage, 3)

    def test_to_dict(self):
        """Test converting item to dictionary."""
        item_dict = self.item.to_dict()
        
        self.assertEqual(item_dict["name"], "Test Sword")
        self.assertEqual(item_dict["item_type"], "weapon")  # Should be value, not enum
        self.assertEqual(item_dict["value"], 100)
        self.assertEqual(item_dict["description"], "A test sword")
        self.assertEqual(item_dict["attack_bonus"], 5)
        self.assertEqual(item_dict["defense_bonus"], 2)
        self.assertEqual(item_dict["status_effect"], "burn")
        self.assertEqual(item_dict["status_chance"], 0.3)
        self.assertEqual(item_dict["status_damage"], 3)

    def test_from_dict(self):
        """Test creating item from dictionary."""
        item_dict = {
            "name": "Created Sword",
            "item_type": "weapon",
            "value": 150,
            "description": "A created sword",
            "attack_bonus": 8,
            "defense_bonus": 3,
            "status_effect": "poison",
            "status_chance": 0.25,
            "status_damage": 5,
            "status_effects": {"burn": 2}
        }
        
        created_item = Item.from_dict(item_dict)
        
        self.assertEqual(created_item.name, "Created Sword")
        self.assertEqual(created_item.item_type, ItemType.WEAPON)
        self.assertEqual(created_item.value, 150)
        self.assertEqual(created_item.description, "A created sword")
        self.assertEqual(created_item.attack_bonus, 8)
        self.assertEqual(created_item.defense_bonus, 3)
        self.assertEqual(created_item.status_effect, "poison")
        self.assertEqual(created_item.status_chance, 0.25)
        self.assertEqual(created_item.status_damage, 5)
        self.assertEqual(created_item.status_effects, {"burn": 2})

    def test_different_item_types(self):
        """Test creating items with different types."""
        weapon = Item("Sword", ItemType.WEAPON, 50)
        armor = Item("Shield", ItemType.ARMOR, 30)
        consumable = Item("Health Potion", ItemType.CONSUMABLE, 20)
        key = Item("Golden Key", ItemType.KEY, 10)
        trigger = Item("Rune", ItemType.TRIGGER, 15)
        
        self.assertEqual(weapon.item_type, ItemType.WEAPON)
        self.assertEqual(armor.item_type, ItemType.ARMOR)
        self.assertEqual(consumable.item_type, ItemType.CONSUMABLE)
        self.assertEqual(key.item_type, ItemType.KEY)
        self.assertEqual(trigger.item_type, ItemType.TRIGGER)

    def test_item_with_defaults(self):
        """Test creating item with default values."""
        minimal_item = Item("Basic Item", ItemType.CONSUMABLE)
        
        self.assertEqual(minimal_item.name, "Basic Item")
        self.assertEqual(minimal_item.item_type, ItemType.CONSUMABLE)
        self.assertEqual(minimal_item.value, 0)
        self.assertEqual(minimal_item.description, "")
        self.assertEqual(minimal_item.attack_bonus, 0)
        self.assertEqual(minimal_item.defense_bonus, 0)
        self.assertIsNone(minimal_item.status_effect)
        self.assertEqual(minimal_item.status_chance, 0.0)
        self.assertEqual(minimal_item.status_damage, 0)


if __name__ == '__main__':
    unittest.main()