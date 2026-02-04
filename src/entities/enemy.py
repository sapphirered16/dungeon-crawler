"""Enemy-related classes for the dungeon crawler game."""

from . import Entity


class Enemy(Entity):
    def __init__(self, name: str, health: int, attack: int, defense: int, 
                 exp_reward: int = 10, gold_min: int = 1, gold_max: int = 5):
        super().__init__(name, health, attack, defense)
        self.exp_reward = exp_reward
        self.gold_min = gold_min
        self.gold_max = gold_min  # Fixed typo: was gold_min, should be gold_max
        self.gold_max = gold_max

    def generate_loot(self):
        """Generate random loot when defeated."""
        import random
        from ..items import Item, ItemType
        
        loot = []
        
        # Random chance to drop gold
        if random.random() < 0.7:  # 70% chance
            gold_amount = random.randint(self.gold_min, self.gold_max)
            # Create a temporary "Gold" item for display purposes
            gold_item = Item(f"{gold_amount} Gold", ItemType.CONSUMABLE, value=gold_amount)
            loot.append(gold_item)
        
        # Small chance to drop an actual item
        if random.random() < 0.2:  # 20% chance
            item_types = [
                ("Health Potion", ItemType.CONSUMABLE, 5, 0, 0, 10),
                ("Strength Potion", ItemType.CONSUMABLE, 3, 5, 0, 0),
                ("Toughness Potion", ItemType.CONSUMABLE, 3, 0, 5, 0),
                ("Old Sword", ItemType.WEAPON, 15, 3, 1, 0),
                ("Rusty Shield", ItemType.ARMOR, 12, 0, 2, 5),
                ("Magic Ring", ItemType.WEAPON, 20, 2, 2, 3),
                ("Leather Armor", ItemType.ARMOR, 18, 0, 3, 10),
            ]
            
            item_data = random.choice(item_types)
            item = Item(
                name=item_data[0],
                item_type=item_data[1],
                value=item_data[2],
                attack_bonus=item_data[3],
                defense_bonus=item_data[4],
                health_bonus=item_data[5]
            )
            loot.append(item)
        
        return loot