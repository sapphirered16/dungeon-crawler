"""Item-related classes for the dungeon crawler game."""

from enum import Enum


class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    KEY = "key"
    TRIGGER = "trigger"


class Item:
    def __init__(self, name: str, item_type: ItemType, value: int = 0, 
                 attack_bonus: int = 0, defense_bonus: int = 0, health_bonus: int = 0, quantity: int = 1):
        self.name = name
        self.type = item_type
        self.value = value
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.health_bonus = health_bonus
        self.quantity = quantity

    def __str__(self):
        return self.name