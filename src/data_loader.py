"""
Data loader module for the dungeon crawler game
Loads game data from external JSON files
"""

import json
import os
from enum import Enum
from typing import List, Dict, Any


class ItemType(Enum):
    WEAPON = "WEAPON"
    ARMOR = "ARMOR"
    CONSUMABLE = "CONSUMABLE"
    KEY = "KEY"
    TRIGGER = "TRIGGER"


class DataProvider:
    """Provides access to game data loaded from external files"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.items_data = self._load_json("items.json")
        self.enemies_data = self._load_json("enemies.json")
        self.rooms_data = self._load_json("rooms.json")
        self.npcs_data = self._load_json("npcs.json")
    
    def _load_json(self, filename):
        """Load JSON data from a file in the data directory"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {filename} not found in {self.data_dir}")
            return {}
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {filename}")
            return {}
    
    def get_all_items(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return all item definitions"""
        return self.items_data
    
    def get_weapons(self) -> List[Dict[str, Any]]:
        """Return all weapon definitions"""
        return self.items_data.get("weapons", [])
    
    def get_armor(self) -> List[Dict[str, Any]]:
        """Return all armor definitions"""
        return self.items_data.get("armor", [])
    
    def get_consumables(self) -> List[Dict[str, Any]]:
        """Return all consumable item definitions"""
        return self.items_data.get("consumables", [])
    
    def get_keys(self) -> List[Dict[str, Any]]:
        """Return all key definitions"""
        return self.items_data.get("keys", [])
    
    def get_triggers(self) -> List[Dict[str, Any]]:
        """Return all trigger item definitions"""
        return self.items_data.get("triggers", [])
    
    def get_common_enemies(self) -> List[Dict[str, Any]]:
        """Return common enemy definitions"""
        return self.enemies_data.get("common_enemies", [])
    
    def get_mid_level_enemies(self) -> List[Dict[str, Any]]:
        """Return mid-level enemy definitions"""
        return self.enemies_data.get("mid_level_enemies", [])
    
    def get_boss_enemies(self) -> List[Dict[str, Any]]:
        """Return boss enemy definitions"""
        return self.enemies_data.get("boss_enemies", [])
    
    def get_themed_enemies(self) -> List[Dict[str, Any]]:
        """Return themed enemy definitions"""
        return self.enemies_data.get("themed_enemies", [])
    
    def get_all_enemies(self) -> List[Dict[str, Any]]:
        """Return all enemy definitions combined"""
        all_enemies = []
        all_enemies.extend(self.get_common_enemies())
        all_enemies.extend(self.get_mid_level_enemies())
        all_enemies.extend(self.get_boss_enemies())
        all_enemies.extend(self.get_themed_enemies())
        return all_enemies
    
    def get_room_templates(self) -> List[Dict[str, Any]]:
        """Return all room template definitions"""
        return self.rooms_data.get("room_templates", [])
    
    def get_themed_rooms(self) -> Dict[str, Any]:
        """Return themed room definitions"""
        return self.rooms_data.get("themed_rooms", {})
    
    def get_npc_types(self) -> List[Dict[str, Any]]:
        """Return all NPC type definitions"""
        return self.npcs_data.get("npc_types", [])
    
    def get_item_by_name(self, name: str):
        """Find an item definition by name"""
        for category in ["weapons", "armor", "consumables", "keys", "triggers"]:
            items = self.items_data.get(category, [])
            for item in items:
                if item.get("name", "").lower() == name.lower():
                    return item
        return None
    
    def get_enemy_by_name(self, name: str):
        """Find an enemy definition by name"""
        for enemy in self.get_all_enemies():
            if enemy.get("name", "").lower() == name.lower():
                return enemy
        return None
    
    def get_npc_by_name(self, name: str):
        """Find an NPC definition by name"""
        for npc in self.get_npc_types():
            if npc.get("name", "").lower() == name.lower():
                return npc
        return None


# Global data provider instance
data_provider = DataProvider()


def get_data_provider():
    """Get the global data provider instance"""
    return data_provider