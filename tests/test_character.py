"""Unit tests for character classes."""

import unittest
import random
from classes.character import Player, NonPlayerCharacter
from classes.base import ItemType
from classes.item import Item


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.player = Player("Test Hero")

    def test_player_initialization(self):
        """Test that player initializes correctly."""
        self.assertEqual(self.player.name, "Test Hero")
        self.assertEqual(self.player.max_health, 100)
        self.assertEqual(self.player.health, 100)
        self.assertEqual(self.player.attack, 10)
        self.assertEqual(self.player.defense, 5)
        self.assertEqual(self.player.level, 1)
        self.assertEqual(self.player.exp, 0)
        self.assertEqual(self.player.exp_to_next_level, 100)
        self.assertEqual(self.player.gold, 0)
        self.assertEqual(self.player.score, 0)
        self.assertEqual(self.player.enemies_defeated, 0)
        self.assertEqual(self.player.treasures_collected, 0)
        self.assertEqual(self.player.floors_explored, 0)
        self.assertEqual(self.player.distance_traveled, 0)
        self.assertIsNone(self.player.equipped_weapon)
        self.assertIsNone(self.player.equipped_armor)
        self.assertEqual(len(self.player.inventory), 0)
        self.assertEqual(self.player.position, (0, 0, 0))
        self.assertEqual(len(self.player.rooms_explored), 0)

    def test_gain_exp(self):
        """Test gaining experience points."""
        initial_level = self.player.level
        self.player.gain_exp(50)
        
        self.assertEqual(self.player.exp, 50)
        self.assertEqual(self.player.level, initial_level)  # Should not level up yet

    def test_level_up(self):
        """Test leveling up when enough experience is gained."""
        self.player.exp = 100  # Exactly enough to level up
        self.player.level_up()
        
        self.assertEqual(self.player.level, 2)
        self.assertEqual(self.player.exp, 0)
        self.assertEqual(self.player.exp_to_next_level, 150)  # Increased by 50%
        self.assertGreater(self.player.max_health, 100)  # Should have increased
        self.assertGreater(self.player.attack, 10)  # Should have increased
        self.assertGreater(self.player.defense, 5)  # Should have increased

    def test_take_item(self):
        """Test adding items to inventory."""
        item = Item("Test Item", ItemType.CONSUMABLE, 10)
        initial_inventory_size = len(self.player.inventory)
        
        self.player.take_item(item)
        
        self.assertEqual(len(self.player.inventory), initial_inventory_size + 1)
        self.assertIn(item, self.player.inventory)

    def test_equip_item_weapon(self):
        """Test equipping a weapon."""
        weapon = Item("Sword", ItemType.WEAPON, 50, attack_bonus=5)
        
        self.player.inventory.append(weapon)
        self.player.equip_item(weapon)
        
        self.assertEqual(self.player.equipped_weapon, weapon)
        self.assertNotIn(weapon, self.player.inventory)

    def test_equip_item_armor(self):
        """Test equipping armor."""
        armor = Item("Shield", ItemType.ARMOR, 30, defense_bonus=3)
        
        self.player.inventory.append(armor)
        self.player.equip_item(armor)
        
        self.assertEqual(self.player.equipped_armor, armor)
        self.assertNotIn(armor, self.player.inventory)

    def test_get_total_attack(self):
        """Test calculating total attack with equipped weapon."""
        initial_attack = self.player.get_total_attack()
        
        weapon = Item("Sword", ItemType.WEAPON, 50, attack_bonus=5)
        self.player.equipped_weapon = weapon
        
        total_attack = self.player.get_total_attack()
        self.assertEqual(total_attack, initial_attack + 5)

    def test_get_total_defense(self):
        """Test calculating total defense with equipped armor."""
        initial_defense = self.player.get_total_defense()
        
        armor = Item("Shield", ItemType.ARMOR, 30, defense_bonus=3)
        self.player.equipped_armor = armor
        
        total_defense = self.player.get_total_defense()
        self.assertEqual(total_defense, initial_defense + 3)

    def test_travel_to(self):
        """Test traveling to a new position."""
        initial_distance = self.player.distance_traveled
        initial_rooms_explored = len(self.player.rooms_explored)
        
        self.player.travel_to((5, 5, 0))
        
        self.assertEqual(self.player.position, (5, 5, 0))
        self.assertGreater(self.player.distance_traveled, initial_distance)
        self.assertGreater(len(self.player.rooms_explored), initial_rooms_explored)

    def test_to_dict_and_from_dict(self):
        """Test serializing and deserializing player."""
        # Set up player with some state
        self.player.level = 3
        self.player.exp = 75
        self.player.health = 80
        self.player.gold = 100
        self.player.score = 500
        self.player.enemies_defeated = 5
        self.player.treasures_collected = 3
        self.player.floors_explored = 2
        self.player.distance_traveled = 50
        self.player.position = (10, 10, 1)
        self.player.rooms_explored = {(0, 0, 0), (5, 5, 0), (10, 10, 1)}
        
        weapon = Item("Test Sword", ItemType.WEAPON, 50, attack_bonus=5)
        self.player.equipped_weapon = weapon
        self.player.inventory.append(Item("Potion", ItemType.CONSUMABLE, 20))
        
        # Serialize and deserialize
        player_dict = self.player.to_dict()
        new_player = Player.from_dict(player_dict)
        
        # Check that properties are preserved
        self.assertEqual(new_player.name, self.player.name)
        self.assertEqual(new_player.level, self.player.level)
        self.assertEqual(new_player.exp, self.player.exp)
        self.assertEqual(new_player.health, self.player.health)
        self.assertEqual(new_player.gold, self.player.gold)
        self.assertEqual(new_player.score, self.player.score)
        self.assertEqual(new_player.enemies_defeated, self.player.enemies_defeated)
        self.assertEqual(new_player.treasures_collected, self.player.treasures_collected)
        self.assertEqual(new_player.floors_explored, self.player.floors_explored)
        self.assertEqual(new_player.distance_traveled, self.player.distance_traveled)
        self.assertEqual(new_player.position, self.player.position)
        self.assertEqual(new_player.rooms_explored, self.player.rooms_explored)
        self.assertIsNotNone(new_player.equipped_weapon)
        self.assertEqual(new_player.equipped_weapon.name, "Test Sword")
        self.assertEqual(len(new_player.inventory), 1)
        self.assertEqual(new_player.inventory[0].name, "Potion")


class TestNonPlayerCharacter(unittest.TestCase):
    def setUp(self):
        self.npc = NonPlayerCharacter(
            name="Friendly Merchant",
            health=20,
            attack=5,
            defense=2,
            dialogue=["Hello there!", "How can I help?"]
        )

    def test_npc_initialization(self):
        """Test that NPC initializes correctly."""
        self.assertEqual(self.npc.name, "Friendly Merchant")
        self.assertEqual(self.npc.health, 20)
        self.assertEqual(self.npc.attack, 5)
        self.assertEqual(self.npc.defense, 2)
        self.assertEqual(self.npc.dialogue, ["Hello there!", "How can I help?"])
        self.assertEqual(self.npc.quest_items_given, [])
        self.assertFalse(self.npc.quest_completed)

    def test_npc_dialogue(self):
        """Test getting NPC dialogue."""
        dialogue = self.npc.get_dialogue()
        self.assertIn(dialogue, ["Hello there!", "How can I help?"])

    def test_npc_no_dialogue(self):
        """Test NPC with no dialogue."""
        npc_no_dialogue = NonPlayerCharacter("Silent NPC", 10, 3, 1)
        dialogue = npc_no_dialogue.get_dialogue()
        
        self.assertIn("doesn't seem to have anything to say", dialogue)

    def test_give_quest_item(self):
        """Test giving a quest item to player."""
        item = Item("Quest Item", ItemType.CONSUMABLE, 10)
        given_item = self.npc.give_quest_item(item)
        
        self.assertEqual(given_item, item)
        self.assertIn(item, self.npc.quest_items_given)

    def test_has_quest(self):
        """Test checking if NPC has a quest."""
        self.assertFalse(self.npc.has_quest())
        
        item = Item("Quest Item", ItemType.CONSUMABLE, 10)
        self.npc.give_quest_item(item)
        
        self.assertTrue(self.npc.has_quest())


if __name__ == '__main__':
    unittest.main()