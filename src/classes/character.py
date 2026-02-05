"""Character-related classes for the dungeon crawler game."""

import random
from typing import List, Dict, Any
from .base import Entity, ItemType
from .item import Item


class NonPlayerCharacter(Entity):
    def __init__(self, name: str, health: int, attack: int, defense: int, dialogue: List[str] = None):
        super().__init__(name, health, attack, defense)
        self.dialogue = dialogue or []
        self.quest_items_given = []
        self.quest_completed = False

    def give_quest_item(self, item: Item):
        """Give a quest item to the player."""
        self.quest_items_given.append(item)
        return item

    def has_quest(self) -> bool:
        """Check if NPC has a quest."""
        return len(self.quest_items_given) > 0

    def get_dialogue(self) -> str:
        """Get NPC's dialogue."""
        if self.dialogue:
            return random.choice(self.dialogue)
        return f"{self.name} doesn't seem to have anything to say."


class Player(Entity):
    def __init__(self, name: str = "Hero"):
        super().__init__(name, 100, 10, 5)
        self.level = 1
        self.exp = 0
        self.exp_to_next_level = 100
        self.gold = 0
        self.score = 0
        self.enemies_defeated = 0
        self.treasures_collected = 0
        self.floors_explored = 0
        self.rooms_explored = set()
        self.distance_traveled = 0
        self.equipped_weapon = None
        self.equipped_armor = None
        self.inventory = []
        self.position = (0, 0, 0)  # x, y, z (floor)
        self.victory = False  # Track if player has won the game
        self.temporary_buffs = {}  # Store temporary stat buffs with their remaining turns

    def gain_exp(self, amount: int):
        """Gain experience points and level up if enough exp."""
        self.exp += amount
        if self.exp >= self.exp_to_next_level:
            self.level_up()

    def level_up(self):
        """Level up the player."""
        self.level += 1
        self.exp -= self.exp_to_next_level
        self.exp_to_next_level = int(self.exp_to_next_level * 1.5)  # Increase exp requirement
        
        # Improve stats
        self.max_health += 20
        self.health = self.max_health
        self.attack += 3
        self.defense += 2
        
        print(f"🎉 Level up! You are now level {self.level}!")

    def take_item(self, item: Item):
        """Add an item to the inventory."""
        self.inventory.append(item)
        if item.item_type == ItemType.WEAPON:
            self.treasures_collected += 1
        elif item.item_type == ItemType.ARMOR:
            self.treasures_collected += 1

    def equip_item(self, item: Item):
        """Equip an item if possible."""
        if item.item_type == ItemType.WEAPON:
            if self.equipped_weapon:
                self.inventory.append(self.equipped_weapon)
            self.equipped_weapon = item
            self.inventory.remove(item)
        elif item.item_type == ItemType.ARMOR:
            if self.equipped_armor:
                self.inventory.append(self.equipped_armor)
            self.equipped_armor = item
            self.inventory.remove(item)

    def get_total_attack(self) -> int:
        """Get total attack including equipped weapon and temporary buffs."""
        total = self.attack
        if self.equipped_weapon:
            total += self.equipped_weapon.attack_bonus
        # Add temporary attack buffs
        if 'attack' in self.temporary_buffs:
            total += self.temporary_buffs['attack']
        return total

    def get_total_defense(self) -> int:
        """Get total defense including equipped armor and temporary buffs."""
        total = self.defense
        if self.equipped_armor:
            total += self.equipped_armor.defense_bonus
        # Add temporary defense buffs
        if 'defense' in self.temporary_buffs:
            total += self.temporary_buffs['defense']
        return total

    def travel_to(self, new_position: tuple):
        """Travel to a new position and update distance traveled."""
        if self.position != new_position:
            old_x, old_y, old_z = self.position
            new_x, new_y, new_z = new_position
            # Calculate Manhattan distance for movement cost
            distance = abs(new_x - old_x) + abs(new_y - old_y) + abs(new_z - old_z)
            self.distance_traveled += distance
            self.position = new_position
            # Add room to explored set
            self.rooms_explored.add(new_position)
            # Update floors explored
            if new_z + 1 > self.floors_explored:
                self.floors_explored = new_z + 1

    def use_item(self, item: Item) -> str:
        """Use a consumable item to apply its effects."""
        if item.item_type != ItemType.CONSUMABLE:
            return f"{item.name} is not a consumable item."
        
        # Apply the item's effects
        result_parts = [f"You consumed {item.name}."]
        
        # Apply health bonus if present
        if item.health_bonus > 0:
            old_health = self.health
            self.heal(item.health_bonus)
            gained_health = self.health - old_health
            result_parts.append(f"Healed {gained_health} HP.")
        
        # Apply temporary attack and defense buffs
        if item.attack_bonus > 0:
            # Add temporary attack buff for 3 turns (configurable based on item)
            self.temporary_buffs['attack'] = self.temporary_buffs.get('attack', 0) + item.attack_bonus
            self.temporary_buffs['attack_turns'] = 3  # Default duration
            result_parts.append(f"Gained +{item.attack_bonus} attack for 3 turns.")
        
        if item.defense_bonus > 0:
            # Add temporary defense buff for 3 turns (configurable based on item)
            self.temporary_buffs['defense'] = self.temporary_buffs.get('defense', 0) + item.defense_bonus
            self.temporary_buffs['defense_turns'] = 3  # Default duration
            result_parts.append(f"Gained +{item.defense_bonus} defense for 3 turns.")
        
        # Apply any status effects from the item
        if item.status_effects:
            for effect, duration in item.status_effects.items():
                self.active_status_effects[effect] = duration
            result_parts.append(f"Status effects applied: {', '.join(item.status_effects.keys())}.")
        
        # Remove the item from inventory after use
        self.inventory.remove(item)
        
        return " ".join(result_parts)

    def heal_percentage(self, percentage: float):
        """Heal a percentage of max health."""
        heal_amount = int(self.max_health * percentage)
        return self.heal(heal_amount)

    def update_temporary_buffs(self):
        """Update temporary buffs at the end of each turn."""
        buffs_to_update = []
        
        # Update attack buff
        if 'attack_turns' in self.temporary_buffs and self.temporary_buffs['attack_turns'] > 0:
            self.temporary_buffs['attack_turns'] -= 1
            if self.temporary_buffs['attack_turns'] <= 0:
                # Remove the buff when duration expires
                if 'attack' in self.temporary_buffs:
                    del self.temporary_buffs['attack']
                del self.temporary_buffs['attack_turns']
        
        # Update defense buff
        if 'defense_turns' in self.temporary_buffs and self.temporary_buffs['defense_turns'] > 0:
            self.temporary_buffs['defense_turns'] -= 1
            if self.temporary_buffs['defense_turns'] <= 0:
                # Remove the buff when duration expires
                if 'defense' in self.temporary_buffs:
                    del self.temporary_buffs['defense']
                del self.temporary_buffs['defense_turns']

    def to_dict(self) -> Dict[str, Any]:
        """Convert player to dictionary for saving."""
        return {
            "name": self.name,
            "max_health": self.max_health,
            "health": self.health,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "level": self.level,
            "exp": self.exp,
            "exp_to_next_level": self.exp_to_next_level,
            "gold": self.gold,
            "score": self.score,
            "enemies_defeated": self.enemies_defeated,
            "treasures_collected": self.treasures_collected,
            "floors_explored": self.floors_explored,
            "distance_traveled": self.distance_traveled,
            "equipped_weapon": self.equipped_weapon.to_dict() if self.equipped_weapon else None,
            "equipped_armor": self.equipped_armor.to_dict() if self.equipped_armor else None,
            "inventory": [item.to_dict() for item in self.inventory],
            "position": self.position,
            "rooms_explored": list(self.rooms_explored)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create player from dictionary for loading."""
        from .item import Item  # Import here to avoid circular dependency
        
        player = cls(data["name"])
        player.max_health = data["max_health"]
        player.health = data["health"]
        player.attack = data["attack"]
        player.defense = data["defense"]
        player.speed = data.get("speed", 10)
        player.level = data["level"]
        player.exp = data["exp"]
        player.exp_to_next_level = data["exp_to_next_level"]
        player.gold = data["gold"]
        player.score = data["score"]
        player.enemies_defeated = data["enemies_defeated"]
        player.treasures_collected = data["treasures_collected"]
        player.floors_explored = data["floors_explored"]
        player.distance_traveled = data["distance_traveled"]
        player.position = tuple(data["position"])
        player.rooms_explored = set(tuple(pos) if isinstance(pos, list) else pos for pos in data.get("rooms_explored", []))
        
        # Load equipped items
        if data["equipped_weapon"]:
            player.equipped_weapon = Item.from_dict(data["equipped_weapon"])
        if data["equipped_armor"]:
            player.equipped_armor = Item.from_dict(data["equipped_armor"])
        
        # Load inventory
        for item_data in data["inventory"]:
            player.inventory.append(Item.from_dict(item_data))
        
        return player