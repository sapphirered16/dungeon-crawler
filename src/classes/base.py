"""Base classes for the dungeon crawler game."""

from enum import Enum
from typing import List, Dict, Optional, Tuple
import json
import random


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    UP = "up"
    DOWN = "down"


class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    KEY = "key"
    TRIGGER = "trigger"
    ARTIFACT = "artifact"
    TOOL = "tool"


class Entity:
    def __init__(self, name: str, health: int, attack: int, defense: int, speed: int = 10):
        self.name = name
        self.max_health = health
        self.health = health
        self.attack = attack
        self.defense = defense
        self.speed = speed  # For initiative determination
        self.active_status_effects = {}  # Initialize status effects

    def take_damage(self, damage: int):
        actual_damage = max(1, damage - self.defense)  # Minimum 1 damage
        self.health -= actual_damage
        return actual_damage

    def is_alive(self):
        return self.health > 0

    def apply_status_effects(self):
        """Apply active status effects at the beginning of the turn."""
        effects_to_remove = []
        for effect, duration in self.active_status_effects.items():
            if duration > 0:
                if effect == "burn":
                    # Burn damage is equal to 10% of max health
                    burn_damage = max(1, self.max_health // 10)
                    self.health -= burn_damage
                    print(f"{self.name} takes {burn_damage} burn damage!")
                elif effect == "poison":
                    # Poison damage is equal to 5% of max health
                    poison_damage = max(1, self.max_health // 20)
                    self.health -= poison_damage
                    print(f"{self.name} takes {poison_damage} poison damage!")
                elif effect == "regen":
                    # Regen heals 5% of max health
                    regen_amount = max(1, self.max_health // 20)
                    self.health = min(self.max_health, self.health + regen_amount)
                    print(f"{self.name} regenerates {regen_amount} health!")

                # Reduce duration
                self.active_status_effects[effect] = duration - 1
            else:
                effects_to_remove.append(effect)

        # Remove expired effects
        for effect in effects_to_remove:
            del self.active_status_effects[effect]

    def heal(self, amount: int):
        """Heal the entity by the specified amount."""
        old_health = self.health
        self.health = min(self.max_health, self.health + amount)
        healed = self.health - old_health
        return healed