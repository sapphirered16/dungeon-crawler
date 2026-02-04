"""Entity-related classes for the dungeon crawler game."""

from enum import Enum
from typing import List, Set, Tuple
from ..items import Item, ItemType


class EntityType(Enum):
    PLAYER = "player"
    ENEMY = "enemy"


class Entity:
    def __init__(self, name: str, health: int, attack: int, defense: int):
        self.name = name
        self.max_health = health
        self.health = health
        self.attack = attack
        self.defense = defense

    def is_alive(self):
        return self.health > 0

    def take_damage(self, damage: int) -> int:
        actual_damage = max(0, damage - self.defense)
        self.health = max(0, self.health - actual_damage)
        return actual_damage


class Player(Entity):
    def __init__(self, name: str):
        super().__init__(name, 100, 10, 5)  # Default starting stats
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 100
        self.inventory: List[Item] = []
        self.equipped_weapon: Item = None
        self.equipped_armor: Item = None
        self.gold = 0
        self.position: Tuple[int, int, int] = (0, 0, 0)  # x, y, floor
        
        # Scoring and tracking stats
        self.score = 0
        self.enemies_defeated = 0
        self.treasures_collected = 0
        self.floors_explored: Set[int] = set()
        self.rooms_explored: Set[Tuple[int, int, int]] = set()
        self.distance_traveled = 0

    def gain_experience(self, exp: int):
        """Gain experience and potentially level up."""
        self.experience += exp
        if self.experience >= self.experience_to_next_level:
            self.level_up()

    def level_up(self):
        """Level up the player."""
        self.level += 1
        self.max_health += 20
        self.health = self.max_health
        self.attack += 5
        self.defense += 2
        
        # Increase experience requirement
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)
        
        print(f"\n*** LEVEL UP! You are now level {self.level}! ***")
        print(f"Stats increased: HP: +20, Attack: +5, Defense: +2")

    def equip_item(self, item: Item):
        """Equip an item."""
        if item.type == ItemType.WEAPON:
            if self.equipped_weapon:
                # Unequip current weapon first
                self.unequip_item(ItemType.WEAPON)
            self.equipped_weapon = item
            self.attack += item.attack_bonus
            self.defense += item.defense_bonus
            self.max_health += item.health_bonus
            self.health += item.health_bonus
        elif item.type == ItemType.ARMOR:
            if self.equipped_armor:
                # Unequip current armor first
                self.unequip_item(ItemType.ARMOR)
            self.equipped_armor = item
            self.defense += item.defense_bonus
            self.max_health += item.health_bonus
            self.health += item.health_bonus

    def unequip_item(self, item_type: ItemType):
        """Unequip an item."""
        if item_type == ItemType.WEAPON and self.equipped_weapon:
            item = self.equipped_weapon
            self.attack -= item.attack_bonus
            self.defense -= item.defense_bonus
            self.max_health -= item.health_bonus
            # Ensure health doesn't exceed max
            self.health = min(self.health, self.max_health)
            self.equipped_weapon = None
        elif item_type == ItemType.ARMOR and self.equipped_armor:
            item = self.equipped_armor
            self.defense -= item.defense_bonus
            self.max_health -= item.health_bonus
            # Ensure health doesn't exceed max
            self.health = min(self.health, self.max_health)
            self.equipped_armor = None

    def take_damage(self, damage: int) -> int:
        """Override take_damage to account for equipped armor."""
        # Calculate damage reduction from equipped armor
        total_defense = self.defense
        if self.equipped_armor:
            total_defense += self.equipped_armor.defense_bonus
            
        actual_damage = max(0, damage - total_defense)
        self.health = max(0, self.health - actual_damage)
        return actual_damage