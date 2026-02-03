import json
import random
import os
from enum import Enum
from typing import List, Dict, Optional, Tuple


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    KEY = "key"


class Entity:
    def __init__(self, name: str, health: int, attack: int, defense: int):
        self.name = name
        self.max_health = health
        self.health = health
        self.attack = attack
        self.defense = defense

    def take_damage(self, damage: int):
        actual_damage = max(1, damage - self.defense)  # Minimum 1 damage
        self.health -= actual_damage
        return actual_damage

    def is_alive(self):
        return self.health > 0


class Item:
    def __init__(self, name: str, item_type: ItemType, value: int = 0, 
                 attack_bonus: int = 0, defense_bonus: int = 0, health_bonus: int = 0):
        self.name = name
        self.type = item_type
        self.value = value
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.health_bonus = health_bonus

    def __str__(self):
        return self.name


class Player(Entity):
    def __init__(self, name: str = "Hero"):
        super().__init__(name, health=100, attack=10, defense=5)
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 100
        self.inventory: List[Item] = []
        self.equipped_weapon: Optional[Item] = None
        self.equipped_armor: Optional[Item] = None
        self.position = (0, 0, 0)  # x, y, floor
        self.gold = 0

    @property
    def total_attack(self):
        bonus = self.equipped_weapon.attack_bonus if self.equipped_weapon else 0
        return self.attack + bonus

    @property
    def total_defense(self):
        bonus = self.equipped_armor.defense_bonus if self.equipped_armor else 0
        return self.defense + bonus

    @property
    def total_max_health(self):
        bonus = (self.equipped_armor.health_bonus if self.equipped_armor else 0) + \
                sum(item.health_bonus for item in self.inventory if item != self.equipped_armor)
        return self.max_health + bonus

    def gain_experience(self, exp: int):
        self.experience += exp
        if self.experience >= self.experience_to_next_level:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.max_health += 20
        self.health = self.max_health
        self.attack += 5
        self.defense += 2
        self.experience -= self.experience_to_next_level
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)
        print(f"\nLevel up! You are now level {self.level}.")


class Enemy(Entity):
    def __init__(self, name: str, health: int, attack: int, defense: int, 
                 exp_reward: int, gold_min: int, gold_max: int):
        super().__init__(name, health, attack, defense)
        self.exp_reward = exp_reward
        self.gold_min = gold_min
        self.gold_max = gold_max

    def generate_loot(self) -> List[Item]:
        # Basic loot generation
        loot = []
        if random.random() < 0.3:  # 30% chance to drop gold
            gold_amount = random.randint(self.gold_min, self.gold_max)
            loot.append(Item(f"{gold_amount} Gold", ItemType.CONSUMABLE, value=gold_amount))
        return loot


class Room:
    def __init__(self, x: int, y: int, floor: int):
        self.x = x
        self.y = y
        self.floor = floor
        self.entities: List[Entity] = []
        self.items: List[Item] = []
        self.connections: Dict[Direction, 'Room'] = {}
        self.room_type = "generic"  # Could be "treasure", "monster", "empty", etc.
        self.description = "A standard dungeon room."

    def connect(self, direction: Direction, room: 'Room'):
        self.connections[direction] = room
        # Connect back
        opposite_direction = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST
        }[direction]
        room.connections[opposite_direction] = self

    def has_entity(self, entity_type: type):
        return any(isinstance(e, entity_type) for e in self.entities)


class Dungeon:
    def __init__(self, width: int = 10, height: int = 10, floors: int = 5):
        self.width = width
        self.height = height
        self.floors = floors
        self.rooms: Dict[Tuple[int, int, int], Room] = {}
        self.generate_dungeon()

    def generate_dungeon(self):
        # Generate basic grid of rooms
        for floor in range(self.floors):
            for x in range(self.width):
                for y in range(self.height):
                    # Randomly skip some rooms to create irregular layout
                    if random.random() > 0.2:  # 80% of rooms exist
                        room = Room(x, y, floor)
                        
                        # Set room type
                        rand = random.random()
                        if rand < 0.1:
                            room.room_type = "treasure"
                            room.description = "A treasure room filled with gleaming objects."
                            # Add some treasure
                            if random.random() < 0.7:
                                room.items.append(self.generate_random_item())
                        elif rand < 0.3:
                            room.room_type = "monster"
                            room.description = "A room with hostile creatures lurks ahead."
                            # Add an enemy
                            room.entities.append(self.generate_random_enemy(floor))
                        elif rand < 0.4:
                            room.room_type = "trap"
                            room.description = "A dangerous-looking room with potential hazards."
                        else:
                            room.room_type = "empty"
                            room.description = "An empty, quiet room."
                        
                        self.rooms[(x, y, floor)] = room
        
        # Create connections between adjacent rooms
        for (x, y, floor), room in self.rooms.items():
            for dx, dy, direction in [(0, -1, Direction.NORTH), (0, 1, Direction.SOUTH),
                                      (1, 0, Direction.EAST), (-1, 0, Direction.WEST)]:
                neighbor_pos = (x + dx, y + dy, floor)
                if neighbor_pos in self.rooms:
                    room.connect(direction, self.rooms[neighbor_pos])

    def get_room(self, x: int, y: int, floor: int) -> Optional[Room]:
        return self.rooms.get((x, y, floor))

    def generate_random_enemy(self, floor: int) -> Enemy:
        enemy_types = [
            ("Goblin", 20, 5, 1, 20, 1, 5),
            ("Orc", 35, 8, 3, 35, 3, 8),
            ("Skeleton", 30, 7, 2, 30, 2, 6),
            ("Zombie", 25, 6, 1, 25, 1, 4),
            ("Spider", 15, 6, 0, 15, 1, 3),
            ("Ogre", 50, 12, 5, 50, 5, 12),
            ("Demon", 75, 15, 8, 75, 8, 18),
        ]
        
        # Select harder enemies for deeper floors
        eligible_enemies = [e for e in enemy_types if e[5] <= floor * 2 + 5]
        if not eligible_enemies:
            eligible_enemies = enemy_types[-1:]  # Use hardest if floor is very high
            
        enemy_data = random.choice(eligible_enemies)
        return Enemy(*enemy_data[:5], *enemy_data[5:])

    def generate_random_item(self) -> Item:
        item_types = [
            # Weapons
            ("Rusty Sword", ItemType.WEAPON, 10, 5, 0, 0),
            ("Iron Sword", ItemType.WEAPON, 25, 10, 0, 0),
            ("Steel Sword", ItemType.WEAPON, 50, 18, 0, 0),
            ("Magic Staff", ItemType.WEAPON, 40, 12, 0, 0),
            ("Dagger", ItemType.WEAPON, 15, 7, 0, 0),
            
            # Armor
            ("Leather Armor", ItemType.ARMOR, 20, 0, 5, 10),
            ("Chain Mail", ItemType.ARMOR, 40, 0, 10, 20),
            ("Plate Armor", ItemType.ARMOR, 80, 0, 18, 35),
            ("Robe", ItemType.ARMOR, 15, 0, 3, 25),
            
            # Consumables
            ("Health Potion", ItemType.CONSUMABLE, 10, 0, 0, 30),
            ("Greater Health Potion", ItemType.CONSUMABLE, 25, 0, 0, 60),
        ]
        
        return Item(*random.choice(item_types))


class GameEngine:
    def __init__(self):
        self.player = Player()
        self.dungeon = Dungeon()
        self.current_room = self.dungeon.get_room(0, 0, 0)  # Start at entrance
        if not self.current_room:
            # Find first available room if (0,0,0) wasn't generated
            for pos, room in self.dungeon.rooms.items():
                self.current_room = room
                self.player.position = pos
                break
    
    def move_player(self, direction: Direction) -> bool:
        """Attempt to move the player in the given direction."""
        if direction not in self.current_room.connections:
            print("You cannot go that way.")
            return False
        
        new_room = self.current_room.connections[direction]
        self.current_room = new_room
        self.player.position = (new_room.x, new_room.y, new_room.floor)
        
        print(f"You move {direction.value}.")
        self.describe_room()
        return True
    
    def describe_room(self):
        """Describe the current room to the player."""
        print(f"\n--- Floor {self.player.position[2]+1}, Room ({self.player.position[0]}, {self.player.position[1]}) ---")
        print(self.current_room.description)
        
        if self.current_room.has_entity(Enemy):
            for entity in self.current_room.entities:
                if isinstance(entity, Enemy) and entity.is_alive():
                    print(f"A {entity.name} is here!")
        
        if self.current_room.items:
            print("Items in the room:")
            for item in self.current_room.items:
                print(f"- {item.name}")
    
    def look_around(self):
        """Look around the current room."""
        self.describe_room()
    
    def show_stats(self):
        """Display player statistics."""
        print(f"\n--- {self.player.name}'s Stats ---")
        print(f"Level: {self.player.level}")
        print(f"HP: {self.player.health}/{self.player.total_max_health}")
        print(f"Attack: {self.player.total_attack}")
        print(f"Defense: {self.player.total_defense}")
        print(f"EXP: {self.player.experience}/{self.player.experience_to_next_level}")
        print(f"Gold: {self.player.gold}")
        print(f"Position: Floor {self.player.position[2]+1}, ({self.player.position[0]}, {self.player.position[1]})")
        
        if self.player.equipped_weapon:
            print(f"Weapon: {self.player.equipped_weapon.name}")
        else:
            print("Weapon: None equipped")
        
        if self.player.equipped_armor:
            print(f"Armor: {self.player.equipped_armor.name}")
        else:
            print("Armor: None equipped")
    
    def show_inventory(self):
        """Display player inventory."""
        print(f"\n--- Inventory ({len(self.player.inventory)}/10) ---")
        if not self.player.inventory:
            print("Your inventory is empty.")
            return
        
        for i, item in enumerate(self.player.inventory):
            status = ""
            if item == self.player.equipped_weapon:
                status = " [equipped as weapon]"
            elif item == self.player.equipped_armor:
                status = " [equipped as armor]"
            print(f"{i+1}. {item.name}{status}")
    
    def equip_item(self, item_index: int) -> bool:
        """Equip an item from the inventory."""
        if 0 <= item_index < len(self.player.inventory):
            item = self.player.inventory[item_index]
            
            if item.type == ItemType.WEAPON:
                # Unequip current weapon if any
                if self.player.equipped_weapon:
                    self.player.inventory.append(self.player.equipped_weapon)
                
                self.player.equipped_weapon = item
                self.player.inventory.remove(item)
                print(f"You equip the {item.name}.")
                return True
            
            elif item.type == ItemType.ARMOR:
                # Unequip current armor if any
                if self.player.equipped_armor:
                    self.player.inventory.append(self.player.equipped_armor)
                
                self.player.equipped_armor = item
                self.player.inventory.remove(item)
                print(f"You put on the {item.name}.")
                return True
            else:
                print("You cannot equip that item.")
                return False
        else:
            print("Invalid item number.")
            return False
    
    def attack_enemy(self, enemy_index: int) -> bool:
        """Attack an enemy in the current room."""
        alive_enemies = [e for e in self.current_room.entities if isinstance(e, Enemy) and e.is_alive()]
        
        if not alive_enemies:
            print("There are no enemies here to attack.")
            return False
        
        if 0 <= enemy_index < len(alive_enemies):
            enemy = alive_enemies[enemy_index]
            print(f"You attack the {enemy.name}!")
            
            # Player attacks enemy
            damage_dealt = enemy.take_damage(self.player.total_attack)
            print(f"You deal {damage_dealt} damage to the {enemy.name}.")
            
            if not enemy.is_alive():
                print(f"The {enemy.name} is defeated!")
                
                # Gain experience and loot
                self.player.gain_experience(enemy.exp_reward)
                self.player.gold += random.randint(enemy.gold_min, enemy.gold_max)
                
                # Get loot
                loot = enemy.generate_loot()
                for item in loot:
                    self.current_room.items.append(item)
                    print(f"The {enemy.name} dropped: {item.name}")
                
                return True
            else:
                # Enemy counterattacks
                damage_taken = self.player.take_damage(enemy.attack)
                print(f"The {enemy.name} hits you for {damage_taken} damage!")
                
                if not self.player.is_alive():
                    print("You have been defeated! Game over.")
                    return False
                
                return True
        else:
            print("Invalid enemy selection.")
            return False
    
    def take_item(self, item_index: int) -> bool:
        """Take an item from the current room."""
        if 0 <= item_index < len(self.current_room.items):
            item = self.current_room.items[item_index]
            
            # Check if inventory is full
            if len(self.player.inventory) >= 10:
                print("Your inventory is full! You need to drop something first.")
                return False
            
            self.current_room.items.remove(item)
            self.player.inventory.append(item)
            print(f"You take the {item.name}.")
            return True
        else:
            print("Invalid item selection.")
            return False
    
    def rest(self):
        """Rest to recover some health."""
        recovery = min(20, self.player.total_max_health - self.player.health)
        if recovery > 0:
            self.player.health = min(self.player.total_max_health, self.player.health + 20)
            print(f"You rest and recover {recovery} health.")
        else:
            print("You are already at full health.")
    
    def save_game(self, filename: str = "savegame.json"):
        """Save the current game state to a file."""
        game_state = {
            "player": {
                "name": self.player.name,
                "health": self.player.health,
                "max_health": self.player.max_health,
                "attack": self.player.attack,
                "defense": self.player.defense,
                "level": self.player.level,
                "experience": self.player.experience,
                "experience_to_next_level": self.player.experience_to_next_level,
                "inventory": [{"name": item.name, "type": item.type.value, "value": item.value, 
                              "attack_bonus": item.attack_bonus, "defense_bonus": item.defense_bonus, 
                              "health_bonus": item.health_bonus} for item in self.player.inventory],
                "equipped_weapon": self.player.equipped_weapon.name if self.player.equipped_weapon else None,
                "equipped_armor": self.player.equipped_armor.name if self.player.equipped_armor else None,
                "position": self.player.position,
                "gold": self.player.gold
            },
            "current_room": self.player.position
        }
        
        with open(filename, 'w') as f:
            json.dump(game_state, f, indent=2)
        
        print(f"Game saved to {filename}.")
    
    def load_game(self, filename: str = "savegame.json"):
        """Load a saved game state from a file."""
        try:
            with open(filename, 'r') as f:
                game_state = json.load(f)
            
            # Reconstruct player
            player_data = game_state["player"]
            self.player = Player(player_data["name"])
            self.player.health = player_data["health"]
            self.player.max_health = player_data["max_health"]
            self.player.attack = player_data["attack"]
            self.player.defense = player_data["defense"]
            self.player.level = player_data["level"]
            self.player.experience = player_data["experience"]
            self.player.experience_to_next_level = player_data["experience_to_next_level"]
            self.player.gold = player_data["gold"]
            self.player.position = tuple(player_data["position"])
            
            # Reconstruct inventory
            for item_data in player_data["inventory"]:
                item = Item(
                    name=item_data["name"],
                    item_type=ItemType(item_data["type"]),
                    value=item_data["value"],
                    attack_bonus=item_data["attack_bonus"],
                    defense_bonus=item_data["defense_bonus"],
                    health_bonus=item_data["health_bonus"]
                )
                self.player.inventory.append(item)
            
            # Equip items if they exist
            if player_data["equipped_weapon"]:
                for item in self.player.inventory:
                    if item.name == player_data["equipped_weapon"]:
                        self.player.equipped_weapon = item
                        self.player.inventory.remove(item)
                        break
            
            if player_data["equipped_armor"]:
                for item in self.player.inventory:
                    if item.name == player_data["equipped_armor"]:
                        self.player.equipped_armor = item
                        self.player.inventory.remove(item)
                        break
            
            # Set current room
            pos = self.player.position
            self.current_room = self.dungeon.get_room(pos[0], pos[1], pos[2])
            
            print(f"Game loaded from {filename}.")
            return True
        except FileNotFoundError:
            print(f"No save file found at {filename}.")
            return False
        except Exception as e:
            print(f"Error loading game: {e}")
            return False


def main():
    print("Welcome to Terminal Dungeon Crawler!")
    print("Type 'help' for a list of commands.")
    
    game = GameEngine()
    game.describe_room()
    
    while game.player.is_alive():
        try:
            command = input("\n> ").strip().lower()
            
            if command in ["quit", "exit"]:
                save_choice = input("Would you like to save before quitting? (y/n): ")
                if save_choice.lower() in ["y", "yes"]:
                    game.save_game()
                print("Thanks for playing!")
                break
            elif command == "help":
                print("\nAvailable commands:")
                print("  move <direction> - Move north, south, east, or west")
                print("  attack <number> - Attack enemy number in room")
                print("  take <number> - Take item number from room")
                print("  equip <number> - Equip item number from inventory")
                print("  look - Look around the current room")
                print("  inventory - View your inventory")
                print("  stats - View your character stats")
                print("  rest - Rest to recover health")
                print("  save - Save the game")
                print("  load - Load a saved game")
                print("  quit - Quit the game")
            elif command.startswith("move "):
                direction_str = command[5:]
                try:
                    direction = Direction(direction_str)
                    game.move_player(direction)
                except ValueError:
                    print("Invalid direction. Use: north, south, east, or west.")
            elif command.startswith("attack "):
                try:
                    enemy_num = int(command[7:]) - 1
                    if not game.attack_enemy(enemy_num):
                        if not game.player.is_alive():
                            break
                except ValueError:
                    print("Please specify a valid enemy number to attack.")
            elif command.startswith("take "):
                try:
                    item_num = int(command[5:]) - 1
                    game.take_item(item_num)
                except ValueError:
                    print("Please specify a valid item number to take.")
            elif command.startswith("equip "):
                try:
                    item_num = int(command[6:]) - 1
                    game.equip_item(item_num)
                except ValueError:
                    print("Please specify a valid item number to equip.")
            elif command == "look":
                game.look_around()
            elif command == "inventory":
                game.show_inventory()
            elif command == "stats":
                game.show_stats()
            elif command == "rest":
                game.rest()
            elif command == "save":
                game.save_game()
            elif command == "load":
                game.load_game()
            else:
                print("Unknown command. Type 'help' for a list of commands.")
        
        except KeyboardInterrupt:
            print("\n\nGame interrupted. Thanks for playing!")
            break
        except EOFError:
            print("\n\nGame ended. Thanks for playing!")
            break
    
    if not game.player.is_alive():
        print("\nGame over! You have died.")
        print("Thanks for playing!")


if __name__ == "__main__":
    main()