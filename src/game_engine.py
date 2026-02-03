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
        self.score = 0  # Total score
        self.enemies_defeated = 0  # Count of enemies defeated
        self.treasures_collected = 0  # Count of valuable items collected
        self.floors_explored = set()  # Set of floors visited
        self.rooms_explored = set()  # Set of rooms visited
        self.distance_traveled = 0  # Total moves made

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
        # Add to score based on experience gained
        self.score += exp
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


class RoomInfo:
    def __init__(self, x, y, width, height, floor):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.floor = floor
        self.center_x = x + width // 2
        self.center_y = y + height // 2

class Dungeon:
    def __init__(self, width: int = 30, height: int = 30, floors: int = 3):
        self.width = width
        self.height = height
        self.floors = floors
        self.rooms: Dict[Tuple[int, int, int], Room] = {}
        self.room_layouts = {}  # Store room boundaries for collision detection
        self.generate_dungeon()

    def generate_dungeon(self):
        # Generate structured dungeon with rooms and corridors
        for floor in range(self.floors):
            # Create rooms
            rooms_info = []
            num_rooms = random.randint(8, 15)  # Number of rooms for this floor
            
            for _ in range(num_rooms):
                # Random room size
                room_width = random.randint(3, 6)
                room_height = random.randint(3, 6)
                
                # Random position (ensuring it fits in the grid)
                x = random.randint(1, self.width - room_width - 1)
                y = random.randint(1, self.height - room_height - 1)
                
                # Check for overlap with existing rooms
                overlaps = False
                for existing_room in rooms_info:
                    # Simple overlap check
                    if not (x + room_width < existing_room.x or 
                           existing_room.x + existing_room.width < x or
                           y + room_height < existing_room.y or 
                           existing_room.y + existing_room.height < y):
                        overlaps = True
                        break
                
                if not overlaps:
                    room_info = RoomInfo(x, y, room_width, room_height, floor)
                    rooms_info.append(room_info)
                    
                    # Create rooms for each cell in the room rectangle
                    for rx in range(room_info.x, room_info.x + room_info.width):
                        for ry in range(room_info.y, room_info.y + room_info.height):
                            room = Room(rx, ry, floor)
                            
                            # Set room type based on position in room
                            if rx == room_info.x or rx == room_info.x + room_info.width - 1 or \
                               ry == room_info.y or ry == room_info.y + room_info.height - 1:
                                room.room_type = "hallway"  # Border cells treated as hallway
                                room.description = "A narrow hallway."
                            else:
                                # Center cells - determine type
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
                            
                            self.rooms[(rx, ry, floor)] = room
            
            # Connect rooms with hallways
            for i in range(len(rooms_info) - 1):
                room1 = rooms_info[i]
                room2 = rooms_info[i + 1]
                
                # Create L-shaped corridor between room centers
                self.create_corridor(room1.center_x, room1.center_y, 
                                   room2.center_x, room2.center_y, floor)
            
            # Ensure the first room connects to the second room for full connectivity
            if len(rooms_info) > 1:
                # Create additional connections to ensure all rooms are reachable
                for i in range(len(rooms_info)):
                    # Connect to a random other room to ensure good connectivity
                    j = random.randint(0, len(rooms_info) - 1)
                    if i != j:
                        self.create_corridor(rooms_info[i].center_x, rooms_info[i].center_y,
                                           rooms_info[j].center_x, rooms_info[j].center_y, floor)
            
            # Place the ultimate artifact on the deepest floor
            if floor == self.floors - 1:  # Last floor (deepest)
                # Find a random room in this floor to place the artifact
                floor_rooms = [(x, y, z) for x, y, z in self.rooms.keys() if z == floor]
                if floor_rooms:
                    artifact_pos = random.choice(floor_rooms)
                    artifact_room = self.rooms[artifact_pos]
                    artifact_room.room_type = "artifact"
                    artifact_room.description = "A mystical chamber glows with ethereal light. At the center lies the legendary Artifact of Power!"
                    artifact_room.items.append(Item("Artifact of Power", ItemType.CONSUMABLE, value=1000, 
                                                  attack_bonus=50, defense_bonus=50, health_bonus=100))

        # Now create connections between adjacent accessible rooms
        for (x, y, floor), room in self.rooms.items():
            for dx, dy, direction in [(0, -1, Direction.NORTH), (0, 1, Direction.SOUTH),
                                      (1, 0, Direction.EAST), (-1, 0, Direction.WEST)]:
                neighbor_pos = (x + dx, y + dy, floor)
                if neighbor_pos in self.rooms:  # Only connect if the neighbor exists
                    room.connect(direction, self.rooms[neighbor_pos])

    def create_corridor(self, x1, y1, x2, y2, floor):
        """Create an L-shaped corridor between two points"""
        # Horizontal first, then vertical
        if random.choice([True, False]):  # Random choice of L-shape orientation
            # Horizontal corridor
            min_x, max_x = min(x1, x2), max(x1, x2)
            for x in range(min_x, max_x + 1):
                pos = (x, y1, floor)
                if pos not in self.rooms:
                    room = Room(x, y1, floor)
                    room.room_type = "hallway"
                    room.description = "A narrow hallway."
                    self.rooms[pos] = room
            
            # Vertical corridor
            min_y, max_y = min(y1, y2), max(y1, y2)
            for y in range(min_y, max_y + 1):
                pos = (x2, y, floor)
                if pos not in self.rooms:
                    room = Room(x2, y, floor)
                    room.room_type = "hallway"
                    room.description = "A narrow hallway."
                    self.rooms[pos] = room
        else:
            # Vertical first, then horizontal
            # Vertical corridor
            min_y, max_y = min(y1, y2), max(y1, y2)
            for y in range(min_y, max_y + 1):
                pos = (x1, y, floor)
                if pos not in self.rooms:
                    room = Room(x1, y, floor)
                    room.room_type = "hallway"
                    room.description = "A narrow hallway."
                    self.rooms[pos] = room
            
            # Horizontal corridor
            min_x, max_x = min(x1, x2), max(x1, x2)
            for x in range(min_x, max_x + 1):
                pos = (x, y2, floor)
                if pos not in self.rooms:
                    room = Room(x, y2, floor)
                    room.room_type = "hallway"
                    room.description = "A narrow hallway."
                    self.rooms[pos] = room

    def get_room(self, x: int, y: int, floor: int) -> Optional[Room]:
        return self.rooms.get((x, y, floor))

    def generate_random_enemy(self, floor: int) -> Enemy:
        # Define enemy tiers based on floor depth
        if floor <= 0:  # Floor 1 (0-indexed)
            # Shallow floors - basic enemies
            enemy_types = [
                ("Goblin", 20, 5, 1, 20, 1, 5),
                ("Skeleton", 30, 7, 2, 30, 2, 6),
                ("Zombie", 25, 6, 1, 25, 1, 4),
                ("Spider", 15, 6, 0, 15, 1, 3),
            ]
        elif floor <= 1:  # Floor 2 (0-indexed)
            # Mid floors - moderate enemies
            enemy_types = [
                ("Goblin", 20, 5, 1, 20, 1, 5),
                ("Orc", 35, 8, 3, 35, 3, 8),
                ("Skeleton", 30, 7, 2, 30, 2, 6),
                ("Zombie", 25, 6, 1, 25, 1, 4),
                ("Ogre", 50, 12, 5, 50, 5, 12),
            ]
        else:  # Floor 3 and deeper (0-indexed)
            # Deep floors - powerful enemies
            enemy_types = [
                ("Orc", 35, 8, 3, 35, 3, 8),
                ("Ogre", 50, 12, 5, 50, 5, 12),
                ("Demon", 75, 15, 8, 75, 8, 18),
                ("Dragon", 120, 20, 12, 120, 12, 25),
                ("Ancient Guardian", 150, 25, 15, 150, 15, 30),
            ]
        
        # Select enemy from appropriate tier
        enemy_data = random.choice(enemy_types)
        
        # Scale stats based on floor with increased difficulty curve
        base_hp, base_attack, base_defense, base_exp, base_gold_min, base_gold_max = enemy_data[1], enemy_data[2], enemy_data[3], enemy_data[4], enemy_data[5], enemy_data[6]
        hp = int(base_hp * (1 + floor * 0.4))  # Increased scaling factor
        attack = int(base_attack * (1 + floor * 0.35))  # Increased scaling factor
        defense = int(base_defense * (1 + floor * 0.35))  # Increased scaling factor
        exp = int(base_exp * (1 + floor * 0.3))
        gold_min = int(base_gold_min * (1 + floor * 0.25))
        gold_max = int(base_gold_max * (1 + floor * 0.25))
        
        return Enemy(enemy_data[0], hp, attack, defense, exp, gold_min, gold_max)

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
        old_position = self.player.position
        self.player.position = (new_room.x, new_room.y, new_room.floor)
        
        # Track exploration
        self.player.floors_explored.add(new_room.floor)
        self.player.rooms_explored.add((new_room.x, new_room.y, new_room.floor))
        self.player.distance_traveled += 1
        
        # Award points for exploration
        # If it's a new room, award exploration points
        if (new_room.x, new_room.y, new_room.floor) not in self.player.rooms_explored or new_room.floor not in self.player.floors_explored:
            exploration_points = 10
            self.player.score += exploration_points
            print(f"You move {direction.value}. (+{exploration_points} exploration points)")
        else:
            print(f"You move {direction.value}.")
        
        # Award bonus points for reaching new floors
        if new_room.floor not in self.player.floors_explored:
            floor_bonus = 50
            self.player.score += floor_bonus
            print(f"You reached a new floor! (+{floor_bonus} floor bonus)")
        
        self.describe_room()
        return True
    
    def describe_room(self):
        """Describe the current room to the player."""
        print(f"\n--- Floor {self.player.position[2]+1}, Room ({self.player.position[0]}, {self.player.position[1]}) ---")
        
        # Generate dynamic room description based on current contents
        living_enemies = [e for e in self.current_room.entities if isinstance(e, Enemy) and e.is_alive()]
        room_items = self.current_room.items
        
        # Generate dynamic description based on contents
        if living_enemies and room_items:
            print("A room with both hostile creatures and treasures!")
        elif living_enemies:
            print("A room with hostile creatures lurks ahead.")
        elif room_items:
            print("A treasure room filled with gleaming objects.")
        elif self.current_room.room_type == "trap":
            print("A dangerous-looking room with potential hazards.")
        else:
            print("An empty, quiet room.")
        
        # Display living enemies
        if living_enemies:
            for entity in living_enemies:
                print(f"A {entity.name} is here!")
        
        # Display items in the room
        if room_items:
            print("Items in the room:")
            for item in room_items:
                print(f"- {item.name}")
        
        # Show adjacent room information
        print("\nAdjacent areas:")
        for direction in Direction:
            if direction in self.current_room.connections:
                adj_room = self.current_room.connections[direction]
                
                # Generate dynamic description for adjacent room based on its contents
                adj_living_enemies = [e for e in adj_room.entities if isinstance(e, Enemy) and e.is_alive()]
                adj_items = adj_room.items
                
                # Determine description based on contents
                if adj_living_enemies and adj_items:
                    adj_desc = "A room with both hostile creatures and treasures!"
                elif adj_living_enemies:
                    adj_desc = "A room with hostile creatures lurks ahead."
                elif adj_items:
                    adj_desc = "A treasure room filled with gleaming objects."
                elif adj_room.room_type == "trap":
                    adj_desc = "A dangerous-looking room with potential hazards."
                else:
                    adj_desc = "An empty, quiet room."
                
                # Count contents for display
                enemy_count = len(adj_living_enemies)
                item_count = len(adj_items)
                
                desc_parts = []
                if enemy_count > 0:
                    desc_parts.append(f"{enemy_count} enemy{'s' if enemy_count != 1 else ''}")
                if item_count > 0:
                    desc_parts.append(f"{item_count} item{'s' if item_count != 1 else ''}")
                if not desc_parts:
                    desc_parts.append("appears empty")
                
                print(f"  {direction.value.capitalize()}: {', '.join(desc_parts)} - {adj_desc}")
            else:
                print(f"  {direction.value.capitalize()}: blocked")
    
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
        print(f"Score: {self.player.score}")
        print(f"Enemies Defeated: {self.player.enemies_defeated}")
        print(f"Treasures Collected: {self.player.treasures_collected}")
        print(f"Floors Explored: {len(self.player.floors_explored)}")
        print(f"Rooms Explored: {len(self.player.rooms_explored)}")
        print(f"Distance Traveled: {self.player.distance_traveled}")
        
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
        # Adjust item_index since the game displays items starting from 1
        adjusted_index = item_index - 1
        
        if 0 <= adjusted_index < len(self.player.inventory):
            item = self.player.inventory[adjusted_index]
            
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
    
    def unequip_item(self, item_type: str) -> bool:
        """Unequip an equipped item and return it to inventory."""
        if item_type.lower() == "weapon":
            if self.player.equipped_weapon:
                # Check if inventory has space
                if len(self.player.inventory) >= 10:
                    print("Your inventory is full! You need to drop something first.")
                    return False
                
                self.player.inventory.append(self.player.equipped_weapon)
                print(f"You unequip the {self.player.equipped_weapon.name}.")
                self.player.equipped_weapon = None
                return True
            else:
                print("You don't have a weapon equipped.")
                return False
        
        elif item_type.lower() == "armor":
            if self.player.equipped_armor:
                # Check if inventory has space
                if len(self.player.inventory) >= 10:
                    print("Your inventory is full! You need to drop something first.")
                    return False
                
                self.player.inventory.append(self.player.equipped_armor)
                print(f"You unequip the {self.player.equipped_armor.name}.")
                self.player.equipped_armor = None
                return True
            else:
                print("You don't have armor equipped.")
                return False
        else:
            print("Invalid item type. Use 'weapon' or 'armor'.")
            return False
    
    def attack_enemy(self, enemy_index: int) -> bool:
        """Attack an enemy in the current room."""
        alive_enemies = [e for e in self.current_room.entities if isinstance(e, Enemy) and e.is_alive()]
        
        if not alive_enemies:
            print("There are no enemies here to attack.")
            return False
        
        # Adjust enemy_index since the game displays enemies starting from 1
        adjusted_index = enemy_index - 1
        
        if 0 <= adjusted_index < len(alive_enemies):
            enemy = alive_enemies[adjusted_index]
            print(f"You attack the {enemy.name}!")
            
            # Player attacks enemy
            damage_dealt = enemy.take_damage(self.player.total_attack)
            print(f"You deal {damage_dealt} damage to the {enemy.name}.")
            
            if not enemy.is_alive():
                print(f"The {enemy.name} is defeated!")
                
                # Update scoring for defeating enemy
                self.player.enemies_defeated += 1
                # Score based on enemy strength
                enemy_score_value = enemy.exp_reward + (enemy.max_health // 2) + (enemy.attack * 2)
                self.player.score += enemy_score_value
                print(f"You earned {enemy_score_value} points for defeating the {enemy.name}!")
                
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
        # Adjust item_index since the game displays items starting from 1
        adjusted_index = item_index - 1
        
        if 0 <= adjusted_index < len(self.current_room.items):
            item = self.current_room.items[adjusted_index]
            
            # Check if this is the artifact (win condition)
            if item.name == "Artifact of Power":
                print(f"\nCongratulations! You have obtained the {item.name}!")
                print("You have completed your quest and emerged victorious!")
                print(f"Final Score: {self.player.score}")
                print(f"Enemies Defeated: {self.player.enemies_defeated}")
                print(f"Treasures Collected: {self.player.treasures_collected}")
                print(f"Floors Explored: {len(self.player.floors_explored)}")
                print(f"Rooms Explored: {len(self.player.rooms_explored)}")
                print(f"Distance Traveled: {self.player.distance_traveled}")
                print("\nThank you for playing Terminal Dungeon Crawler!")
                
                # Exit the game after winning
                exit(0)
            
            # Check if inventory is full
            if len(self.player.inventory) >= 10:
                print("Your inventory is full! You need to drop something first.")
                return False
            
            self.current_room.items.remove(item)
            self.player.inventory.append(item)
            print(f"You take the {item.name}.")
            
            # Update scoring for collecting treasure
            self.player.treasures_collected += 1
            # Score based on item value and bonuses
            item_score_value = item.value + item.attack_bonus * 5 + item.defense_bonus * 5 + item.health_bonus * 2
            self.player.score += item_score_value
            print(f"You earned {item_score_value} points for collecting the {item.name}!")
            
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
        # Prepare dungeon data for saving
        dungeon_data = {}
        for pos, room in self.dungeon.rooms.items():
            # Convert tuple position to string for JSON serialization
            pos_key = f"({pos[0]},{pos[1]},{pos[2]})"
            dungeon_data[pos_key] = {
                "x": room.x,
                "y": room.y,
                "floor": room.floor,
                "room_type": room.room_type,
                "description": room.description,
                "connections": {dir.value: [target_room.x, target_room.y, target_room.floor] 
                               for dir, target_room in room.connections.items()},
                "entities": [],
                "items": []
            }
            
            # Save entities (enemies)
            for entity in room.entities:
                if isinstance(entity, Enemy):
                    dungeon_data[pos_key]["entities"].append({
                        "name": entity.name,
                        "health": entity.health,
                        "max_health": entity.max_health,
                        "attack": entity.attack,
                        "defense": entity.defense,
                        "exp_reward": entity.exp_reward,
                        "gold_min": entity.gold_min,
                        "gold_max": entity.gold_max
                    })
            
            # Save items
            for item in room.items:
                dungeon_data[pos_key]["items"].append({
                    "name": item.name,
                    "type": item.type.value,
                    "value": item.value,
                    "attack_bonus": item.attack_bonus,
                    "defense_bonus": item.defense_bonus,
                    "health_bonus": item.health_bonus
                })
        
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
                "gold": self.player.gold,
                "score": self.player.score,
                "enemies_defeated": self.player.enemies_defeated,
                "treasures_collected": self.player.treasures_collected,
                "floors_explored": list(self.player.floors_explored),
                "rooms_explored": list(self.player.rooms_explored),
                "distance_traveled": self.player.distance_traveled
            },
            "dungeon": {
                "width": self.dungeon.width,
                "height": self.dungeon.height,
                "floors": self.dungeon.floors,
                "rooms": dungeon_data
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(game_state, f, indent=2)
        
        # Quietly saved - don't print message
    
    def load_game(self, filename: str = "savegame.json"):
        """Load a saved game state from a file."""
        try:
            with open(filename, 'r') as f:
                game_state = json.load(f)
            
            # Reconstruct dungeon first
            dungeon_data = game_state["dungeon"]
            # Create a new dungeon without generating rooms initially
            self.dungeon = Dungeon(dungeon_data["width"], dungeon_data["height"], dungeon_data["floors"])
            # Clear the auto-generated rooms and recreate from save
            self.dungeon.rooms = {}
            
            # Recreate rooms from saved data
            temp_rooms = {}  # Temporary storage for rooms
            room_map = {}    # Map from position tuples to rooms
            for pos_str, room_data in dungeon_data["rooms"].items():
                # Convert string key back to tuple
                pos_tuple = tuple(int(x) for x in pos_str.strip('()').split(','))
                x, y, floor = pos_tuple
                
                room = Room(x, y, floor)
                room.room_type = room_data["room_type"]
                room.description = room_data["description"]
                
                # Recreate entities
                for entity_data in room_data["entities"]:
                    enemy = Enemy(
                        name=entity_data["name"],
                        health=entity_data["max_health"],  # Full health when saved
                        attack=entity_data["attack"],
                        defense=entity_data["defense"],
                        exp_reward=entity_data["exp_reward"],
                        gold_min=entity_data["gold_min"],
                        gold_max=entity_data["gold_max"]
                    )
                    # Set current health to saved value
                    enemy.health = entity_data["health"]
                    room.entities.append(enemy)
                
                # Recreate items
                for item_data in room_data["items"]:
                    item = Item(
                        name=item_data["name"],
                        item_type=ItemType(item_data["type"]),
                        value=item_data["value"],
                        attack_bonus=item_data["attack_bonus"],
                        defense_bonus=item_data["defense_bonus"],
                        health_bonus=item_data["health_bonus"]
                    )
                    room.items.append(item)
                
                temp_rooms[pos_str] = room  # Store room directly
                room_map[pos_tuple] = room  # Map for easy lookup later
            
            # Now add all rooms to the dungeon first
            for pos_str, room in temp_rooms.items():
                # Convert string key back to tuple
                pos_tuple = tuple(int(x) for x in pos_str.strip('()').split(','))
                self.dungeon.rooms[pos_tuple] = room
            
            # Now recreate connections after all rooms exist
            for pos_str, room in temp_rooms.items():
                # Create connections
                for direction_str, target_coords in dungeon_data["rooms"][pos_str]["connections"].items():
                    target_pos = tuple(target_coords)  # Convert [x, y, floor] back to tuple
                    target_room = self.dungeon.rooms.get(target_pos)
                    
                    if target_room:
                        direction = Direction(direction_str)
                        room.connect(direction, target_room)
            
            # Reconstruct player first
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
            # Restore score-related properties
            self.player.score = player_data.get("score", 0)
            self.player.enemies_defeated = player_data.get("enemies_defeated", 0)
            self.player.treasures_collected = player_data.get("treasures_collected", 0)
            self.player.floors_explored = set(player_data.get("floors_explored", []))
            self.player.rooms_explored = set(map(tuple, player_data.get("rooms_explored", [])))
            self.player.distance_traveled = player_data.get("distance_traveled", 0)
            
            # Now set current room after dungeon and player are fully reconstructed
            pos = self.player.position
            self.current_room = self.dungeon.get_room(pos[0], pos[1], pos[2])
            
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
            
            # Quietly loaded - don't print message
            return True
        except FileNotFoundError:
            # No save file - this is expected for new games
            return False
        except Exception as e:
            print(f"Error loading game: {e}")
            # Don't reset the game state here since it was already initialized
            # when the GameEngine was created
            return False


def main():
    import sys
    
    # Check if a command was provided as an argument
    args = sys.argv[1:]  # Exclude script name
    
    # Initialize game (try to load if exists, otherwise start new)
    game = GameEngine()
    loaded = game.load_game()  # Attempt to load existing game, returns True if successful
    
    # If no save was found, we have a new game with random dungeon
    # If save was loaded, we have the saved state
    
    if not args:
        # No command provided - show current status and possible actions
        print("=== TERMINAL DUNGEON CRAWLER ===")
        print("Current Status:")
        game.show_stats()
        print()
        game.describe_room()
        print("\nPossible actions:")
        print("  move <direction> - Move north, south, east, or west")
        print("  attack <number> - Attack enemy number in room")
        print("  take <number> - Take item number from room")
        print("  equip <number> - Equip item number from inventory")
        print("  unequip <weapon|armor> - Unequip weapon or armor")
        print("  look - Look around the current room")
        print("  inventory - View your inventory")
        print("  stats - View your character stats")
        print("  rest - Rest to recover health")
        print("  save - Save the game")
        print("  load - Load a saved game")
        print("  quit - Quit the game")
        print("\nExample: python game_engine.py move north")
        print("         python game_engine.py attack 1")
        print("         python game_engine.py take 1")
        print("         python game_engine.py equip 1")
        print("         python game_engine.py unequip armor")
        print("         python game_engine.py stats")
        
        # If this is a new game (no save was loaded), save the initial state quietly
        if not loaded:
            game.save_game()
        
        return
    
    # Process the command from arguments
    command = " ".join(args).strip().lower()
    
    try:
        if command in ["quit", "exit"]:
            game.save_game()
            print("Thanks for playing!")
        elif command == "help":
            print("\nAvailable commands:")
            print("  move <direction> - Move north, south, east, or west")
            print("  attack <number> - Attack enemy number in room")
            print("  take <number> - Take item number from room")
            print("  equip <number> - Equip item number from inventory")
            print("  unequip <weapon|armor> - Unequip weapon or armor")
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
                game.save_game()  # Auto-save after each move (quietly)
            except ValueError:
                print("Invalid direction. Use: north, south, east, or west.")
        elif command.startswith("attack "):
            try:
                enemy_num = int(command[7:])  # Pass the original number (1-based)
                if game.attack_enemy(enemy_num):
                    if game.player.is_alive():
                        game.save_game()  # Auto-save after successful attack (quietly)
                    else:
                        print("\nGame over! You have died.")
                        print("Your save file remains with your last healthy state.")
                else:
                    if not game.player.is_alive():
                        print("\nGame over! You have died.")
                        print("Your save file remains with your last healthy state.")
            except ValueError:
                print("Please specify a valid enemy number to attack.")
        elif command.startswith("take "):
            try:
                item_num = int(command[5:])  # Pass the original number (1-based)
                if game.take_item(item_num):
                    game.save_game()  # Auto-save after taking an item (quietly)
            except ValueError:
                print("Please specify a valid item number to take.")
        elif command.startswith("equip "):
            try:
                item_num = int(command[6:])  # Pass the original number (1-based)
                if game.equip_item(item_num):
                    game.save_game()  # Auto-save after equipping an item (quietly)
            except ValueError:
                print("Please specify a valid item number to equip.")
        elif command.startswith("unequip "):
            item_type = command[8:].lower()
            if item_type in ["weapon", "armor"]:
                if game.unequip_item(item_type):
                    game.save_game()  # Auto-save after unequipping an item (quietly)
            else:
                print("Please specify a valid item type to unequip: 'weapon' or 'armor'.")
        elif command == "look":
            game.look_around()
        elif command == "inventory":
            game.show_inventory()
        elif command == "stats":
            game.show_stats()
        elif command == "rest":
            game.rest()
            game.save_game()  # Auto-save after resting (quietly)
        elif command == "save":
            game.save_game()
            print("Game saved.")
        elif command == "load":
            if game.load_game():
                print("Game loaded.")
            else:
                print("No save file found.")
        else:
            print("Unknown command. Type 'python game_engine.py help' for a list of commands.")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    # If player died, don't save the dead state
    if game.player.is_alive():
        game.save_game()


if __name__ == "__main__":
    main()