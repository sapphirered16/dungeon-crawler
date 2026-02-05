"""Item class for the dungeon crawler game."""

from typing import Dict, Any
from .base import ItemType


class Item:
    def __init__(self, name: str, item_type: ItemType, value: int = 0, description: str = "", 
                 attack_bonus: int = 0, defense_bonus: int = 0, status_effect: str = None, 
                 status_chance: float = 0.0, status_damage: int = 0, status_effects: Dict[str, int] = None,
                 health_bonus: int = 0):
        self.name = name
        self.item_type = item_type
        self.value = value
        self.description = description
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.health_bonus = health_bonus  # Added for consumable items that heal
        self.status_effect = status_effect
        self.status_chance = status_chance
        self.status_damage = status_damage
        self.status_effects = status_effects if status_effects is not None else {}  # For items that can have multiple status effects

    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary for serialization."""
        return {
            "name": self.name,
            "item_type": self.item_type.value,
            "value": self.value,
            "description": self.description,
            "attack_bonus": self.attack_bonus,
            "defense_bonus": self.defense_bonus,
            "health_bonus": self.health_bonus,
            "status_effect": self.status_effect,
            "status_chance": self.status_chance,
            "status_damage": self.status_damage,
            "status_effects": self.status_effects
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create item from dictionary for deserialization."""
        item = cls(
            name=data["name"],
            item_type=ItemType(data["item_type"]),
            value=data.get("value", 0),
            description=data.get("description", ""),
            attack_bonus=data.get("attack_bonus", 0),
            defense_bonus=data.get("defense_bonus", 0),
            health_bonus=data.get("health_bonus", 0),
            status_effect=data.get("status_effect"),
            status_chance=data.get("status_chance", 0.0),
            status_damage=data.get("status_damage", 0),
            status_effects=data.get("status_effects", {})
        )
        return item