"""Room-related classes for the dungeon crawler game."""

from typing import List, Dict, Any, Optional
from .base import Direction
from .item import Item
from .character import Entity, NonPlayerCharacter


class RoomState:
    def __init__(self, pos: tuple, room_type: str = "empty"):
        self.pos = pos
        self.room_type = room_type
        self.items = []
        self.entities = []  # Monsters, NPCs, etc.
        self.npcs = []
        self.connections = {}  # {Direction: (x, y, z)}
        self.has_stairs_up = False
        self.has_stairs_down = False
        self.stairs_up_target = None  # Target position when going up
        self.stairs_down_target = None  # Target position when going down
        self.locked_doors = {}  # {Direction: key_required}
        self.blocked_passages = {}  # {Direction: trigger_item_required}
        self.description = "An empty, quiet room."
        self.theme = "generic"

    def add_item(self, item: Item):
        """Add an item to the room."""
        self.items.append(item)

    def add_entity(self, entity: Entity):
        """Add an entity (monster, NPC) to the room."""
        self.entities.append(entity)

    def add_npc(self, npc: NonPlayerCharacter):
        """Add an NPC to the room."""
        self.npcs.append(npc)
        self.entities.append(npc)

    def remove_entity(self, entity: Entity):
        """Remove an entity from the room."""
        if entity in self.entities:
            self.entities.remove(entity)

    def get_living_entities(self) -> List[Entity]:
        """Get all living entities in the room."""
        return [entity for entity in self.entities if entity.is_alive() and entity.name != "Player"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert room state to dictionary for serialization."""
        from .item import Item  # Import here to avoid circular dependency
        
        return {
            "pos": self.pos,
            "room_type": self.room_type,
            "items": [item.to_dict() for item in self.items],
            "entities": [{"name": e.name, "health": e.health, "max_health": e.max_health, 
                         "attack": e.attack, "defense": e.defense, "speed": e.speed,
                         "active_status_effects": getattr(e, 'active_status_effects', {})} 
                        for e in self.entities],
            "npcs": [e.name for e in self.npcs],  # We'll reconstruct NPCs separately
            "connections": {dir.value: pos for dir, pos in self.connections.items()},
            "has_stairs_up": self.has_stairs_up,
            "has_stairs_down": self.has_stairs_down,
            "stairs_up_target": self.stairs_up_target,
            "stairs_down_target": self.stairs_down_target,
            "locked_doors": {dir.value: key for dir, key in self.locked_doors.items()},
            "blocked_passages": {dir.value: item for dir, item in self.blocked_passages.items()},
            "description": self.description,
            "theme": self.theme
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create room state from dictionary for deserialization."""
        from .item import Item  # Import here to avoid circular dependency
        from .character import Entity
        
        room = cls(tuple(data["pos"]), data["room_type"])
        room.items = [Item.from_dict(item_data) for item_data in data["items"]]
        
        # Recreate entities
        for entity_data in data["entities"]:
            entity = Entity(
                name=entity_data["name"],
                health=entity_data["health"],
                attack=entity_data["attack"],
                defense=entity_data["defense"],
                speed=entity_data.get("speed", 10)
            )
            entity.max_health = entity_data["max_health"]
            entity.active_status_effects = entity_data.get("active_status_effects", {})
            room.entities.append(entity)
        
        room.connections = {Direction(dir_str): pos for dir_str, pos in data["connections"].items()}
        room.has_stairs_up = data["has_stairs_up"]
        room.has_stairs_down = data["has_stairs_down"]
        room.stairs_up_target = data.get("stairs_up_target")
        room.stairs_down_target = data.get("stairs_down_target")
        room.locked_doors = {Direction(dir_str): key for dir_str, key in data["locked_doors"].items()}
        room.blocked_passages = {Direction(dir_str): item for dir_str, item in data["blocked_passages"].items()}
        room.description = data["description"]
        room.theme = data["theme"]
        
        return room