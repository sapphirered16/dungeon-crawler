"""Data loader for the dungeon crawler game."""

import json
import os
from typing import List, Dict, Any


class DataProvider:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._ensure_data_files_exist()
        self._load_all_data()

    def _ensure_data_files_exist(self):
        """Ensure data files exist, create defaults if missing."""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create default data files if they don't exist
        default_items = [
            {"name": "Iron Sword", "type": "weapon", "value": 50, "attack_bonus": 5},
            {"name": "Steel Sword", "type": "weapon", "value": 80, "attack_bonus": 8},
            {"name": "Magic Sword", "type": "weapon", "value": 120, "attack_bonus": 12, "status_effect": "burn", "status_chance": 0.2, "status_damage": 3},
            {"name": "Leather Armor", "type": "armor", "value": 30, "defense_bonus": 3},
            {"name": "Chain Mail", "type": "armor", "value": 60, "defense_bonus": 6},
            {"name": "Plate Armor", "type": "armor", "value": 150, "defense_bonus": 12},
            {"name": "Health Potion", "type": "consumable", "value": 20, "description": "Restores 20 HP"},
            {"name": "Strength Potion", "type": "consumable", "value": 40, "description": "Temporarily increases attack"},
            {"name": "Shield", "type": "armor", "value": 60, "defense_bonus": 5},
            {"name": "Helmet", "type": "armor", "value": 40, "defense_bonus": 4},
            {"name": "Boots", "type": "armor", "value": 30, "defense_bonus": 3},
            {"name": "Cloak", "type": "armor", "value": 40, "defense_bonus": 2},
            {"name": "Bow", "type": "weapon", "value": 70, "attack_bonus": 6},
            {"name": "Staff", "type": "weapon", "value": 60, "attack_bonus": 5, "status_effect": "stun", "status_chance": 0.15},
            {"name": "Dagger", "type": "weapon", "value": 25, "attack_bonus": 4},
            {"name": "Golden Key", "type": "key", "value": 10},
            {"name": "Silver Key", "type": "key", "value": 5},
            {"name": "Crystal Key", "type": "key", "value": 20},
            {"name": "Rune", "type": "trigger", "value": 15}
        ]
        
        default_enemies = [
            {"name": "Goblin", "health": 20, "attack": 5, "defense": 2, "min_floor": 0},
            {"name": "Orc", "health": 40, "attack": 8, "defense": 4, "min_floor": 1},
            {"name": "Skeleton", "health": 25, "attack": 6, "defense": 3, "min_floor": 0},
            {"name": "Zombie", "health": 30, "attack": 7, "defense": 2, "min_floor": 0},
            {"name": "Ghost", "health": 40, "attack": 10, "defense": 5, "min_floor": 1},
            {"name": "Ogre", "health": 50, "attack": 12, "defense": 6, "min_floor": 1},
            {"name": "Troll", "health": 70, "attack": 14, "defense": 10, "min_floor": 2},
            {"name": "Demon", "health": 60, "attack": 15, "defense": 8, "min_floor": 2},
            {"name": "Dragon", "health": 100, "attack": 20, "defense": 15, "min_floor": 3},
            {"name": "Ancient Guardian", "health": 80, "attack": 18, "defense": 12, "min_floor": 2},
            {"name": "Spider", "health": 15, "attack": 5, "defense": 1, "min_floor": 0},
            {"name": "Bat", "health": 10, "attack": 4, "defense": 1, "min_floor": 0}
        ]
        
        default_npcs = [
            {"name": "Friendly Merchant", "health": 10, "attack": 3, "defense": 1, "dialogue": ["Welcome traveler!", "Need supplies?", "Watch out for monsters ahead!"]},
            {"name": "Wounded Adventurer", "health": 25, "attack": 5, "defense": 2, "dialogue": ["Please... help...", "Monsters... everywhere...", "Take this..."]},
            {"name": "Mysterious Hermit", "health": 15, "attack": 4, "defense": 3, "dialogue": ["The path forward is treacherous...", "Look for hidden passages...", "Knowledge is power."]},
            {"name": "Dungeon Guide", "health": 20, "attack": 6, "defense": 5, "dialogue": ["I can show you the way...", "Be careful in the deeper levels...", "Keys unlock more than doors."]}
        ]
        
        default_rooms = [
            {"name": "Empty Room", "type": "empty", "description": "An empty, quiet room."},
            {"name": "Treasure Room", "type": "treasure", "description": "A treasure room filled with gleaming objects."},
            {"name": "Monster Room", "type": "monster", "description": "A room with hostile creatures lurks ahead."},
            {"name": "Trap Room", "type": "trap", "description": "A room with dangerous traps awaits."},
            {"name": "NPC Room", "type": "npc", "description": "A room where an NPC awaits."},
            {"name": "Artifact Room", "type": "artifact", "description": "A room containing ancient artifacts."}
        ]
        
        files_to_create = {
            "items.json": default_items,
            "enemies.json": default_enemies,
            "npcs.json": default_npcs,
            "rooms.json": default_rooms
        }
        
        for filename, default_data in files_to_create.items():
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    json.dump(default_data, f, indent=2)

    def _load_all_data(self):
        """Load all data files."""
        try:
            with open(os.path.join(self.data_dir, "items.json"), 'r') as f:
                self.items = json.load(f)
        except FileNotFoundError:
            self.items = []
        
        try:
            with open(os.path.join(self.data_dir, "enemies.json"), 'r') as f:
                self.enemies = json.load(f)
        except FileNotFoundError:
            self.enemies = []
        
        try:
            with open(os.path.join(self.data_dir, "npcs.json"), 'r') as f:
                self.npcs = json.load(f)
        except FileNotFoundError:
            self.npcs = []
        
        try:
            with open(os.path.join(self.data_dir, "rooms.json"), 'r') as f:
                self.room_templates = json.load(f)
        except FileNotFoundError:
            self.room_templates = []

    def get_items(self) -> List[Dict[str, Any]]:
        """Get all items."""
        return self.items

    def get_enemies(self) -> List[Dict[str, Any]]:
        """Get all enemies."""
        return self.enemies

    def get_npcs(self) -> List[Dict[str, Any]]:
        """Get all NPCs."""
        return self.npcs

    def get_room_templates(self) -> List[Dict[str, Any]]:
        """Get all room templates."""
        return self.room_templates

    def get_item_by_name(self, name: str) -> Dict[str, Any]:
        """Get an item by name."""
        for item in self.items:
            if item["name"] == name:
                return item
        return None

    def get_enemy_by_name(self, name: str) -> Dict[str, Any]:
        """Get an enemy by name."""
        for enemy in self.enemies:
            if enemy["name"] == name:
                return enemy
        return None

    def refresh_data(self):
        """Refresh all data from files."""
        self._load_all_data()