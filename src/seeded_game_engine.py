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
    UP = "up"
    DOWN = "down"


class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    KEY = "key"
    TRIGGER = "trigger"


class Entity:
    def __init__(self, name: str, health: int, attack: int, defense: int, speed: int = 10):
        self.name = name
        self.max_health = health
        self.health = health
        self.attack = attack
        self.defense = defense
        self.speed = speed  # For initiative determination

    def take_damage(self, damage: int):
        actual_damage = max(1, damage - self.defense)  # Minimum 1 damage
        self.health -= actual_damage
        return actual_damage

    def apply_status_effects(self):
        """Apply active status effects at the beginning of the turn."""
        if not hasattr(self, 'active_status_effects'):
            self.active_status_effects = {}
        
        effects_to_remove = []
        for effect, duration in self.active_status_effects.items():
            if duration > 0:
                if effect == "burn":
                    # Burn damage is equal to 10% of max health
                    burn_damage = max(1, self.max_health // 10)
                    self.health -= burn_damage
                    print(f"The {self.name} takes {burn_damage} burn damage!")
                elif effect == "poison":
                    # Poison damage is equal to 5% of max health
                    poison_damage = max(1, self.max_health // 20)
                    self.health -= poison_damage
                    print(f"The {self.name} takes {poison_damage} poison damage!")
                
                # Decrease duration
                self.active_status_effects[effect] = duration - 1
            else:
                effects_to_remove.append(effect)
        
        # Remove expired effects
        for effect in effects_to_remove:
            del self.active_status_effects[effect]

    def is_alive(self):
        return self.health > 0


class Item:
    def __init__(self, name: str, item_type: ItemType, value: int = 0, 
                 attack_bonus: int = 0, defense_bonus: int = 0, health_bonus: int = 0,
                 special_effect: str = "", status_effects: dict = None):
        self.name = name
        self.type = item_type
        self.value = value
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.health_bonus = health_bonus
        self.special_effect = special_effect  # For special abilities like "gruff" or "turbo"
        self.status_effects = status_effects or {}  # Dictionary of status effects like {"burn": 3} for 3 turns of burn damage

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
        # Status effects
        self.active_status_effects: dict = {}  # Dictionary of active status effects

    @property
    def total_attack(self):
        bonus = self.equipped_weapon.attack_bonus if self.equipped_weapon else 0
        total = self.attack + bonus
        
        # Apply special weapon effects
        if self.equipped_weapon and self.equipped_weapon.special_effect:
            if "gruff" in self.equipped_weapon.special_effect.lower() or "gruff" in self.equipped_weapon.name.lower():
                total = int(total * 1.2)  # 20% damage boost for gruff weapons
        return total

    @property
    def total_defense(self):
        bonus = self.equipped_armor.defense_bonus if self.equipped_armor else 0
        total = self.defense + bonus
        
        # Apply special armor effects
        if self.equipped_armor and self.equipped_armor.special_effect:
            if "shielding" in self.equipped_armor.special_effect.lower() or "shielding" in self.equipped_armor.name.lower():
                total = int(total * 1.15)  # 15% defense boost for shielding armor
        return total

    @property
    def total_max_health(self):
        bonus = (self.equipped_armor.health_bonus if self.equipped_armor else 0) + \
                sum(item.health_bonus for item in self.inventory if item != self.equipped_armor)
        return self.max_health + bonus

    @property
    def total_speed(self):
        """Calculate total speed including equipped item effects."""
        total = self.speed
        
        # Apply special item effects that affect speed
        if self.equipped_weapon and self.equipped_weapon.special_effect:
            if "turbo" in self.equipped_weapon.special_effect.lower() or "turbo" in self.equipped_weapon.name.lower():
                total += 5  # Turbo weapons increase initiative
        if self.equipped_armor and self.equipped_armor.special_effect:
            if "light" in self.equipped_armor.special_effect.lower() or "light" in self.equipped_armor.name.lower():
                total += 3  # Light armor increases speed
        return total

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
                 exp_reward: int, gold_min: int, gold_max: int, speed: int = 10,
                 status_effects_on_hit: dict = None):
        super().__init__(name, health, attack, defense, speed)
        self.exp_reward = exp_reward
        self.gold_min = gold_min
        self.gold_max = gold_max
        self.status_effects_on_hit = status_effects_on_hit or {}  # Status effects applied when this enemy hits player

    def generate_loot(self) -> List[Item]:
        # Basic loot generation
        loot = []
        if random.random() < 0.3:  # 30% chance to drop gold
            gold_amount = random.randint(self.gold_min, self.gold_max)
            loot.append(Item(f"{gold_amount} Gold", ItemType.CONSUMABLE, value=gold_amount))
        
        # Chance to drop special quest items based on enemy type
        if random.random() < 0.1:  # 10% chance to drop a quest trophy
            trophy_name = f"{self.name} Trophy"
            trophy = Item(trophy_name, ItemType.CONSUMABLE, value=50)
            loot.append(trophy)
        
        return loot


class NonPlayerCharacter(Entity):
    def __init__(self, name: str, health: int = 1, dialogue: str = "", quest: dict = None):
        super().__init__(name, health, attack=0, defense=0, speed=0)
        self.dialogue = dialogue
        self.quest = quest or {}  # Quest format: {"target_item": "item_name", "reward": Item, "description": "quest_text"}
        self.has_given_quest = False
        self.has_completed_quest = False


class RoomState:
    """Represents the mutable state of a room that can change during gameplay"""
    def __init__(self, position: Tuple[int, int, int]):
        self.position = position
        self.items: List[Item] = []
        self.entities: List[Enemy] = []  # Only enemies that can be defeated
        self.npcs: List[NonPlayerCharacter] = []
        self.visited = False  # Whether the player has visited this room
        # State of doors and passages
        self.unlocked_doors: set = set()
        self.activated_passages: set = set()
        # Whether the room's contents have been modified from the original generation
        self.modified_from_original = False
        # Room attributes that may be set during generation
        self.room_type = "generic"
        self.description = "A standard dungeon room."
        self.has_stairs_down = False
        self.has_stairs_up = False
        self.stairs_down_target = None  # Target room when going down
        self.stairs_up_target = None    # Target room when going up
        # For locked doors and blocked passages
        self.locked_doors: Dict[Direction, str] = {}  # Direction -> key name needed
        self.blocked_passages: Dict[Direction, str] = {}  # Direction -> trigger item needed
        # Connections to other rooms
        self.connections: Dict[Direction, Tuple[int, int, int]] = {}  # Direction -> (x, y, floor)


class SeededDungeon:
    def __init__(self, width: int = 30, height: int = 30, floors: int = 3, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.floors = floors
        self.seed = seed or random.randint(0, 1000000)
        self.room_states: Dict[Tuple[int, int, int], RoomState] = {}
        
        # Generate the base dungeon structure based on the seed
        self._generate_base_structure()
    
    def _generate_base_structure(self):
        """Generate the base dungeon structure based on the seed"""
        # Set the random seed to ensure reproducible generation
        random.seed(self.seed)
        
        # Store room layouts for generation
        room_layouts = {}
        
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
                    room_info = self.RoomInfo(x, y, room_width, room_height, floor)
                    rooms_info.append(room_info)
                    
                    # Create rooms for each cell in the room rectangle
                    for rx in range(room_info.x, room_info.x + room_info.width):
                        for ry in range(room_info.y, room_info.y + room_info.height):
                            # Create the base room state
                            pos = (rx, ry, floor)
                            room_state = RoomState(pos)
                            
                            # Set room type based on position in room
                            if rx == room_info.x or rx == room_info.x + room_info.width - 1 or \
                               ry == room_info.y or ry == room_info.y + room_info.height - 1:
                                room_state.room_type = "hallway"  # Border cells treated as hallway
                                room_state.description = "A narrow hallway."
                            else:
                                # Center cells - determine type
                                rand = random.random()
                                if rand < 0.1:
                                    room_state.room_type = "treasure"
                                    room_state.description = "A treasure room filled with gleaming objects."
                                    # Add some treasure
                                    if random.random() < 0.7:
                                        room_state.items.append(self._generate_random_item())
                                elif rand < 0.3:
                                    room_state.room_type = "monster"
                                    room_state.description = "A room with hostile creatures lurks ahead."
                                    # Add an enemy
                                    room_state.entities.append(self._generate_random_enemy(floor))
                                elif rand < 0.4:
                                    room_state.room_type = "trap"
                                    room_state.description = "A dangerous-looking room with potential hazards."
                                elif rand < 0.45:  # 5% chance for NPC with quest
                                    room_state.room_type = "npc"
                                    room_state.description = "A room with a mysterious stranger."
                                    
                                    # Create an NPC with a quest
                                    npc_dialogues = [
                                        "Greetings, traveler. I seek a powerful item that was lost in these depths.",
                                        "Hello adventurer, I have a task for you if you're brave enough.",
                                        "Welcome, hero. I need someone to retrieve something precious to me.",
                                        "Oh, a visitor! Perhaps you can assist me with a small matter."
                                    ]
                                    
                                    # Choose a boss monster whose drop is the quest target
                                    boss_monsters = ["Orc", "Ogre", "Demon", "Dragon", "Ancient Guardian"]
                                    target_monster = random.choice(boss_monsters)
                                    target_item = f"{target_monster} Trophy"
                                    
                                    # Create a reward
                                    reward_types = [
                                        Item("Flame Sword", ItemType.WEAPON, value=100, attack_bonus=15, defense_bonus=2, status_effects={"burn": 3}),
                                        Item("Frost Helm", ItemType.ARMOR, value=80, attack_bonus=3, defense_bonus=10, health_bonus=20, status_effects={"chill": 2}),
                                        Item("Lightning Blade", ItemType.WEAPON, value=120, attack_bonus=20, defense_bonus=0, status_effects={"shock": 2}),
                                        Item("Healing Amulet", ItemType.ARMOR, value=60, attack_bonus=5, defense_bonus=5, health_bonus=50),
                                        Item("Thunder Hammer", ItemType.WEAPON, value=150, attack_bonus=25, defense_bonus=3, status_effects={"stun": 2})
                                    ]
                                    reward = random.choice(reward_types)
                                    
                                    quest_description = f"I need you to defeat a {target_monster} and bring me its trophy. In return, I'll give you this {reward.name}."
                                    
                                    npc = NonPlayerCharacter(
                                        name="Wandering Sage",
                                        health=1,
                                        dialogue=random.choice(npc_dialogues),
                                        quest={
                                            "target_item": target_item,
                                            "reward": reward,
                                            "description": quest_description
                                        }
                                    )
                                    room_state.npcs.append(npc)
                                else:
                                    room_state.room_type = "empty"
                                    room_state.description = "An empty, quiet room."
                            
                            self.room_states[pos] = room_state
            
            # Connect rooms with hallways
            for i in range(len(rooms_info) - 1):
                room1 = rooms_info[i]
                room2 = rooms_info[i + 1]
                
                # Create L-shaped corridor between room centers
                self._create_corridor(room1.center_x, room1.center_y, 
                                   room2.center_x, room2.center_y, floor)
            
            # Ensure the first room connects to the second room for full connectivity
            if len(rooms_info) > 1:
                # Create additional connections to ensure all rooms are reachable
                for i in range(len(rooms_info)):
                    # Connect to a random other room to ensure good connectivity
                    j = random.randint(0, len(rooms_info) - 1)
                    if i != j:
                        self._create_corridor(rooms_info[i].center_x, rooms_info[i].center_y,
                                           rooms_info[j].center_x, rooms_info[j].center_y, floor)
            
            # Place the ultimate artifact on the deepest floor
            if floor == self.floors - 1:  # Last floor (deepest)
                # Find a random room in this floor to place the artifact
                floor_rooms = [(x, y, z) for x, y, z in self.room_states.keys() if z == floor]
                if floor_rooms:
                    artifact_pos = random.choice(floor_rooms)
                    artifact_room = self.room_states[artifact_pos]
                    artifact_room.room_type = "artifact"
                    artifact_room.description = "A mystical chamber glows with ethereal light. At the center lies the legendary Artifact of Power!"
                    artifact_room.items.append(Item("Artifact of Power", ItemType.CONSUMABLE, value=1000, 
                                                  attack_bonus=50, defense_bonus=50, health_bonus=100))

        # Now create connections between adjacent accessible rooms
        for (x, y, floor), room_state in self.room_states.items():
            for dx, dy, direction in [(0, -1, Direction.NORTH), (0, 1, Direction.SOUTH),
                                      (1, 0, Direction.EAST), (-1, 0, Direction.WEST)]:
                neighbor_pos = (x + dx, y + dy, floor)
                if neighbor_pos in self.room_states:  # Only connect if the neighbor exists
                    if not hasattr(room_state, 'connections'):
                        room_state.connections = {}
                    room_state.connections[direction] = neighbor_pos
        
        # Add stairs between floors (using special room flags)
        # Ensure at least one staircase exists between each pair of floors
        for floor in range(self.floors - 1):  # Connect each floor to the one below it
            # Find a room on the current floor that is accessible (has connections)
            current_floor_rooms_with_connections = []
            next_floor_rooms_with_connections = []
            
            for pos, room_state in self.room_states.items():
                if pos[2] == floor and len(room_state.connections) > 0:  # Room is on current floor and has connections
                    current_floor_rooms_with_connections.append(pos)
            
            for pos, room_state in self.room_states.items():
                if pos[2] == floor + 1 and len(room_state.connections) > 0:  # Room is on next floor and has connections
                    next_floor_rooms_with_connections.append(pos)
            
            if current_floor_rooms_with_connections and next_floor_rooms_with_connections:
                # Pick a connected room from each floor to place stairs
                # Make sure to include rooms that might be accessible from start
                current_room_pos = current_floor_rooms_with_connections[0]  # Use first accessible room
                next_room_pos = next_floor_rooms_with_connections[0]  # Use first accessible room on next floor
                
                current_room_state = self.room_states[current_room_pos]
                next_room_state = self.room_states[next_room_pos]
                
                # Mark rooms as having stairs and set targets
                current_room_state.has_stairs_down = True
                current_room_state.stairs_down_target = next_room_pos  # Going down leads to next floor room
                next_room_state.has_stairs_up = True
                next_room_state.stairs_up_target = current_room_pos   # Going up leads back to current floor room
                
                # Add visual indicators that these are stair locations
                current_room_state.description = "A room with stairs leading down to the next level."
                next_room_state.description = "A room with stairs leading up from the level below."

        # Add locked doors and blocked passages for puzzle elements
        all_accessible_rooms = [room_state for room_state in self.room_states.values() if len(room_state.connections) > 0]
        
        # Add some locked doors (about 10% of accessible rooms)
        num_locked_doors = max(1, len(all_accessible_rooms) // 10)
        selected_rooms_for_doors = random.sample(all_accessible_rooms, min(num_locked_doors, len(all_accessible_rooms)))
        
        # Keep track of placed keys to ensure accessibility
        placed_keys = set()
        
        for room_state in selected_rooms_for_doors:
            # Find a direction that has a connection but isn't stairs
            available_directions = []
            for direction, connected_pos in room_state.connections.items():
                # Don't lock stair directions
                if not ((direction == Direction.UP and room_state.has_stairs_up) or 
                       (direction == Direction.DOWN and room_state.has_stairs_down)):
                    available_directions.append(direction)
            
            if available_directions:
                direction_to_lock = random.choice(available_directions)
                # Add locked door - require a specific key type
                key_types = ["Iron Key", "Silver Key", "Golden Key", "Ancient Key", "Crystal Key"]
                key_required = random.choice(key_types)
                room_state.locked_doors[direction_to_lock] = key_required
                
                # Add the corresponding key to some other room in the dungeon
                # Find a random room that's not the same room
                other_rooms = [r for r in all_accessible_rooms if r != room_state]
                if other_rooms:
                    key_room = random.choice(other_rooms)
                    key_item = Item(name=key_required, item_type=ItemType.KEY, value=10)
                    key_room.items.append(key_item)
                    placed_keys.add(key_required)

        # Add some blocked passages (about 5% of accessible rooms)
        num_blocked_passages = max(1, len(all_accessible_rooms) // 20)
        # Select from remaining rooms that don't already have locked doors
        remaining_rooms = [room_state for room_state in selected_rooms_for_doors if len(room_state.locked_doors) == 0]
        if len(remaining_rooms) < num_blocked_passages:
            # Add more rooms if needed
            additional_rooms = [room_state for room_state in all_accessible_rooms if room_state not in selected_rooms_for_doors]
            num_additional_needed = num_blocked_passages - len(remaining_rooms)
            if num_additional_needed > 0 and len(additional_rooms) > 0:
                num_to_select = min(num_additional_needed, len(additional_rooms))
                additional_selected = random.sample(additional_rooms, num_to_select)
                remaining_rooms.extend(additional_selected)
        
        selected_rooms_for_passages = random.sample(remaining_rooms, min(num_blocked_passages, len(remaining_rooms)))
        
        # Keep track of placed trigger items
        placed_triggers = set()
        
        for room_state in selected_rooms_for_passages:
            # Find a direction that has a connection
            available_directions = [d for d in room_state.connections.keys() 
                                  if not ((d == Direction.UP and room_state.has_stairs_up) or 
                                         (d == Direction.DOWN and room_state.has_stairs_down))]
            
            if available_directions:
                direction_to_block = random.choice(available_directions)
                # Add blocked passage - require a specific trigger item
                trigger_types = ["Rune", "Powder", "Crystal", "Stone", "Charm", "Sundial", "Sunday"]
                trigger_required = random.choice(trigger_types)
                if trigger_required == "Sunday":
                    # Special case for Sunday
                    trigger_name = "Sunday"
                else:
                    trigger_name = f"Power {trigger_required}"
                room_state.blocked_passages[direction_to_block] = trigger_name
                
                # Add the corresponding trigger item to some other room in the dungeon
                other_rooms = [r for r in all_accessible_rooms if r != room_state]
                if other_rooms:
                    trigger_room = random.choice(other_rooms)
                    # For "Sunday", use a special trigger item; others use TRIGGER type
                    if trigger_required == "Sunday":
                        trigger_item = Item(name=trigger_name, item_type=ItemType.TRIGGER, value=5)
                    else:
                        trigger_item = Item(name=trigger_name, item_type=ItemType.TRIGGER, value=5)
                    trigger_room.items.append(trigger_item)
                    placed_triggers.add(trigger_name)

    def _create_corridor(self, x1, y1, x2, y2, floor):
        """Create an L-shaped corridor between two points"""
        # Horizontal first, then vertical
        if random.choice([True, False]):  # Random choice of L-shape orientation
            # Horizontal corridor
            min_x, max_x = min(x1, x2), max(x1, x2)
            for x in range(min_x, max_x + 1):
                pos = (x, y1, floor)
                if pos not in self.room_states:
                    room_state = RoomState(pos)
                    room_state.room_type = "hallway"
                    room_state.description = "A narrow hallway."
                    self.room_states[pos] = room_state
            
            # Vertical corridor
            min_y, max_y = min(y1, y2), max(y1, y2)
            for y in range(min_y, max_y + 1):
                pos = (x2, y, floor)
                if pos not in self.room_states:
                    room_state = RoomState(pos)
                    room_state.room_type = "hallway"
                    room_state.description = "A narrow hallway."
                    self.room_states[pos] = room_state
        else:
            # Vertical first, then horizontal
            # Vertical corridor
            min_y, max_y = min(y1, y2), max(y1, y2)
            for y in range(min_y, max_y + 1):
                pos = (x1, y, floor)
                if pos not in self.room_states:
                    room_state = RoomState(pos)
                    room_state.room_type = "hallway"
                    room_state.description = "A narrow hallway."
                    self.room_states[pos] = room_state
            
            # Horizontal corridor
            min_x, max_x = min(x1, x2), max(x1, x2)
            for x in range(min_x, max_x + 1):
                pos = (x, y2, floor)
                if pos not in self.room_states:
                    room_state = RoomState(pos)
                    room_state.room_type = "hallway"
                    room_state.description = "A narrow hallway."
                    self.room_states[pos] = room_state

    def get_room_state(self, x: int, y: int, floor: int) -> Optional[RoomState]:
        return self.room_states.get((x, y, floor))

    def _generate_random_enemy(self, floor: int) -> Enemy:
        # Define enemy tiers based on floor depth
        if floor <= 0:  # Floor 1 (0-indexed)
            # Shallow floors - basic enemies
            enemy_types = [
                ("Goblin", 20, 5, 1, 20, 1, 5, 12),  # Fast goblins
                ("Skeleton", 30, 7, 2, 30, 2, 6, 10), # Average speed skeletons
                ("Zombie", 25, 6, 1, 25, 1, 4, 6),   # Slow zombies
                ("Spider", 15, 6, 0, 15, 1, 3, 14),   # Fast spiders
            ]
        elif floor <= 1:  # Floor 2 (0-indexed)
            # Mid floors - moderate enemies
            enemy_types = [
                ("Goblin", 20, 5, 1, 20, 1, 5, 12),  # Fast goblins
                ("Orc", 35, 8, 3, 35, 3, 8, 8),     # Slower orcs
                ("Skeleton", 30, 7, 2, 30, 2, 6, 10), # Average speed skeletons
                ("Zombie", 25, 6, 1, 25, 1, 4, 6),   # Slow zombies
                ("Ogre", 50, 12, 5, 50, 5, 12, 7),   # Slow but strong ogres
            ]
        else:  # Floor 3 and deeper (0-indexed)
            # Deep floors - powerful enemies
            enemy_types = [
                ("Orc", 35, 8, 3, 35, 3, 8, 8),
                ("Ogre", 50, 12, 5, 50, 5, 12, 7),
                ("Demon", 75, 15, 8, 75, 8, 18, 11),  # Fast demons
                ("Dragon", 120, 20, 12, 120, 12, 25, 9), # Powerful but slower dragons
                ("Ancient Guardian", 150, 25, 15, 150, 15, 30, 5), # Very slow but powerful guardians
            ]
        
        # Select enemy from appropriate tier
        enemy_data = random.choice(enemy_types)
        
        # Scale stats based on floor with increased difficulty curve
        base_hp, base_attack, base_defense, base_exp, base_gold_min, base_gold_max, base_speed = enemy_data[1], enemy_data[2], enemy_data[3], enemy_data[4], enemy_data[5], enemy_data[6], enemy_data[7] if len(enemy_data) > 7 else 10
        hp = int(base_hp * (1 + floor * 0.4))  # Increased scaling factor
        attack = int(base_attack * (1 + floor * 0.35))  # Increased scaling factor
        defense = int(base_defense * (1 + floor * 0.35))  # Increased scaling factor
        exp = int(base_exp * (1 + floor * 0.3))
        gold_min = int(base_gold_min * (1 + floor * 0.25))
        gold_max = int(base_gold_max * (1 + floor * 0.25))
        speed = int(base_speed * (1 + floor * 0.2))  # Speed also scales with floor
        
        # Add status effects on hit for some enemies (15% chance)
        status_effects_on_hit = {}
        if random.random() < 0.15:
            effect_type = random.choice(["burn", "poison", "chill"])
            status_effects_on_hit[effect_type] = random.randint(2, 3)  # 2-3 turns of effect
        
        return Enemy(enemy_data[0], hp, attack, defense, exp, gold_min, gold_max, speed, status_effects_on_hit)

    def _generate_random_item(self) -> Item:
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
        
        # Randomly select an item type
        item_data = random.choice(item_types)
        
        # Add special effects randomly
        name, item_type, value, attack_bonus, defense_bonus, health_bonus = item_data
        
        # Add special effects based on item name
        special_effect = ""
        if "Gruff" in name or "gruff" in name:
            special_effect = "gruff"  # Increases damage
        elif "Turbo" in name or "turbo" in name:
            special_effect = "turbo"  # Increases initiative
        elif "Light" in name or "light" in name:
            special_effect = "light"  # Increases speed
        elif "Shielding" in name or "shielding" in name:
            special_effect = "shielding"  # Increases defense
        
        # Add status effects randomly
        status_effects = {}
        # 5% chance for items to have status effects
        if random.random() < 0.05 and item_type in [ItemType.WEAPON, ItemType.ARMOR]:
            status_effect_type = random.choice(["burn", "poison", "chill", "shock", "stun"])
            status_effects[status_effect_type] = random.randint(2, 4)  # Duration of 2-4 turns
        
        return Item(name, item_type, value, attack_bonus, defense_bonus, health_bonus, special_effect, status_effects)

    class RoomInfo:
        def __init__(self, x, y, width, height, floor):
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.floor = floor
            self.center_x = x + width // 2
            self.center_y = y + height // 2


class SeededGameEngine:
    def __init__(self, seed: Optional[int] = None):
        self.player = Player()
        self.dungeon = SeededDungeon(seed=seed)
        self.current_room_state = self.dungeon.get_room_state(0, 0, 0)  # Try to start at entrance
        
        # If the starting position doesn't exist or has stairs down, find a suitable starting room
        if not self.current_room_state or getattr(self.current_room_state, 'has_stairs_down', False):
            # Find a room without stairs down to start in
            for pos, room_state in self.dungeon.room_states.items():
                if not getattr(room_state, 'has_stairs_down', False):
                    self.current_room_state = room_state
                    self.player.position = pos
                    break
            else:
                # If no room without stairs is found, just use the first available
                for pos, room_state in self.dungeon.room_states.items():
                    self.current_room_state = room_state
                    self.player.position = pos
                    break
        
        # High score tracking
        self.high_score = 0
        self.load_high_score()
    
    def get_current_room(self):
        """Get the full room representation with current state"""
        # We need to reconstruct the full room from the base dungeon and current state
        # For now, just return the room state as is
        return self.current_room_state
    
    def move_player(self, direction: Direction) -> bool:
        """Attempt to move the player in the given direction."""
        # Handle stair movement specially
        if direction == Direction.DOWN:
            if not getattr(self.current_room_state, 'has_stairs_down', False):
                # Check regular connections
                if hasattr(self.current_room_state, 'connections') and direction in self.current_room_state.connections:
                    new_pos = self.current_room_state.connections[direction]
                    new_room_state = self.dungeon.room_states[new_pos]
                else:
                    print("You cannot go that way.")
                    return False
            elif not getattr(self.current_room_state, 'stairs_down_target', None):
                # Check regular connections
                if hasattr(self.current_room_state, 'connections') and direction in self.current_room_state.connections:
                    new_pos = self.current_room_state.connections[direction]
                    new_room_state = self.dungeon.room_states[new_pos]
                else:
                    print("You cannot go that way.")
                    return False
            else:
                new_pos = self.current_room_state.stairs_down_target
                new_room_state = self.dungeon.room_states[new_pos]
        elif direction == Direction.UP:
            if not getattr(self.current_room_state, 'has_stairs_up', False):
                # Check regular connections
                if hasattr(self.current_room_state, 'connections') and direction in self.current_room_state.connections:
                    new_pos = self.current_room_state.connections[direction]
                    new_room_state = self.dungeon.room_states[new_pos]
                else:
                    print("You cannot go that way.")
                    return False
            elif not getattr(self.current_room_state, 'stairs_up_target', None):
                # Check regular connections
                if hasattr(self.current_room_state, 'connections') and direction in self.current_room_state.connections:
                    new_pos = self.current_room_state.connections[direction]
                    new_room_state = self.dungeon.room_states[new_pos]
                else:
                    print("You cannot go that way.")
                    return False
            else:
                new_pos = self.current_room_state.stairs_up_target
                new_room_state = self.dungeon.room_states[new_pos]
        elif hasattr(self.current_room_state, 'connections') and direction in self.current_room_state.connections:
            new_pos = self.current_room_state.connections[direction]
            new_room_state = self.dungeon.room_states[new_pos]
        else:
            print("You cannot go that way.")
            return False
        
        self.current_room_state = new_room_state
        old_position = self.player.position
        self.player.position = (new_room_state.position[0], new_room_state.position[1], new_room_state.position[2])
        
        # Track exploration
        self.player.floors_explored.add(new_room_state.position[2])
        self.player.rooms_explored.add(new_room_state.position)
        self.player.distance_traveled += 1
        
        # Award points for exploration
        # If it's a new room, award exploration points
        if new_room_state.position not in self.player.rooms_explored or new_room_state.position[2] not in self.player.floors_explored:
            exploration_points = 10
            self.player.score += exploration_points
            print(f"You move {direction.value}. (+{exploration_points} exploration points)")
        else:
            print(f"You move {direction.value}.")
        
        # Award bonus points for reaching new floors
        if new_room_state.position[2] not in self.player.floors_explored:
            floor_bonus = 50
            self.player.score += floor_bonus
            print(f"You reached a new floor! (+{floor_bonus} floor bonus)")
        
        self.describe_room()
        return True
    
    def describe_room(self):
        """Describe the current room to the player."""
        print(f"\n--- Floor {self.player.position[2]+1}, Room ({self.player.position[0]}, {self.player.position[1]}) ---")
        
        # Generate dynamic room description based on current contents
        living_enemies = [e for e in self.current_room_state.entities if e.is_alive()]
        room_items = self.current_room_state.items
        
        # Generate dynamic description based on contents
        if living_enemies and room_items:
            print("A room with both hostile creatures and treasures!")
        elif living_enemies:
            print("A room with hostile creatures lurks ahead.")
        elif room_items:
            print("A treasure room filled with gleaming objects.")
        elif getattr(self.current_room_state, 'room_type', '') == "trap":
            print("A dangerous-looking room with potential hazards.")
        else:
            print("An empty, quiet room.")
        
        # Display living enemies
        if living_enemies:
            for entity in living_enemies:
                print(f"A {entity.name} is here!")
        
        # Display NPCs in the room
        if self.current_room_state.npcs:
            for npc in self.current_room_state.npcs:
                print(f"{npc.name} is here!")
        
        # Display items in the room
        if room_items:
            print("Items in the room:")
            for item in room_items:
                print(f"- {item.name}")
        
        # Show adjacent room information
        print("\nAdjacent areas:")
        for direction in Direction:
            # Check if this is a stair direction
            if direction == Direction.DOWN and getattr(self.current_room_state, 'has_stairs_down', False) and getattr(self.current_room_state, 'stairs_down_target', None):
                print(f"  {direction.value.capitalize()}: stairs down to next floor - Stairs to lower level")
            elif direction == Direction.UP and getattr(self.current_room_state, 'has_stairs_up', False) and getattr(self.current_room_state, 'stairs_up_target', None):
                print(f"  {direction.value.capitalize()}: stairs up to previous floor - Stairs to upper level")
            elif hasattr(self.current_room_state, 'connections') and direction in self.current_room_state.connections:
                adj_pos = self.current_room_state.connections[direction]
                adj_room_state = self.dungeon.room_states[adj_pos]
                
                # Generate dynamic description for adjacent room based on its contents
                adj_living_enemies = [e for e in adj_room_state.entities if e.is_alive()]
                adj_items = adj_room_state.items
                
                # Determine description based on contents
                if adj_living_enemies and adj_items:
                    adj_desc = "A room with both hostile creatures and treasures!"
                elif adj_living_enemies:
                    adj_desc = "A room with hostile creatures lurks ahead."
                elif adj_items:
                    adj_desc = "A treasure room filled with gleaming objects."
                elif getattr(adj_room_state, 'room_type', '') == "trap":
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
        alive_enemies = [e for e in self.current_room_state.entities if e.is_alive()]
        
        if not alive_enemies:
            print("There are no enemies here to attack.")
            return False
        
        # Adjust enemy_index since the game displays enemies starting from 1
        adjusted_index = enemy_index - 1
        
        if 0 <= adjusted_index < len(alive_enemies):
            enemy = alive_enemies[adjusted_index]
            print(f"You attack the {enemy.name}!")
            
            # Apply status effects before combat
            # Apply player's status effects
            self.player.apply_status_effects()
            if not self.player.is_alive():
                print("You have been defeated by status effects! Game over.")
                return False
            
            # Apply enemy's status effects
            enemy.apply_status_effects()
            if not enemy.is_alive():
                print(f"The {enemy.name} is defeated by status effects!")
                
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
                    self.current_room_state.items.append(item)
                
                # Mark room as modified since enemy was defeated
                self.current_room_state.modified_from_original = True
                
                return True
            
            # Determine initiative based on speed (with special effects)
            player_speed = self.player.total_speed
            enemy_speed = enemy.speed
            
            # Calculate who attacks first based on speed
            if player_speed > enemy_speed:
                # Player goes first
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
                        self.current_room_state.items.append(item)
                    
                    # Mark room as modified since enemy was defeated
                    self.current_room_state.modified_from_original = True
                    
                    return True
                else:
                    # Enemy counterattacks
                    damage_taken = self.player.take_damage(enemy.attack)
                    print(f"The {enemy.name} hits you for {damage_taken} damage!")
                    
                    # Apply any status effects from enemy on hit
                    if hasattr(enemy, 'status_effects_on_hit') and enemy.status_effects_on_hit:
                        for effect, duration in enemy.status_effects_on_hit.items():
                            if effect == "burn":
                                print(f"The {enemy.name} burns you!")
                                self.player.active_status_effects['burn'] = duration
                            elif effect == "poison":
                                print(f"The {enemy.name} poisons you!")
                                self.player.active_status_effects['poison'] = duration
                    
                    if not self.player.is_alive():
                        print("You have been defeated! Game over.")
                        return False
                    
                    return True
            elif enemy_speed > player_speed:
                # Enemy goes first (speed advantage)
                damage_taken = self.player.take_damage(enemy.attack)
                print(f"The {enemy.name} strikes first, hitting you for {damage_taken} damage!")
                
                if not self.player.is_alive():
                    print("You have been defeated! Game over.")
                    return False
                
                # Player gets to attack back if still alive
                damage_dealt = enemy.take_damage(self.player.total_attack)
                print(f"You counterattack and deal {damage_dealt} damage to the {enemy.name}.")
                
                # Apply any status effects from player's weapon
                if self.player.equipped_weapon and self.player.equipped_weapon.status_effects:
                    for effect, duration in self.player.equipped_weapon.status_effects.items():
                        if effect == "burn":
                            print(f"The {self.player.equipped_weapon.name} burns the {enemy.name}!")
                            # Add burn effect to enemy for next turn
                            if not hasattr(enemy, 'active_status_effects'):
                                enemy.active_status_effects = {}
                            enemy.active_status_effects['burn'] = duration
                        elif effect == "poison":
                            print(f"The {self.player.equipped_weapon.name} poisons the {enemy.name}!")
                            if not hasattr(enemy, 'active_status_effects'):
                                enemy.active_status_effects = {}
                            enemy.active_status_effects['poison'] = duration
                
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
                        self.current_room_state.items.append(item)
                    
                    # Mark room as modified since enemy was defeated
                    self.current_room_state.modified_from_original = True
                    
                    return True
                else:
                    return True
            else:
                # Equal speeds - random initiative
                if random.choice([True, False]):
                    # Player goes first
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
                            self.current_room_state.items.append(item)
                        
                        # Mark room as modified since enemy was defeated
                        self.current_room_state.modified_from_original = True
                        
                        return True
                    else:
                        # Enemy counterattacks
                        damage_taken = self.player.take_damage(enemy.attack)
                        print(f"The {enemy.name} hits you for {damage_taken} damage!")
                        
                        # Apply any status effects from enemy on hit
                        if hasattr(enemy, 'status_effects_on_hit') and enemy.status_effects_on_hit:
                            for effect, duration in enemy.status_effects_on_hit.items():
                                if effect == "burn":
                                    print(f"The {enemy.name} burns you!")
                                    self.player.active_status_effects['burn'] = duration
                                elif effect == "poison":
                                    print(f"The {enemy.name} poisons you!")
                                    self.player.active_status_effects['poison'] = duration
                        
                        if not self.player.is_alive():
                            print("You have been defeated! Game over.")
                            return False
                        
                        return True
                else:
                    # Enemy goes first
                    damage_taken = self.player.take_damage(enemy.attack)
                    print(f"The {enemy.name} strikes first, hitting you for {damage_taken} damage!")
                    
                    # Apply any status effects from enemy on hit
                    if hasattr(enemy, 'status_effects_on_hit') and enemy.status_effects_on_hit:
                        for effect, duration in enemy.status_effects_on_hit.items():
                            if effect == "burn":
                                print(f"The {enemy.name} burns you!")
                                self.player.active_status_effects['burn'] = duration
                            elif effect == "poison":
                                print(f"The {enemy.name} poisons you!")
                                self.player.active_status_effects['poison'] = duration
                    
                    if not self.player.is_alive():
                        print("You have been defeated! Game over.")
                        return False
                    
                    # Player gets to attack back if still alive
                    damage_dealt = enemy.take_damage(self.player.total_attack)
                    print(f"You counterattack and deal {damage_dealt} damage to the {enemy.name}.")
                    
                    # Apply any status effects from player's weapon
                    if self.player.equipped_weapon and self.player.equipped_weapon.status_effects:
                        for effect, duration in self.player.equipped_weapon.status_effects.items():
                            if effect == "burn":
                                print(f"The {self.player.equipped_weapon.name} burns the {enemy.name}!")
                                # Add burn effect to enemy for next turn
                                if not hasattr(enemy, 'active_status_effects'):
                                    enemy.active_status_effects = {}
                                enemy.active_status_effects['burn'] = duration
                            elif effect == "poison":
                                print(f"The {self.player.equipped_weapon.name} poisons the {enemy.name}!")
                                if not hasattr(enemy, 'active_status_effects'):
                                    enemy.active_status_effects = {}
                                enemy.active_status_effects['poison'] = duration
                    
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
                            self.current_room_state.items.append(item)
                        
                        # Mark room as modified since enemy was defeated
                        self.current_room_state.modified_from_original = True
                        
                        return True
                    else:
                        return True
        else:
            print("Invalid enemy selection.")
            return False
    
    def take_item(self, item_index: int) -> bool:
        """Take an item from the current room."""
        # Adjust item_index since the game displays items starting from 1
        adjusted_index = item_index - 1
        
        if 0 <= adjusted_index < len(self.current_room_state.items):
            item = self.current_room_state.items[adjusted_index]
            
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
            
            self.current_room_state.items.remove(item)
            self.player.inventory.append(item)
            print(f"You take the {item.name}.")
            
            # Update scoring for collecting treasure
            self.player.treasures_collected += 1
            # Score based on item value and bonuses
            item_score_value = item.value + item.attack_bonus * 5 + item.defense_bonus * 5 + item.health_bonus * 2
            self.player.score += item_score_value
            print(f"You earned {item_score_value} points for collecting the {item.name}!")
            
            # Mark room as modified since item was taken
            self.current_room_state.modified_from_original = True
            
            return True
        else:
            print("Invalid item selection.")
            return False
    
    def talk_to_npc(self, npc_index: int) -> bool:
        """Talk to an NPC in the current room."""
        # Adjust npc_index since the game displays NPCs starting from 1
        adjusted_index = npc_index - 1
        
        if 0 <= adjusted_index < len(self.current_room_state.npcs):
            npc = self.current_room_state.npcs[adjusted_index]
            
            print(f"\n{npc.name}: {npc.dialogue}")
            
            # If NPC has a quest and hasn't given it yet
            if npc.quest and not npc.has_given_quest:
                print(f"\nQuest: {npc.quest['name']}")
                print(f"Description: {npc.quest['description']}")
                
                # Ask if player wants to accept
                accept = input("Accept quest? (yes/no): ").lower().strip()
                if accept in ['yes', 'y']:
                    npc.has_given_quest = True
                    print("Quest accepted!")
                    print(f"Goal: Bring {npc.quest['target_item']}")
                    print(f"Reward: {npc.quest['reward'].name}")
                else:
                    print("Maybe next time.")
            
            # Check if NPC has a completed quest
            elif npc.quest and npc.has_given_quest and not npc.has_completed_quest:
                # Check if player has the required item
                target_item_name = npc.quest['target_item']
                if target_item_name in [item.name for item in self.player.inventory]:
                    print(f"\nYou have brought the {target_item_name}!")
                    print(f"NPC gives you: {npc.quest['reward'].name}")
                    
                    # Give the reward
                    self.player.inventory.append(npc.quest['reward'])
                    
                    # Remove the required item from inventory
                    for i, item in enumerate(self.player.inventory):
                        if item.name == target_item_name:
                            del self.player.inventory[i]
                            break
                    
                    npc.has_completed_quest = True
                    print("Quest completed!")
                    
                    # Mark room as modified since quest was completed
                    self.current_room_state.modified_from_original = True
                else:
                    print(f"\nYou still need to find: {target_item_name}")
            
            return True
        else:
            print("Invalid NPC selection.")
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
        # Only save the mutable state of rooms, not the entire dungeon structure
        modified_room_states = {}
        for pos, room_state in self.dungeon.room_states.items():
            if room_state.modified_from_original:
                # Only save rooms that have been modified
                modified_room_states[str(pos)] = {
                    "items": [{"name": item.name, "type": item.type.value, "value": item.value, 
                              "attack_bonus": item.attack_bonus, "defense_bonus": item.defense_bonus, 
                              "health_bonus": item.health_bonus} for item in room_state.items],
                    "entities": [{"name": entity.name, "health": entity.health, "max_health": entity.max_health,
                                 "attack": entity.attack, "defense": entity.defense, "exp_reward": entity.exp_reward,
                                 "gold_min": entity.gold_min, "gold_max": entity.gold_max} 
                                for entity in room_state.entities if entity.is_alive()],
                    "npcs": [{"name": npc.name, "health": npc.health, "attack": npc.attack, "defense": npc.defense,
                              "dialogue": npc.dialogue, "quest": npc.quest, "has_given_quest": npc.has_given_quest,
                              "has_completed_quest": npc.has_completed_quest} 
                             for npc in room_state.npcs],
                    "visited": room_state.visited,
                    "unlocked_doors": [d.value for d in room_state.unlocked_doors],
                    "activated_passages": [d.value for d in room_state.activated_passages]
                }
        
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
            "dungeon_seed": self.dungeon.seed,
            "modified_rooms": modified_room_states
        }
        
        with open(filename, 'w') as f:
            json.dump(game_state, f, indent=2)
        
        # Quietly saved - don't print message
    
    def load_game(self, filename: str = "savegame.json"):
        """Load a saved game state from a file."""
        try:
            with open(filename, 'r') as f:
                game_state = json.load(f)
            
            # Reconstruct dungeon from seed
            seed = game_state.get("dungeon_seed")
            self.dungeon = SeededDungeon(seed=seed)
            
            # Load player first
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
            self.current_room_state = self.dungeon.room_states[pos]
            
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
            
            # Apply modified room states
            modified_rooms = game_state.get("modified_rooms", {})
            for pos_str, room_data in modified_rooms.items():
                pos = tuple(int(x) for x in pos_str.strip('()').split(','))
                if pos in self.dungeon.room_states:
                    room_state = self.dungeon.room_states[pos]
                    
                    # Clear existing items and add saved items
                    room_state.items = []
                    for item_data in room_data.get("items", []):
                        item = Item(
                            name=item_data["name"],
                            item_type=ItemType(item_data["type"]),
                            value=item_data["value"],
                            attack_bonus=item_data["attack_bonus"],
                            defense_bonus=item_data["defense_bonus"],
                            health_bonus=item_data["health_bonus"]
                        )
                        room_state.items.append(item)
                    
                    # Clear existing entities and add saved entities
                    room_state.entities = []
                    for entity_data in room_data.get("entities", []):
                        # Recreate enemy with current health
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
                        room_state.entities.append(enemy)
                    
                    # Clear existing NPCs and add saved NPCs
                    room_state.npcs = []
                    for npc_data in room_data.get("npcs", []):
                        npc = NonPlayerCharacter(
                            name=npc_data["name"],
                            health=npc_data["health"],
                            dialogue=npc_data["dialogue"],
                            quest=npc_data.get("quest", {})
                        )
                        npc.has_given_quest = npc_data.get("has_given_quest", False)
                        npc.has_completed_quest = npc_data.get("has_completed_quest", False)
                        room_state.npcs.append(npc)
                    
                    # Restore other state
                    room_state.visited = room_data.get("visited", False)
                    room_state.unlocked_doors = {Direction(d) for d in room_data.get("unlocked_doors", [])}
                    room_state.activated_passages = {Direction(d) for d in room_data.get("activated_passages", [])}
                    room_state.modified_from_original = True
            
            # Quietly loaded - don't print message
            return True
        except FileNotFoundError:
            # No save file - this is expected for new games
            return False
        except Exception as e:
            print(f"Error loading game: {e}")
            return False

    def load_high_score(self):
        """Load the high score from a file."""
        try:
            with open("highscore.txt", "r") as f:
                self.high_score = int(f.read().strip())
        except FileNotFoundError:
            self.high_score = 0
        except Exception:
            self.high_score = 0

    def save_high_score(self):
        """Save the high score to a file."""
        try:
            with open("highscore.txt", "w") as f:
                f.write(str(max(self.high_score, self.player.score)))
        except Exception as e:
            print(f"Error saving high score: {e}")


def main():
    import sys
    
    # Check if a command was provided as an argument
    args = sys.argv[1:]  # Exclude script name
    
    # Initialize game (try to load if exists, otherwise start new)
    game = SeededGameEngine()
    loaded = game.load_game()  # Attempt to load existing game, returns True if successful
    
    # If no save was found, we have a new game with random dungeon
    # If save was loaded, we have the saved state
    
    if not args:
        # No command provided - show current status and possible actions
        print("=== TERMINAL DUNGEON CRAWLER (SEED-BASED) ===")
        print(f"Dungeon Seed: {game.dungeon.seed}")
        print("Current Status:")
        game.show_stats()
        print()
        game.describe_room()
        print("\nPossible actions:")
        print("  move <direction> - Move north, south, east, west, up, or down")
        print("  attack <number> - Attack enemy number in room")
        print("  take <number> - Take item number from room")
        print("  equip <number> - Equip item number from inventory")
        print("  unequip <weapon|armor> - Unequip weapon or armor")
        print("  talk <number> - Talk to NPC number in room")
        print("  look - Look around the current room")
        print("  inventory - View your inventory")
        print("  stats - View your character stats")
        print("  rest - Rest to recover health")
        print("  save - Save the game")
        print("  load - Load a saved game")
        print("  quit - Quit the game")
        print("\nExample: python seeded_game_engine.py move north")
        print("         python seeded_game_engine.py move down")
        print("         python seeded_game_engine.py attack 1")
        print("         python seeded_game_engine.py take 1")
        print("         python seeded_game_engine.py equip 1")
        print("         python seeded_game_engine.py unequip armor")
        print("         python seeded_game_engine.py talk 1")
        print("         python seeded_game_engine.py stats")
        
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
            print("  move <direction> - Move north, south, east, west, up, or down")
            print("  attack <number> - Attack enemy number in room")
            print("  take <number> - Take item number from room")
            print("  equip <number> - Equip item number from inventory")
            print("  unequip <weapon|armor> - Unequip weapon or armor")
            print("  talk <number> - Talk to NPC number in room")
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
                print("Invalid direction. Use: north, south, east, west, up, or down.")
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
        elif command.startswith("talk "):
            try:
                npc_num = int(command[5:])  # Pass the original number (1-based)
                if game.talk_to_npc(npc_num):
                    game.save_game()  # Auto-save after talking to NPC (quietly)
            except ValueError:
                print("Please specify a valid NPC number to talk to.")
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
            print("Unknown command. Type 'python seeded_game_engine.py help' for a list of commands.")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    # Handle death - delete save but preserve high score
    if not game.player.is_alive():
        print("\nGame over! You have died.")
        print("Your save file has been deleted, but your high score is preserved.")
        # Preserve high score before deleting save
        high_score = game.high_score
        if game.player.score > game.high_score:
            high_score = game.player.score
            print(f"New high score: {high_score}!")
        
        # Delete the save file
        try:
            import os
            if os.path.exists("savegame.json"):
                os.remove("savegame.json")
                print("Save file deleted as per game rules.")
        except Exception as e:
            print(f"Error deleting save file: {e}")
        
        # Save high score
        game.high_score = high_score
        game.save_high_score()
    elif game.player.is_alive():
        game.save_game()


if __name__ == "__main__":
    main()