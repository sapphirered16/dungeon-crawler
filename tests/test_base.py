"""Unit tests for base classes."""

import unittest
from src.classes.base import Entity, ItemType, Direction


class TestEntity(unittest.TestCase):
    def setUp(self):
        self.entity = Entity("Test Entity", 100, 10, 5)

    def test_entity_initialization(self):
        """Test that entity initializes correctly."""
        self.assertEqual(self.entity.name, "Test Entity")
        self.assertEqual(self.entity.max_health, 100)
        self.assertEqual(self.entity.health, 100)
        self.assertEqual(self.entity.attack, 10)
        self.assertEqual(self.entity.defense, 5)
        self.assertEqual(self.entity.speed, 10)

    def test_take_damage(self):
        """Test that taking damage works correctly."""
        initial_health = self.entity.health
        damage_dealt = self.entity.take_damage(20)
        
        self.assertEqual(damage_dealt, 15)  # 20 damage - 5 defense = 15
        self.assertEqual(self.entity.health, initial_health - 15)

    def test_take_damage_min_one(self):
        """Test that minimum damage is 1."""
        damage_dealt = self.entity.take_damage(3)  # Less than defense
        
        self.assertEqual(damage_dealt, 1)  # Minimum damage is 1
        self.assertEqual(self.entity.health, 99)  # 100 - 1 = 99

    def test_is_alive(self):
        """Test is_alive method."""
        self.assertTrue(self.entity.is_alive())
        
        self.entity.health = 0
        self.assertFalse(self.entity.is_alive())

    def test_heal(self):
        """Test healing functionality."""
        self.entity.health = 50  # Reduce health
        healed = self.entity.heal(20)
        
        self.assertEqual(healed, 20)
        self.assertEqual(self.entity.health, 70)

    def test_heal_capped_at_max_health(self):
        """Test that healing doesn't exceed max health."""
        self.entity.health = 90
        healed = self.entity.heal(20)  # Would exceed max health
        
        self.assertEqual(healed, 10)  # Only heal up to max
        self.assertEqual(self.entity.health, 100)

    def test_apply_status_effects_burn(self):
        """Test applying burn status effect."""
        self.entity.active_status_effects = {"burn": 2}
        initial_health = self.entity.health
        
        # Apply burn effect (should deal 10% of max health as damage)
        self.entity.apply_status_effects()
        
        expected_damage = max(1, self.entity.max_health // 10)  # 10% of max health
        self.assertEqual(self.entity.health, initial_health - expected_damage)
        self.assertEqual(self.entity.active_status_effects["burn"], 1)  # Duration reduced

    def test_apply_status_effects_poison(self):
        """Test applying poison status effect."""
        self.entity.active_status_effects = {"poison": 2}
        initial_health = self.entity.health
        
        # Apply poison effect (should deal 5% of max health as damage)
        self.entity.apply_status_effects()
        
        expected_damage = max(1, self.entity.max_health // 20)  # 5% of max health
        self.assertEqual(self.entity.health, initial_health - expected_damage)
        self.assertEqual(self.entity.active_status_effects["poison"], 1)  # Duration reduced

    def test_apply_status_effects_regen(self):
        """Test applying regen status effect."""
        self.entity.active_status_effects = {"regen": 2}
        self.entity.health = 80  # Set lower health
        
        # Apply regen effect (should heal 5% of max health)
        self.entity.apply_status_effects()
        
        expected_heal = max(1, self.entity.max_health // 20)  # 5% of max health
        self.assertEqual(self.entity.health, min(80 + expected_heal, 100))
        self.assertEqual(self.entity.active_status_effects["regen"], 1)  # Duration reduced


class TestEnums(unittest.TestCase):
    def test_direction_enum(self):
        """Test Direction enum values."""
        self.assertEqual(Direction.NORTH.value, "north")
        self.assertEqual(Direction.SOUTH.value, "south")
        self.assertEqual(Direction.EAST.value, "east")
        self.assertEqual(Direction.WEST.value, "west")
        self.assertEqual(Direction.UP.value, "up")
        self.assertEqual(Direction.DOWN.value, "down")

    def test_item_type_enum(self):
        """Test ItemType enum values."""
        self.assertEqual(ItemType.WEAPON.value, "weapon")
        self.assertEqual(ItemType.ARMOR.value, "armor")
        self.assertEqual(ItemType.CONSUMABLE.value, "consumable")
        self.assertEqual(ItemType.KEY.value, "key")
        self.assertEqual(ItemType.TRIGGER.value, "trigger")


if __name__ == '__main__':
    unittest.main()