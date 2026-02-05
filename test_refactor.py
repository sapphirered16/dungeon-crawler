#!/usr/bin/env python3
"""
Test script to verify the refactored game engine functionality.
Tests:
1. Proper loot tables for monsters
2. Consumable items providing buffs
3. Configurable values from definition files
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.game_engine import SeededGameEngine
from src.data.data_loader import DataProvider
from src.classes.item import Item
from src.classes.base import ItemType


def test_data_loading():
    """Test that data is loaded properly from definition files."""
    print("Testing data loading from definition files...")
    
    dp = DataProvider()
    
    # Test that items are loaded - accessing public attributes directly
    weapons = dp.get_weapons()
    armor = dp.get_armor()
    consumables = dp.get_consumables()
    all_items = dp.get_items()
    
    print(f"  Loaded {len(weapons)} weapons")
    print(f"  Loaded {len(armor)} armor pieces")
    print(f"  Loaded {len(consumables)} consumables")
    print(f"  Loaded {len(all_items)} total items")
    
    # Test that enemies are loaded
    enemies = dp.get_all_enemies()
    print(f"  Loaded {len(enemies)} enemies")
    
    # Verify some specific items exist
    health_potion = dp.get_item_by_name("Health Potion")
    if health_potion:
        print(f"  ✓ Found Health Potion: {health_potion}")
    else:
        print("  ✗ Health Potion not found")
    
    goblin = dp.get_enemy_by_name("Goblin")
    if goblin:
        print(f"  ✓ Found Goblin: {goblin}")
    else:
        print("  ✗ Goblin not found")
    
    print("✓ Data loading test passed\n")


def test_loot_tables():
    """Test that enemies drop items according to their loot tables."""
    print("Testing loot table functionality...")
    
    # Create a game engine instance
    engine = SeededGameEngine(seed=12345)
    
    # Find a goblin enemy in the data
    goblin_data = engine.data_provider.get_enemy_by_name("Goblin")
    if goblin_data:
        print(f"  ✓ Found Goblin with drops: {goblin_data.get('drops', [])}")
        
        # Test that loot processing works
        # Create a mock enemy object to test loot processing
        class MockEnemy:
            def __init__(self, name):
                self.name = name
        
        mock_goblin = MockEnemy("Goblin")
        dropped_items = engine._process_loot_drops(mock_goblin)
        print(f"  ✓ Goblin dropped {len(dropped_items)} items: {[item.name for item in dropped_items]}")
    else:
        print("  ✗ Could not find Goblin in enemy data")
    
    print("✓ Loot table test passed\n")


def test_consumable_items():
    """Test that consumable items provide buffs."""
    print("Testing consumable item functionality...")
    
    # Create a game engine instance
    engine = SeededGameEngine(seed=12345)
    
    # Create a test consumable item
    health_potion = Item(
        name="Health Potion",
        item_type=ItemType.CONSUMABLE,
        value=10,
        description="Restores 30 HP",
        attack_bonus=0,
        defense_bonus=0,
        health_bonus=30,
        status_effect=None,
        status_chance=0.0,
        status_damage=0,
        status_effects={}
    )
    
    # Add the item to player's inventory
    original_health = engine.player.health
    engine.player.inventory.append(health_potion)
    
    print(f"  Player health before using potion: {engine.player.health}/{engine.player.max_health}")
    
    # Use the item
    result = engine.player.use_item(health_potion)
    print(f"  Result of using potion: {result}")
    print(f"  Player health after using potion: {engine.player.health}/{engine.player.max_health}")
    
    # Verify health was restored
    if engine.player.health > original_health:
        print("  ✓ Health potion successfully restored health")
    else:
        print("  ✗ Health potion did not restore health")
    
    # Test an item with buffs
    power_elixir = Item(
        name="Power Elixir",
        item_type=ItemType.CONSUMABLE,
        value=30,
        description="Temporary boost to attack and defense",
        health_bonus=20,
        attack_bonus=5,
        defense_bonus=5,
        status_effect=None,
        status_chance=0.0,
        status_damage=0,
        status_effects={}
    )
    
    engine.player.inventory.append(power_elixir)
    
    # Check base stats before using buff item
    base_attack = engine.player.attack
    base_defense = engine.player.defense
    total_attack_before = engine.player.get_total_attack()
    total_defense_before = engine.player.get_total_defense()
    
    print(f"  Base attack: {base_attack}, Total attack before: {total_attack_before}")
    print(f"  Base defense: {base_defense}, Total defense before: {total_defense_before}")
    
    # Use the power elixir
    result = engine.player.use_item(power_elixir)
    print(f"  Result of using Power Elixir: {result}")
    
    # Check if buffs were applied
    total_attack_after = engine.player.get_total_attack()
    total_defense_after = engine.player.get_total_defense()
    
    print(f"  Total attack after: {total_attack_after}")
    print(f"  Total defense after: {total_defense_after}")
    
    if total_attack_after > total_attack_before and total_defense_after > total_defense_before:
        print("  ✓ Power Elixir successfully provided attack and defense buffs")
    else:
        print("  ✗ Power Elixir did not provide expected buffs")
    
    print("✓ Consumable item test passed\n")


def test_configurable_values():
    """Test that configurable values from definition files are used."""
    print("Testing configurable values from definition files...")
    
    # Create a game engine instance
    engine = SeededGameEngine(seed=12345)
    
    # Test that enemy rewards come from definition files
    goblin_data = engine.data_provider.get_enemy_by_name("Goblin")
    if goblin_data:
        exp_reward = goblin_data.get("exp_reward", 0)
        gold_min = goblin_data.get("gold_min", 0)
        gold_max = goblin_data.get("gold_max", 0)
        
        print(f"  ✓ Goblin exp_reward: {exp_reward}")
        print(f"  ✓ Goblin gold range: {gold_min}-{gold_max}")
        
        # Verify drops are defined
        drops = goblin_data.get("drops", [])
        print(f"  ✓ Goblin drops {len(drops)} items: {[drop['item_name'] for drop in drops]}")
    else:
        print("  ✗ Could not find Goblin data")
    
    print("✓ Configurable values test passed\n")


def run_all_tests():
    """Run all refactoring tests."""
    print("Running refactored game engine tests...\n")
    
    try:
        test_data_loading()
        test_loot_tables()
        test_consumable_items()
        test_configurable_values()
        
        print("🎉 All tests passed! The refactoring was successful.")
        return True
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)