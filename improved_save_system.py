#!/usr/bin/env python3
"""
Improved Save System for Dungeon Crawler Game

This script implements a comprehensive save/load system that:
- Saves ONLY game state (items, NPCs, entities, player data)
- Does NOT save room details (rooms are regenerated from seed)
- Auto-saves after every game action
- Ensures procedural generation with seed-based reproducibility
"""

import json
import os
import sys
from typing import Dict, Any, List, Set, Tuple
from datetime import datetime

# Add the src directory to the path
sys.path.append('/home/sapphire/.openclaw/workspace-sapphirepine/dungeon-crawler/src')

from classes.new_dungeon import SeededDungeon
from classes.character import Player
from classes.base import Direction


class ImprovedSaveSystem:
    """Improved save system that only saves game state, not room structure."""
    
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.save_file = "savegame.json"
        self.backup_file = "savegame_backup.json"
    
    def save_game_state(self, filename: str = None) -> bool:
        """
        Save only the game state, not room structure.
        Rooms will be regenerated from seed when loading.
        """
        if filename is None:
            filename = self.save_file
        
        try:
            # Create backup of existing save file
            if os.path.exists(filename):
                self._create_backup(filename)
            
            # Collect game state data (NO room structure!)
            game_state = {
                "metadata": {
                    "seed": self.game_engine.seed,
                    "save_version": "2.0",
                    "timestamp": datetime.now().isoformat(),
                    "player_position": self.game_engine.player.position
                },
                "player": self._collect_player_state(),
                "world_changes": self._collect_world_changes(),
                "progress": self._collect_progress_data()
            }
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(game_state, f, indent=2)
            
            print(f"💾 Game state saved to {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save game: {e}")
            return False
    
    def load_game_state(self, filename: str = None) -> bool:
        """
        Load game state and regenerate dungeon from seed.
        """
        if filename is None:
            filename = self.save_file
        
        if not os.path.exists(filename):
            print(f"❌ Save file {filename} does not exist.")
            return False
        
        try:
            # Load save data
            with open(filename, 'r') as f:
                game_state = json.load(f)
            
            # Extract metadata
            metadata = game_state["metadata"]
            seed = metadata["seed"]
            
            # Regenerate dungeon from seed (this creates all rooms procedurally)
            print(f"🗺️  Regenerating dungeon from seed {seed}...")
            self.game_engine.dungeon = SeededDungeon(seed)
            self.game_engine.seed = seed
            
            # Restore player state
            self._restore_player_state(game_state["player"])
            
            # Apply world changes to the regenerated dungeon
            self._apply_world_changes(game_state["world_changes"])
            
            # Restore progress data
            self._restore_progress_data(game_state["progress"])
            
            # Update current room reference
            player_pos = tuple(metadata["player_position"])
            self.game_engine.current_room = self.game_engine.dungeon.get_room_at_position(player_pos)
            
            print(f"✅ Game state loaded from {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load game: {e}")
            return False
    
    def auto_save(self) -> bool:
        """Auto-save after game actions."""
        return self.save_game_state()
    
    def _collect_player_state(self) -> Dict[str, Any]:
        """Collect player state for saving."""
        player = self.game_engine.player
        
        player_state = {
            "stats": {
                "name": player.name,
                "level": player.level,
                "exp": player.exp,
                "exp_to_next_level": player.exp_to_next_level,
                "max_health": player.max_health,
                "health": player.health,
                "attack": player.attack,
                "defense": player.defense,
                "speed": player.speed,
                "gold": player.gold,
                "score": player.score
            },
            "position": player.position,
            "equipment": {
                "weapon": player.equipped_weapon.to_dict() if player.equipped_weapon else None,
                "armor": player.equipped_armor.to_dict() if player.equipped_armor else None
            },
            "inventory": [item.to_dict() for item in player.inventory],
            "status_effects": player.active_status_effects.copy(),
            "temporary_buffs": player.temporary_buffs.copy(),
            "exploration": {
                "enemies_defeated": player.enemies_defeated,
                "treasures_collected": player.treasures_collected,
                "floors_explored": player.floors_explored,
                "distance_traveled": player.distance_traveled,
                "rooms_explored": list(player.rooms_explored)
            }
        }
        
        return player_state
    
    def _collect_world_changes(self) -> Dict[str, Any]:
        """Collect changes to the world state (items, enemies, NPCs that have been modified)."""
        world_changes = {
            "defeated_enemies": [],
            "collected_items": [],
            "completed_quests": [],
            "unlocked_doors": [],
            "removed_obstacles": []
        }
        
        # Track defeated enemies (enemies that are no longer alive)
        for room in self.game_engine.dungeon.rooms:
            for entity in room.entities:
                if hasattr(entity, 'is_alive') and not entity.is_alive():
                    world_changes["defeated_enemies"].append({
                        "position": getattr(entity, 'position', (0, 0, 0)),
                        "name": entity.name,
                        "room_coords": (room.x, room.y, room.z)
                    })
        
        # Track items that have been picked up (no longer in rooms/grid)
        # This is complex - we'll track by checking which items are no longer in their original positions
        # For now, we'll save the current state of items in the dungeon
        
        # Save current item locations in the grid
        grid_items = {}
        for pos, cell in self.game_engine.dungeon.grid.items():
            if cell.items:
                grid_items[str(pos)] = [item.to_dict() for item in cell.items]
        world_changes["grid_items"] = grid_items
        
        # Save current room items
        room_items = {}
        for room in self.game_engine.dungeon.rooms:
            if room.items:
                room_items[f"{room.x}_{room.y}_{room.z}"] = [item.to_dict() for item in room.items]
        world_changes["room_items"] = room_items
        
        return world_changes
    
    def _collect_progress_data(self) -> Dict[str, Any]:
        """Collect game progress data."""
        return {
            "explored_positions": list(self.game_engine.explored_positions),
            "game_time": getattr(self.game_engine, 'game_time', 0),
            "turn_count": getattr(self.game_engine, 'turn_count', 0)
        }
    
    def _create_backup(self, filename: str):
        """Create backup of existing save file."""
        import shutil
        shutil.copy2(filename, self.backup_file)
    
    def _restore_player_state(self, player_state: Dict[str, Any]):
        """Restore player state from saved data."""
        from classes.item import Item
        
        # Restore basic stats
        stats = player_state["stats"]
        player = self.game_engine.player
        
        player.name = stats["name"]
        player.level = stats["level"]
        player.exp = stats["exp"]
        player.exp_to_next_level = stats["exp_to_next_level"]
        player.max_health = stats["max_health"]
        player.health = stats["health"]
        player.attack = stats["attack"]
        player.defense = stats["defense"]
        player.speed = stats["speed"]
        player.gold = stats["gold"]
        player.score = stats["score"]
        
        # Restore position
        player.position = tuple(player_state["position"])
        
        # Restore equipment
        if player_state["equipment"]["weapon"]:
            player.equipped_weapon = Item.from_dict(player_state["equipment"]["weapon"])
        if player_state["equipment"]["armor"]:
            player.equipped_armor = Item.from_dict(player_state["equipment"]["armor"])
        
        # Restore inventory
        player.inventory = []
        for item_data in player_state["inventory"]:
            item = Item.from_dict(item_data)
            player.inventory.append(item)
        
        # Restore status effects and buffs
        player.active_status_effects = player_state["status_effects"].copy()
        player.temporary_buffs = player_state["temporary_buffs"].copy()
        
        # Restore exploration data
        exploration = player_state["exploration"]
        player.enemies_defeated = exploration["enemies_defeated"]
        player.treasures_collected = exploration["treasures_collected"]
        player.floors_explored = exploration["floors_explored"]
        player.distance_traveled = exploration["distance_traveled"]
        player.rooms_explored = set(tuple(pos) if isinstance(pos, list) else pos 
                                   for pos in exploration["rooms_explored"])
    
    def _apply_world_changes(self, world_changes: Dict[str, Any]):
        """Apply world changes to the regenerated dungeon."""
        from classes.item import Item
        
        # Restore grid items
        grid_items = world_changes.get("grid_items", {})
        for pos_str, item_data_list in grid_items.items():
            pos = eval(pos_str)  # Convert string back to tuple
            if pos in self.game_engine.dungeon.grid:
                cell = self.game_engine.dungeon.grid[pos]
                cell.items = []
                for item_data in item_data_list:
                    item = Item.from_dict(item_data)
                    cell.items.append(item)
        
        # Restore room items
        room_items = world_changes.get("room_items", {})
        for room_key, item_data_list in room_items.items():
            x, y, z = map(int, room_key.split('_'))
            # Find the room
            for room in self.game_engine.dungeon.rooms:
                if room.x == x and room.y == y and room.z == z:
                    room.items = []
                    for item_data in item_data_list:
                        item = Item.from_dict(item_data)
                        room.items.append(item)
                    break
        
        # Apply defeated enemies (mark them as defeated)
        defeated_enemies = world_changes.get("defeated_enemies", [])
        for enemy_data in defeated_enemies:
            enemy_pos = tuple(enemy_data["position"])
            room_coords = enemy_data["room_coords"]
            
            # Find the room
            for room in self.game_engine.dungeon.rooms:
                if (room.x == room_coords[0] and 
                    room.y == room_coords[1] and 
                    room.z == room_coords[2]):
                    
                    # Find and defeat the enemy
                    for entity in room.entities:
                        if (entity.name == enemy_data["name"] and 
                            hasattr(entity, 'position') and 
                            entity.position == enemy_pos):
                            # Mark as defeated
                            if hasattr(entity, 'health'):
                                entity.health = 0
                            break
                    break
    
    def _restore_progress_data(self, progress_data: Dict[str, Any]):
        """Restore progress data."""
        self.game_engine.explored_positions = set(tuple(pos) if isinstance(pos, list) else pos 
                                                for pos in progress_data.get("explored_positions", []))
        
        if hasattr(self.game_engine, 'game_time'):
            self.game_engine.game_time = progress_data.get("game_time", 0)
        if hasattr(self.game_engine, 'turn_count'):
            self.game_engine.turn_count = progress_data.get("turn_count", 0)


def test_save_system():
    """Test the improved save system."""
    # This would be called from the main game to test the save system
    print("🧪 Testing improved save system...")
    
    # Create a test game
    from new_game_engine import SeededGameEngine
    
    test_seed = 12345
    game1 = SeededGameEngine(seed=test_seed)
    
    # Create save system
    save_system = ImprovedSaveSystem(game1)
    
    # Test saving
    print("📝 Testing save...")
    save_result = save_system.save_game_state("test_save.json")
    if save_result:
        print("✅ Save test passed")
    else:
        print("❌ Save test failed")
        return False
    
    # Test loading
    print("📖 Testing load...")
    game2 = SeededGameEngine(seed=test_seed + 999)  # Different seed
    save_system2 = ImprovedSaveSystem(game2)
    load_result = save_system2.load_game_state("test_save.json")
    if load_result:
        print("✅ Load test passed")
        
        # Verify the seed was restored correctly
        if game2.seed == test_seed:
            print("✅ Seed regeneration test passed")
        else:
            print(f"❌ Seed mismatch: expected {test_seed}, got {game2.seed}")
            return False
    else:
        print("❌ Load test failed")
        return False
    
    print("🎉 All save system tests passed!")
    return True


if __name__ == "__main__":
    test_save_system()