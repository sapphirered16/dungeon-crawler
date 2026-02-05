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

                # Decrease duration
                self.active_status_effects[effect] = duration - 1
                if duration - 1 <= 0:
                    effects_to_remove.append(effect)
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
                 status_effects: Optional[Dict[str, int]] = None):
        self.name = name
        self.item_type = item_type
        self.value = value
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.health_bonus = health_bonus
        self.status_effects = status_effects or {}

    def apply_to_entity(self, entity: Entity):
        """Apply item bonuses to an entity."""
        entity.attack += self.attack_bonus
        entity.defense += self.defense_bonus
        entity.max_health += self.health_bonus
        entity.health += self.health_bonus  # Heal the entity too


class NonPlayerCharacter:
    def __init__(self, name: str, health: int, dialogue: str, quest: Optional[dict] = None):
        self.name = name
        self.health = health
        self.dialogue = dialogue
        self.quest = quest  # Contains target_item, reward, description

    def interact(self, player):
        """Handle interaction with player."""
        print(f"{self.name}: {self.dialogue}")
        if self.quest:
            print(f"Quest: {self.quest['description']}")
            # Check if player has the required item
            for item in player.inventory:
                if item.name == self.quest['target_item']:
                    print(f"You hand over the {item.name}!")
                    player.inventory.remove(item)
                    player.inventory.append(self.quest['reward'])
                    print(f"The {self.name} gives you: {self.quest['reward'].name}")
                    self.quest = None  # Quest completed
                    return True
        return False


class RoomState:
    def __init__(self, position: Tuple[int, int, int]):
        self.position = position
        self.room_type = "empty"  # Default room type
        self.description = "An empty, quiet room."
        self.items: List[Item] = []
        self.entities: List[Entity] = []  # Monsters/NPCs
        self.npcs: List[NonPlayerCharacter] = []
        self.connections: Dict[Direction, Tuple[int, int, int]] = {}
        self.has_stairs_up = False
        self.has_stairs_down = False
        self.stairs_up_target = None
        self.stairs_down_target = None
        self.locked_doors: Dict[Direction, str] = {}  # direction -> key name
        self.blocked_passages: Dict[Direction, str] = {}  # direction -> trigger item name


class SeededDungeon:
    def __init__(self, seed: Optional[int] = None, width: int = 30, height: int = 30, floors: int = 3):
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

        # Define room templates with specific types and characteristics
        room_templates = {
            "starting": {"width_range": (4, 6), "height_range": (4, 6), "min_count": 1, "max_count": 1, "allowed_floors": [0]},
            "treasure": {"width_range": (4, 7), "height_range": (4, 7), "min_count": 1, "max_count": 3, "allowed_floors": "all"},
            "monster": {"width_range": (5, 8), "height_range": (4, 6), "min_count": 2, "max_count": 4, "allowed_floors": "all"},
            "trap": {"width_range": (3, 5), "height_range": (3, 5), "min_count": 1, "max_count": 3, "allowed_floors": "all"},
            "npc": {"width_range": (4, 6), "height_range": (4, 6), "min_count": 0, "max_count": 2, "allowed_floors": "all"},
            "empty": {"width_range": (4, 8), "height_range": (4, 8), "min_count": 2, "max_count": 5, "allowed_floors": "all"},
            "staircase_up": {"width_range": (3, 4), "height_range": (3, 4), "min_count": 1, "max_count": 1, "allowed_floors": "upper"},  # Floors > 0
            "staircase_down": {"width_range": (3, 4), "height_range": (3, 4), "min_count": 1, "max_count": 1, "allowed_floors": "non_last"}  # Not last floor
        }

        for floor in range(self.floors):
            # Create rooms with spacing
            rooms_info = []

            # First, place required room types for this specific floor
            required_rooms = []

            # Place starting room only on floor 0
            if floor == 0:
                start_width = random.randint(*room_templates["starting"]["width_range"])
                start_height = random.randint(*room_templates["starting"]["height_range"])
                start_x = self.width // 2 - start_width // 2
                start_y = self.height // 2 - start_height // 2
                required_rooms.append(("starting", start_x, start_y, start_width, start_height))

            # Place staircase down room on all floors except the last floor
            if floor < self.floors - 1:
                stair_width = random.randint(*room_templates["staircase_down"]["width_range"])
                stair_height = random.randint(*room_templates["staircase_down"]["height_range"])
                stair_x = random.randint(2, self.width - stair_width - 2)
                stair_y = random.randint(2, self.height - stair_height - 2)
                required_rooms.append(("staircase_down", stair_x, stair_y, stair_width, stair_height))

            # Place staircase up room on all floors except the first floor
            if floor > 0:
                stair_width = random.randint(*room_templates["staircase_up"]["width_range"])
                stair_height = random.randint(*room_templates["staircase_up"]["height_range"])
                # Place it away from the center to distinguish from other stairs
                stair_x = random.randint(2, self.width - stair_width - 2)
                stair_y = random.randint(2, self.height - stair_height - 2)
                # Make sure it's not overlapping with the down stairs if they exist on this floor
                required_rooms.append(("staircase_up", stair_x, stair_y, stair_width, stair_height))

            # Add required rooms to the list
            for room_type, x, y, width, height in required_rooms:
                room_info = self.RoomInfo(x, y, width, height, floor)
                rooms_info.append((room_info, room_type))

                # Create the room area with specific type
                for rx in range(x, x + width):
                    for ry in range(y, y + height):
                        pos = (rx, ry, floor)
                        room_state = RoomState(pos)

                        # Set room type based on template
                        if room_type == "starting":
                            room_state.room_type = "empty"  # Starting area is safe
                            room_state.description = "The entrance to the dungeon. A safe starting area."
                            # Add a starter item
                            room_state.items.append(self._generate_random_item())
                        elif room_type == "staircase_up":
                            room_state.room_type = "staircase_up"
                            room_state.description = "A room with stairs leading up from the level below."
                        elif room_type == "staircase_down":
                            room_state.room_type = "staircase_down"
                            room_state.description = "A room with stairs leading down to the next level."
                        elif room_type == "treasure":
                            room_state.room_type = "treasure"
                            room_state.description = "A treasure room filled with gleaming objects."
                            # Add multiple treasures
                            num_treasures = random.randint(1, 3)
                            for _ in range(num_treasures):
                                room_state.items.append(self._generate_random_item())
                        elif room_type == "monster":
                            room_state.room_type = "monster"
                            room_state.description = "A room with hostile creatures lurks ahead."
                            # Add multiple enemies
                            num_enemies = random.randint(1, 2)
                            for _ in range(num_enemies):
                                room_state.entities.append(self._generate_random_enemy(floor))
                        elif room_type == "trap":
                            room_state.room_type = "trap"
                            room_state.description = "A dangerous-looking room with potential hazards."
                        elif room_type == "npc":
                            room_state.room_type = "npc"
                            room_state.description = "A room with a mysterious stranger."

                            # Create an NPC with a quest
                            if (rx, ry) == (x, y):  # Only add NPC to one tile in the room to avoid duplicates
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
                        else:  # empty
                            room_state.room_type = "empty"
                            room_state.description = "An empty, quiet room."

                        # Add some extra items to treasure and empty rooms
                        if room_state.room_type in ["treasure", "empty"] and room_type != "starting":
                            if random.random() < 0.3:  # 30% chance to add extra item
                                room_state.items.append(self._generate_random_item())

                        self.room_states[pos] = room_state

            # Now place additional rooms based on templates, respecting floor constraints
            room_counts = {rtype: 0 for rtype in room_templates.keys()}

            # Count already placed required rooms
            for _, rtype in rooms_info:
                if rtype in room_counts:
                    room_counts[rtype] += 1

            # Place additional rooms up to the maximum count for each type, respecting floor constraints
            total_attempts = 0
            max_total_rooms = random.randint(8, 15)

            while len(rooms_info) < max_total_rooms and total_attempts < 100:
                total_attempts += 1

                # Select a room type to place based on remaining quota and floor constraints
                available_types = []
                for rtype, limits in room_templates.items():
                    # Check if this room type is allowed on this floor
                    allowed_on_floor = False
                    if limits["allowed_floors"] == "all":
                        allowed_on_floor = True
                    elif limits["allowed_floors"] == "upper" and floor > 0:
                        allowed_on_floor = True
                    elif limits["allowed_floors"] == "non_last" and floor < self.floors - 1:
                        allowed_on_floor = True
                    elif isinstance(limits["allowed_floors"], list) and floor in limits["allowed_floors"]:
                        allowed_on_floor = True
                    
                    # Check if we haven't reached the max count for this type
                    if room_counts.get(rtype, 0) < limits["max_count"] and allowed_on_floor:
                        # Add the type multiple times to weight the probability
                        for _ in range(max(1, limits["max_count"] - room_counts.get(rtype, 0))):
                            available_types.append(rtype)

                if not available_types:
                    break  # No more room types to place

                room_type = random.choice(available_types)

                # Skip already-handled special rooms (starting, stairs) as they're already placed
                if room_type in ["starting", "staircase_up", "staircase_down"]:
                    continue

                # Get dimensions for this room type
                room_width = random.randint(*room_templates[room_type]["width_range"])
                room_height = random.randint(*room_templates[room_type]["height_range"])

                # Random position (ensuring it fits in the grid with spacing)
                # Add spacing buffer to prevent rooms from being too close
                spacing_buffer = 3  # Minimum space between rooms
                x = random.randint(spacing_buffer, self.width - room_width - spacing_buffer)
                y = random.randint(spacing_buffer, self.height - room_height - spacing_buffer)

                # Check for overlap with existing rooms (with spacing)
                overlaps = False
                for existing_room_info, _ in rooms_info:
                    existing_room = existing_room_info
                    # Check for overlap with spacing buffer
                    min_dist_x = existing_room.x - room_width - spacing_buffer
                    max_dist_x = existing_room.x + existing_room.width + spacing_buffer
                    min_dist_y = existing_room.y - room_height - spacing_buffer
                    max_dist_y = existing_room.y + existing_room.height + spacing_buffer

                    if not (x > max_dist_x or x + room_width < min_dist_x or 
                           y > max_dist_y or y + room_height < min_dist_y):
                        overlaps = True
                        break

                if not overlaps:
                    room_info = self.RoomInfo(x, y, room_width, room_height, floor)
                    rooms_info.append((room_info, room_type))
                    room_counts[room_type] += 1

                    # Create the room area with specific type
                    for rx in range(x, x + room_width):
                        for ry in range(y, y + room_height):
                            pos = (rx, ry, floor)
                            room_state = RoomState(pos)

                            # Set room type based on template
                            if room_type == "treasure":
                                room_state.room_type = "treasure"
                                room_state.description = "A treasure room filled with gleaming objects."
                                # Add multiple treasures
                                num_treasures = random.randint(1, 3)
                                for _ in range(num_treasures):
                                    room_state.items.append(self._generate_random_item())
                            elif room_type == "monster":
                                room_state.room_type = "monster"
                                room_state.description = "A room with hostile creatures lurks ahead."
                                # Add multiple enemies
                                num_enemies = random.randint(1, 2)
                                for _ in range(num_enemies):
                                    room_state.entities.append(self._generate_random_enemy(floor))
                            elif room_type == "trap":
                                room_state.room_type = "trap"
                                room_state.description = "A dangerous-looking room with potential hazards."
                            elif room_type == "npc":
                                room_state.room_type = "npc"
                                room_state.description = "A room with a mysterious stranger."

                                # Create an NPC with a quest
                                if (rx, ry) == (x, y):  # Only add NPC to one tile in the room to avoid duplicates
                                    # Customize NPC dialog based on floor depth for more immersive experience
                                    floor_specific_dialogs = {
                                        0: [
                                            "Greetings, traveler. The surface world feels distant already.",
                                            "Hello adventurer, I seek a powerful item that was lost in these depths.",
                                            "Welcome, hero. I need someone to retrieve something precious to me."
                                        ],
                                        1: [
                                            "You're descending deeper. Be wary of what lies ahead.",
                                            "Another soul dares to venture where few return.",
                                            "The deeper you go, the more dangerous it becomes."
                                        ],
                                        2: [
                                            "So deep already? You must be truly brave.",
                                            "Few make it this far. What brings you to these depths?",
                                            "The ancient guardian of this level won't let you pass easily."
                                        ]
                                    }
                                    
                                    dialogs = floor_specific_dialogs.get(floor, [
                                        "Oh, a visitor! Perhaps you can assist me with a small matter.",
                                        "Adventurer, I have a task for you if you're brave enough.",
                                        "Welcome, hero. I need someone to retrieve something precious to me."
                                    ])

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

                                    quest_description = f"I need you to defeat a {target_monster} on floor {floor + 1} and bring me its trophy. In return, I'll give you this {reward.name}."

                                    npc = NonPlayerCharacter(
                                        name="Wandering Sage" if floor < 2 else "Ancient Keeper",
                                        health=1,
                                        dialogue=random.choice(dialogs),
                                        quest={
                                            "target_item": target_item,
                                            "reward": reward,
                                            "description": quest_description
                                        }
                                    )
                                    room_state.npcs.append(npc)
                            else:  # empty
                                room_state.room_type = "empty"
                                room_state.description = "An empty, quiet room."

                            # Add some extra items to treasure and empty rooms
                            if room_state.room_type in ["treasure", "empty"]:
                                if random.random() < 0.3:  # 30% chance to add extra item
                                    room_state.items.append(self._generate_random_item())

                            self.room_states[pos] = room_state

            # Connect rooms with hallways and establish directional connections
            if len(rooms_info) > 1:
                # Create hallways connecting rooms in sequence to ensure all are connected
                for i in range(len(rooms_info) - 1):
                    room1_info, _ = rooms_info[i]
                    room2_info, _ = rooms_info[i + 1]

                    # Create L-shaped corridor between room centers
                    self._create_corridor(room1_info.center_x, room1_info.center_y, 
                                       room2_info.center_x, room2_info.center_y, floor)

                    # Establish directional connections between the rooms
                    # Find a hallway cell that connects these two rooms
                    # First, find all hallway cells between these rooms
                    hallway_points = self._find_hallway_between_rooms(room1_info, room2_info, floor)
                    
                    # Connect the rooms via hallway points
                    for rx in range(room1_info.x, room1_info.x + room1_info.width):
                        for ry in range(room1_info.y, room1_info.y + room1_info.height):
                            pos1 = (rx, ry, floor)
                            if pos1 in self.room_states:
                                # Connect to hallway points near room2
                                for h_x, h_y in hallway_points:
                                    # If hallway point is adjacent to room1 area
                                    if abs(h_x - rx) <= 1 and abs(h_y - ry) <= 1 and (h_x != rx or h_y != ry):
                                        # Determine direction from room1 point to hallway
                                        dx, dy = h_x - rx, h_y - ry
                                        direction = None
                                        if dx == 1: direction = Direction.EAST
                                        elif dx == -1: direction = Direction.WEST
                                        elif dy == 1: direction = Direction.SOUTH
                                        elif dy == -1: direction = Direction.NORTH
                                        
                                        if direction:
                                            hallway_pos = (h_x, h_y, floor)
                                            self.room_states[pos1].connections[direction] = hallway_pos
                                            
                    for rx in range(room2_info.x, room2_info.x + room2_info.width):
                        for ry in range(room2_info.y, room2_info.y + room2_info.height):
                            pos2 = (rx, ry, floor)
                            if pos2 in self.room_states:
                                # Connect to hallway points near room1
                                for h_x, h_y in hallway_points:
                                    # If hallway point is adjacent to room2 area
                                    if abs(h_x - rx) <= 1 and abs(h_y - ry) <= 1 and (h_x != rx or h_y != ry):
                                        # Determine direction from hallway to room2 point
                                        dx, dy = rx - h_x, ry - h_y
                                        direction = None
                                        if dx == 1: direction = Direction.EAST
                                        elif dx == -1: direction = Direction.WEST
                                        elif dy == 1: direction = Direction.SOUTH
                                        elif dy == -1: direction = Direction.NORTH
                                        
                                        if direction:
                                            hallway_pos = (h_x, h_y, floor)
                                            self.room_states[pos2].connections[direction] = hallway_pos

                # Ensure good connectivity by adding extra connections
                for i in range(len(rooms_info)):
                    # Connect to a random other room to ensure all rooms are reachable
                    j = random.randint(0, len(rooms_info) - 1)
                    if i != j and random.random() < 0.3:  # 30% chance of extra connection
                        room_i_info, _ = rooms_info[i]
                        room_j_info, _ = rooms_info[j]
                        
                        # Create corridor between rooms
                        self._create_corridor(room_i_info.center_x, room_i_info.center_y,
                                           room_j_info.center_x, room_j_info.center_y, floor)
                        
                        # Establish connections between these rooms too
                        hallway_points = self._find_hallway_between_rooms(room_i_info, room_j_info, floor)
                        
                        for rx in range(room_i_info.x, room_i_info.x + room_i_info.width):
                            for ry in range(room_i_info.y, room_i_info.y + room_i_info.height):
                                pos_i = (rx, ry, floor)
                                if pos_i in self.room_states:
                                    for h_x, h_y in hallway_points:
                                        if abs(h_x - rx) <= 1 and abs(h_y - ry) <= 1 and (h_x != rx or h_y != ry):
                                            dx, dy = h_x - rx, h_y - ry
                                            direction = None
                                            if dx == 1: direction = Direction.EAST
                                            elif dx == -1: direction = Direction.WEST
                                            elif dy == 1: direction = Direction.SOUTH
                                            elif dy == -1: direction = Direction.NORTH
                                            
                                            if direction:
                                                hallway_pos = (h_x, h_y, floor)
                                                self.room_states[pos_i].connections[direction] = hallway_pos
                                                
                        for rx in range(room_j_info.x, room_j_info.x + room_j_info.width):
                            for ry in range(room_j_info.y, room_j_info.y + room_j_info.height):
                                pos_j = (rx, ry, floor)
                                if pos_j in self.room_states:
                                    for h_x, h_y in hallway_points:
                                        if abs(h_x - rx) <= 1 and abs(h_y - ry) <= 1 and (h_x != rx or h_y != ry):
                                            dx, dy = rx - h_x, ry - h_y
                                            direction = None
                                            if dx == 1: direction = Direction.EAST
                                            elif dx == -1: direction = Direction.WEST
                                            elif dy == 1: direction = Direction.SOUTH
                                            elif dy == -1: direction = Direction.NORTH
                                            
                                            if direction:
                                                hallway_pos = (h_x, h_y, floor)
                                                self.room_states[pos_j].connections[direction] = hallway_pos

    def _find_hallway_between_rooms(self, room1_info, room2_info, floor):
        """Helper method to find hallway points between two rooms"""
        # For now, just return the center points as a simplified approach
        # In a more sophisticated implementation, we'd trace the actual corridor
        points = []
        
        # Add center points and adjacent points as potential hallway connections
        center1 = (room1_info.center_x, room1_info.center_y)
        center2 = (room2_info.center_x, room2_info.center_y)
        
        # Add center of room 1
        points.append(center1)
        # Add center of room 2  
        points.append(center2)
        
        # Add a few points along the path for L-shaped corridors
        # Horizontal segment
        for x in range(min(center1[0], center2[0]), max(center1[0], center2[0]) + 1):
            points.append((x, center1[1]))
        # Vertical segment
        for y in range(min(center1[1], center2[1]), max(center1[1], center2[1]) + 1):
            points.append((center2[0], y))
            
        return list(set(points))  # Remove duplicates

    def _generate_base_structure(self):
        """Generate the base dungeon structure based on the seed"""
        # Set the random seed to ensure reproducible generation
        random.seed(self.seed)

        # Define room templates with specific types and characteristics
        room_templates = {
            "starting": {"width_range": (4, 6), "height_range": (4, 6), "min_count": 1, "max_count": 1, "allowed_floors": [0]},
            "treasure": {"width_range": (4, 7), "height_range": (4, 7), "min_count": 1, "max_count": 3, "allowed_floors": "all"},
            "monster": {"width_range": (5, 8), "height_range": (4, 6), "min_count": 2, "max_count": 4, "allowed_floors": "all"},
            "trap": {"width_range": (3, 5), "height_range": (3, 5), "min_count": 1, "max_count": 3, "allowed_floors": "all"},
            "npc": {"width_range": (4, 6), "height_range": (4, 6), "min_count": 0, "max_count": 2, "allowed_floors": "all"},
            "empty": {"width_range": (4, 8), "height_range": (4, 8), "min_count": 2, "max_count": 5, "allowed_floors": "all"},
            "staircase_up": {"width_range": (3, 4), "height_range": (3, 4), "min_count": 1, "max_count": 1, "allowed_floors": "upper"},  # Floors > 0
            "staircase_down": {"width_range": (3, 4), "height_range": (3, 4), "min_count": 1, "max_count": 1, "allowed_floors": "non_last"}  # Not last floor
        }

        for floor in range(self.floors):
            # Create rooms with spacing
            rooms_info = []

            # First, place required room types for this specific floor
            required_rooms = []

            # Place starting room only on floor 0
            if floor == 0:
                start_width = random.randint(*room_templates["starting"]["width_range"])
                start_height = random.randint(*room_templates["starting"]["height_range"])
                start_x = self.width // 2 - start_width // 2
                start_y = self.height // 2 - start_height // 2
                required_rooms.append(("starting", start_x, start_y, start_width, start_height))

            # Place staircase down room on all floors except the last floor
            if floor < self.floors - 1:
                stair_width = random.randint(*room_templates["staircase_down"]["width_range"])
                stair_height = random.randint(*room_templates["staircase_down"]["height_range"])
                stair_x = random.randint(2, self.width - stair_width - 2)
                stair_y = random.randint(2, self.height - stair_height - 2)
                required_rooms.append(("staircase_down", stair_x, stair_y, stair_width, stair_height))

            # Place staircase up room on all floors except the first floor
            if floor > 0:
                stair_width = random.randint(*room_templates["staircase_up"]["width_range"])
                stair_height = random.randint(*room_templates["staircase_up"]["height_range"])
                # Place it away from the center to distinguish from other stairs
                stair_x = random.randint(2, self.width - stair_width - 2)
                stair_y = random.randint(2, self.height - stair_height - 2)
                # Make sure it's not overlapping with the down stairs if they exist on this floor
                required_rooms.append(("staircase_up", stair_x, stair_y, stair_width, stair_height))

            # Add required rooms to the list
            for room_type, x, y, width, height in required_rooms:
                room_info = self.RoomInfo(x, y, width, height, floor)
                rooms_info.append((room_info, room_type))

                # Create the room area with specific type
                for rx in range(x, x + width):
                    for ry in range(y, y + height):
                        pos = (rx, ry, floor)
                        room_state = RoomState(pos)

                        # Set room type based on template
                        if room_type == "starting":
                            room_state.room_type = "empty"  # Starting area is safe
                            room_state.description = "The entrance to the dungeon. A safe starting area."
                            # Add a starter item
                            room_state.items.append(self._generate_random_item())
                        elif room_type == "staircase_up":
                            room_state.room_type = "staircase_up"
                            room_state.description = "A room with stairs leading up from the level below."
                        elif room_type == "staircase_down":
                            room_state.room_type = "staircase_down"
                            room_state.description = "A room with stairs leading down to the next level."
                        elif room_type == "treasure":
                            room_state.room_type = "treasure"
                            room_state.description = "A treasure room filled with gleaming objects."
                            # Add multiple treasures
                            num_treasures = random.randint(1, 3)
                            for _ in range(num_treasures):
                                room_state.items.append(self._generate_random_item())
                        elif room_type == "monster":
                            room_state.room_type = "monster"
                            room_state.description = "A room with hostile creatures lurks ahead."
                            # Add multiple enemies
                            num_enemies = random.randint(1, 2)
                            for _ in range(num_enemies):
                                room_state.entities.append(self._generate_random_enemy(floor))
                        elif room_type == "trap":
                            room_state.room_type = "trap"
                            room_state.description = "A dangerous-looking room with potential hazards."
                        elif room_type == "npc":
                            room_state.room_type = "npc"
                            room_state.description = "A room with a mysterious stranger."

                            # Create an NPC with a quest
                            if (rx, ry) == (x, y):  # Only add NPC to one tile in the room to avoid duplicates
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

                                quest_description = f"I need you to defeat a {target_monster} on floor {floor + 1} and bring me its trophy. In return, I'll give you this {reward.name}."

                                npc = NonPlayerCharacter(
                                    name="Wandering Sage" if floor < 2 else "Ancient Keeper",
                                    health=1,
                                    dialogue=random.choice(npc_dialogues),
                                    quest={
                                        "target_item": target_item,
                                        "reward": reward,
                                        "description": quest_description
                                    }
                                )
                                room_state.npcs.append(npc)
                        else:  # empty
                            room_state.room_type = "empty"
                            room_state.description = "An empty, quiet room."

                        # Add some extra items to treasure and empty rooms
                        if room_state.room_type in ["treasure", "empty"] and room_type != "starting":
                            if random.random() < 0.3:  # 30% chance to add extra item
                                room_state.items.append(self._generate_random_item())

                        self.room_states[pos] = room_state

            # Now place additional rooms based on templates, respecting floor constraints
            room_counts = {rtype: 0 for rtype in room_templates.keys()}

            # Count already placed required rooms
            for _, rtype in rooms_info:
                if rtype in room_counts:
                    room_counts[rtype] += 1

            # Place additional rooms up to the maximum count for each type, respecting floor constraints
            total_attempts = 0
            max_total_rooms = random.randint(8, 15)

            while len(rooms_info) < max_total_rooms and total_attempts < 100:
                total_attempts += 1

                # Select a room type to place based on remaining quota and floor constraints
                available_types = []
                for rtype, limits in room_templates.items():
                    # Check if this room type is allowed on this floor
                    allowed_on_floor = False
                    if limits["allowed_floors"] == "all":
                        allowed_on_floor = True
                    elif limits["allowed_floors"] == "upper" and floor > 0:
                        allowed_on_floor = True
                    elif limits["allowed_floors"] == "non_last" and floor < self.floors - 1:
                        allowed_on_floor = True
                    elif isinstance(limits["allowed_floors"], list) and floor in limits["allowed_floors"]:
                        allowed_on_floor = True
                    
                    # Check if we haven't reached the max count for this type
                    if room_counts.get(rtype, 0) < limits["max_count"] and allowed_on_floor:
                        # Add the type multiple times to weight the probability
                        for _ in range(max(1, limits["max_count"] - room_counts.get(rtype, 0))):
                            available_types.append(rtype)

                if not available_types:
                    break  # No more room types to place

                room_type = random.choice(available_types)

                # Skip already-handled special rooms (starting, stairs) as they're already placed
                if room_type in ["starting", "staircase_up", "staircase_down"]:
                    continue

                # Get dimensions for this room type
                room_width = random.randint(*room_templates[room_type]["width_range"])
                room_height = random.randint(*room_templates[room_type]["height_range"])

                # Random position (ensuring it fits in the grid with spacing)
                # Add spacing buffer to prevent rooms from being too close
                spacing_buffer = 3  # Minimum space between rooms
                x = random.randint(spacing_buffer, self.width - room_width - spacing_buffer)
                y = random.randint(spacing_buffer, self.height - room_height - spacing_buffer)

                # Check for overlap with existing rooms (with spacing)
                overlaps = False
                for existing_room_info, _ in rooms_info:
                    existing_room = existing_room_info
                    # Check for overlap with spacing buffer
                    min_dist_x = existing_room.x - room_width - spacing_buffer
                    max_dist_x = existing_room.x + existing_room.width + spacing_buffer
                    min_dist_y = existing_room.y - room_height - spacing_buffer
                    max_dist_y = existing_room.y + existing_room.height + spacing_buffer

                    if not (x > max_dist_x or x + room_width < min_dist_x or 
                           y > max_dist_y or y + room_height < min_dist_y):
                        overlaps = True
                        break

                if not overlaps:
                    room_info = self.RoomInfo(x, y, room_width, room_height, floor)
                    rooms_info.append((room_info, room_type))
                    room_counts[room_type] += 1

                    # Create the room area with specific type
                    for rx in range(x, x + room_width):
                        for ry in range(y, y + room_height):
                            pos = (rx, ry, floor)
                            room_state = RoomState(pos)

                            # Set room type based on template
                            if room_type == "treasure":
                                room_state.room_type = "treasure"
                                room_state.description = "A treasure room filled with gleaming objects."
                                # Add multiple treasures
                                num_treasures = random.randint(1, 3)
                                for _ in range(num_treasures):
                                    room_state.items.append(self._generate_random_item())
                            elif room_type == "monster":
                                room_state.room_type = "monster"
                                room_state.description = "A room with hostile creatures lurks ahead."
                                # Add multiple enemies
                                num_enemies = random.randint(1, 2)
                                for _ in range(num_enemies):
                                    room_state.entities.append(self._generate_random_enemy(floor))
                            elif room_type == "trap":
                                room_state.room_type = "trap"
                                room_state.description = "A dangerous-looking room with potential hazards."
                            elif room_type == "npc":
                                room_state.room_type = "npc"
                                room_state.description = "A room with a mysterious stranger."

                                # Create an NPC with a quest
                                if (rx, ry) == (x, y):  # Only add NPC to one tile in the room to avoid duplicates
                                    # Customize NPC dialog based on floor depth for more immersive experience
                                    floor_specific_dialogs = {
                                        0: [
                                            "Greetings, traveler. The surface world feels distant already.",
                                            "Hello adventurer, I seek a powerful item that was lost in these depths.",
                                            "Welcome, hero. I need someone to retrieve something precious to me."
                                        ],
                                        1: [
                                            "You're descending deeper. Be wary of what lies ahead.",
                                            "Another soul dares to venture where few return.",
                                            "The deeper you go, the more dangerous it becomes."
                                        ],
                                        2: [
                                            "So deep already? You must be truly brave.",
                                            "Few make it this far. What brings you to these depths?",
                                            "The ancient guardian of this level won't let you pass easily."
                                        ]
                                    }
                                    
                                    dialogs = floor_specific_dialogs.get(floor, [
                                        "Oh, a visitor! Perhaps you can assist me with a small matter.",
                                        "Adventurer, I have a task for you if you're brave enough.",
                                        "Welcome, hero. I need someone to retrieve something precious to me."
                                    ])

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

                                    quest_description = f"I need you to defeat a {target_monster} on floor {floor + 1} and bring me its trophy. In return, I'll give you this {reward.name}."

                                    npc = NonPlayerCharacter(
                                        name="Wandering Sage" if floor < 2 else "Ancient Keeper",
                                        health=1,
                                        dialogue=random.choice(dialogs),
                                        quest={
                                            "target_item": target_item,
                                            "reward": reward,
                                            "description": quest_description
                                        }
                                    )
                                    room_state.npcs.append(npc)
                            else:  # empty
                                room_state.room_type = "empty"
                                room_state.description = "An empty, quiet room."

                            # Add some extra items to treasure and empty rooms
                            if room_state.room_type in ["treasure", "empty"]:
                                if random.random() < 0.3:  # 30% chance to add extra item
                                    room_state.items.append(self._generate_random_item())

                            self.room_states[pos] = room_state

            # Connect rooms with hallways (this creates the narrow connections between rooms)
            if len(rooms_info) > 1:
                # Create hallways connecting rooms in sequence to ensure all are connected
                for i in range(len(rooms_info) - 1):
                    room1_info, _ = rooms_info[i]
                    room2_info, _ = rooms_info[i + 1]

                    # Create L-shaped corridor between room centers
                    self._create_corridor(room1_info.center_x, room1_info.center_y, 
                                       room2_info.center_x, room2_info.center_y, floor)

                # Ensure good connectivity by adding extra connections
                for i in range(len(rooms_info)):
                    # Connect to a random other room to ensure all rooms are reachable
                    j = random.randint(0, len(rooms_info) - 1)
                    if i != j and random.random() < 0.3:  # 30% chance of extra connection
                        room_i_info, _ = rooms_info[i]
                        room_j_info, _ = rooms_info[j]
                        self._create_corridor(room_i_info.center_x, room_i_info.center_y,
                                           room_j_info.center_x, room_j_info.center_y, floor)

            # Place the ultimate artifact on the deepest floor
            if floor == self.floors - 1:  # Last floor (deepest)
                # Find a random treasure room in this floor to place the artifact
                treasure_rooms = [(x, y, z) for (x, y, z), room_state in self.room_states.items() 
                                if z == floor and room_state.room_type == "treasure"]
                if treasure_rooms:
                    artifact_pos = random.choice(treasure_rooms)
                    artifact_room = self.room_states[artifact_pos]
                    artifact_room.room_type = "artifact"
                    artifact_room.description = "A mystical chamber glows with ethereal light. At the center lies the legendary Artifact of Power!"
                    artifact_room.items.append(Item("Artifact of Power", ItemType.CONSUMABLE, value=1000, 
                                                  attack_bonus=50, defense_bonus=50, health_bonus=100))
                else:
                    # If no treasure room found, place in any room on the last floor
                    floor_rooms = [(x, y, z) for x, y, z in self.room_states.keys() if z == floor]
                    if floor_rooms:
                        artifact_pos = random.choice(floor_rooms)
                        artifact_room = self.room_states[artifact_pos]
                        artifact_room.room_type = "artifact"
                        artifact_room.description = "A mystical chamber glows with ethereal light. At the center lies the legendary Artifact of Power!"
                        artifact_room.items.append(Item("Artifact of Power", ItemType.CONSUMABLE, value=1000, 
                                                      attack_bonus=50, defense_bonus=50, health_bonus=100))

        # After creating all rooms and hallways, establish connections between adjacent cells
        # This is a simplified approach: connect adjacent cells that are both in the dungeon
        for x in range(self.width):
            for y in range(self.height):
                for floor in range(self.floors):
                    pos = (x, y, floor)
                    if pos in self.room_states:
                        current_room = self.room_states[pos]
                        
                        # Check adjacent positions
                        adjacent_offsets = [
                            (Direction.NORTH, 0, -1),
                            (Direction.SOUTH, 0, 1),
                            (Direction.EAST, 1, 0),
                            (Direction.WEST, -1, 0)
                        ]
                        
                        for direction, dx, dy in adjacent_offsets:
                            adj_pos = (x + dx, y + dy, floor)
                            if adj_pos in self.room_states:
                                current_room.connections[direction] = adj_pos

        # Add stairs between floors (using special room flags)
        # Ensure at least one staircase exists between each pair of floors
        # But make sure stairs are not in the starting room area
        for floor in range(self.floors - 1):  # Connect each floor to the one below it
            # Find rooms on the current floor that are not the starting room area
            # We'll avoid placing stairs near the starting area
            start_area_positions = set()
            # Define start area as rooms on floor 0 that are not staircase rooms
            for pos, room_state in self.room_states.items():
                if pos[2] == 0 and room_state.room_type == "empty":  # Likely the starting room area
                    start_area_positions.add(pos)

            current_floor_rooms = [(x, y, z) for (x, y, z), room_state in self.room_states.items() 
                                 if z == floor and (x, y, z) not in start_area_positions and room_state.room_type not in ["staircase_up", "staircase_down"]]
            next_floor_rooms = [(x, y, z) for (x, y, z), room_state in self.room_states.items() 
                              if z == floor + 1 and room_state.room_type not in ["staircase_up", "staircase_down"]]

            if current_floor_rooms and next_floor_rooms:
                # Pick a random room from each floor to place stairs (avoiding start area)
                current_room_pos = random.choice(current_floor_rooms)
                next_room_pos = random.choice(next_floor_rooms)

                current_room_state = self.room_states[current_room_pos]
                next_room_state = self.room_states[next_room_pos]

                # Mark rooms as having stairs and set targets
                current_room_state.has_stairs_down = True
                current_room_state.stairs_down_target = next_room_pos  # Going down leads to next floor room
                next_room_state.has_stairs_up = True
                next_room_state.stairs_up_target = current_room_pos   # Going up leads back to current floor room

                # Update descriptions to reflect the connection
                if current_room_state.room_type != "staircase_down":
                    current_room_state.description = "A room with stairs leading down to the next level."
                if next_room_state.room_type != "staircase_up":
                    next_room_state.description = "A room with stairs leading up from the level below."

        # Add locked doors and blocked passages for puzzle elements
        # These should be placed in hallways to create meaningful barriers between areas
        hallway_rooms = [room_state for room_state in self.room_states.values() 
                        if getattr(room_state, 'room_type', '') == 'hallway' and len(room_state.connections) > 0]

        # If we don't have enough hallway rooms, include some other connection points
        if len(hallway_rooms) < 3:  # Need at least a few hallways for this to make sense
            all_accessible_rooms = [room_state for room_state in self.room_states.values() if len(room_state.connections) > 0]
        else:
            all_accessible_rooms = hallway_rooms

        # Add some locked doors (about 10% of accessible rooms, but prefer hallways)
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

                # Add the corresponding key to a room that comes before this one in dungeon progression
                # We'll place keys on earlier floors or in earlier areas of the same floor
                key_rooms = []
                
                # Look for rooms on the same floor with lower coordinates (more central/earlier areas)
                current_pos = list(room_state.position) if hasattr(room_state, 'position') else list(next(k for k,v in self.room_states.items() if v == room_state))
                current_floor = current_pos[2]
                
                # Find rooms on the same floor that are "earlier" (closer to starting area)
                for other_room in self.room_states.values():
                    if (other_room != room_state and 
                        other_room.room_type not in ["staircase_up", "staircase_down"] and  # Don't put keys in stair rooms
                        other_room.room_type != "hallway"):  # Don't put keys in hallways
                        # Check if this room is on the same or earlier floor
                        other_pos = list(other_room.position) if hasattr(other_room, 'position') else list(next(k for k,v in self.room_states.items() if v == other_room))
                        if other_pos[2] <= current_floor:
                            key_rooms.append(other_room)
                
                # If no suitable rooms found, fall back to any non-staircase rooms
                if not key_rooms:
                    for other_room in self.room_states.values():
                        if (other_room != room_state and 
                            other_room.room_type not in ["staircase_up", "staircase_down"] and
                            other_room.room_type != "hallway"):  # Still avoid hallways for keys
                            key_rooms.append(other_room)
                
                if key_rooms:
                    key_room = random.choice(key_rooms)
                    key_item = Item(name=key_required, item_type=ItemType.KEY, value=10)
                    key_room.items.append(key_item)
                    placed_keys.add(key_required)

        # Add some blocked passages (about 5% of accessible rooms, but prefer hallways)
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
        # Handle case where there aren't enough rooms
        elif len(remaining_rooms) == 0:
            remaining_rooms = all_accessible_rooms

        selected_rooms_for_passages = random.sample(remaining_rooms, min(num_blocked_passages, len(remaining_rooms)))

        for room_state in selected_rooms_for_passages:
            room_state.blocked_passages[Direction(random.choice(["north", "south", "east", "west"]))] = random.choice(["Rune", "Powder", "Crystal", "Stone", "Charm", "Sundial", "Sunday"])
            
            # Add the item needed to clear the blocked passage to an earlier area
            # Similar logic to keys above
            trigger_items = {
                "Rune": "Power Rune",
                "Powder": "Magic Powder", 
                "Crystal": "Power Crystal",
                "Stone": "Power Stone",
                "Charm": "Power Charm",
                "Sundial": "Power Sundial",
                "Sunday": "Sunday"
            }
            trigger_needed = random.choice(["Rune", "Powder", "Crystal", "Stone", "Charm", "Sundial", "Sunday"])
            item_needed = trigger_items[trigger_needed]
            
            # Find a suitable room for the trigger item (similar to key placement)
            trigger_rooms = []
            current_pos = list(room_state.position) if hasattr(room_state, 'position') else list(next(k for k,v in self.room_states.items() if v == room_state))
            current_floor = current_pos[2]
            
            for other_room in self.room_states.values():
                if (other_room != room_state and 
                    other_room.room_type not in ["staircase_up", "staircase_down"] and
                    other_room.room_type != "hallway"):  # Don't put trigger items in hallways
                    other_pos = list(other_room.position) if hasattr(other_room, 'position') else list(next(k for k,v in self.room_states.items() if v == other_room))
                    if other_pos[2] <= current_floor:
                        trigger_rooms.append(other_room)
            
            if trigger_rooms:
                trigger_room = random.choice(trigger_rooms)
                trigger_item = Item(name=item_needed, item_type=ItemType.TRIGGER, value=5)
                trigger_room.items.append(trigger_item)

        # With the new room structure, rooms are connected via hallways created earlier,
        # not through adjacent grid positions. The hallway creation already established
        # connections between rooms, so we don't need this automatic grid-based connection.
        # Rooms exist as areas in the grid and are connected via the hallway system created earlier.

        # Add stairs between floors (using special room flags)
        # Ensure at least one staircase exists between each pair of floors
        # But make sure stairs are not in the starting room area
        for floor in range(self.floors - 1):  # Connect each floor to the one below it
            # Find rooms on the current floor that are not the starting room area
            # We'll avoid placing stairs near the starting area
            start_area_positions = set()
            # Define start area as rooms on floor 0 that are not staircase rooms
            for pos, room_state in self.room_states.items():
                if pos[2] == 0 and room_state.room_type == "empty":  # Likely the starting room area
                    start_area_positions.add(pos)

            current_floor_rooms = [(x, y, z) for (x, y, z), room_state in self.room_states.items() 
                                 if z == floor and (x, y, z) not in start_area_positions and room_state.room_type not in ["staircase_up", "staircase_down"]]
            next_floor_rooms = [(x, y, z) for (x, y, z), room_state in self.room_states.items() 
                              if z == floor + 1 and room_state.room_type not in ["staircase_up", "staircase_down"]]

            if current_floor_rooms and next_floor_rooms:
                # Pick a random room from each floor to place stairs (avoiding start area)
                current_room_pos = random.choice(current_floor_rooms)
                next_room_pos = random.choice(next_floor_rooms)

                current_room_state = self.room_states[current_room_pos]
                next_room_state = self.room_states[next_room_pos]

                # Mark rooms as having stairs and set targets
                current_room_state.has_stairs_down = True
                current_room_state.stairs_down_target = next_room_pos  # Going down leads to next floor room
                next_room_state.has_stairs_up = True
                next_room_state.stairs_up_target = current_room_pos   # Going up leads back to current floor room

                # Update descriptions to reflect the connection
                if current_room_state.room_type != "staircase_down":
                    current_room_state.description = "A room with stairs leading down to the next level."
                if next_room_state.room_type != "staircase_up":
                    next_room_state.description = "A room with stairs leading up from the level below."

        # After creating all rooms and hallways, establish connections between adjacent cells
        # This is a simplified approach: connect adjacent cells that are both in the dungeon
        for x in range(self.width):
            for y in range(self.height):
                for floor in range(self.floors):
                    pos = (x, y, floor)
                    if pos in self.room_states:
                        current_room = self.room_states[pos]
                        
                        # Check adjacent positions
                        adjacent_offsets = [
                            (Direction.NORTH, 0, -1),
                            (Direction.SOUTH, 0, 1),
                            (Direction.EAST, 1, 0),
                            (Direction.WEST, -1, 0)
                        ]
                        
                        for direction, dx, dy in adjacent_offsets:
                            adj_pos = (x + dx, y + dy, floor)
                            if adj_pos in self.room_states:
                                current_room.connections[direction] = adj_pos

        # Add locked doors and blocked passages for puzzle elements
        # These should be placed in hallways to create meaningful barriers between areas
        hallway_rooms = [room_state for room_state in self.room_states.values() 
                        if getattr(room_state, 'room_type', '') == 'hallway' and len(room_state.connections) > 0]

        # If we don't have enough hallway rooms, include some other connection points
        if len(hallway_rooms) < 3:  # Need at least a few hallways for this to make sense
            all_accessible_rooms = [room_state for room_state in self.room_states.values() if len(room_state.connections) > 0]
        else:
            all_accessible_rooms = hallway_rooms

        # Add some locked doors (about 10% of accessible rooms, but prefer hallways)
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

                # Add the corresponding key to a room that comes before this one in dungeon progression
                # We'll place keys on earlier floors or in earlier areas of the same floor
                key_rooms = []
                
                # Look for rooms on the same floor with lower coordinates (more central/earlier areas)
                current_pos = list(room_state.position) if hasattr(room_state, 'position') else list(next(k for k,v in self.room_states.items() if v == room_state))
                current_floor = current_pos[2]
                
                # Find rooms on the same floor that are "earlier" (closer to starting area)
                for other_room in self.room_states.values():
                    if (other_room != room_state and 
                        other_room.room_type not in ["staircase_up", "staircase_down"] and  # Don't put keys in stair rooms
                        other_room.room_type != "hallway"):  # Don't put keys in hallways
                        # Check if this room is on the same or earlier floor
                        other_pos = list(other_room.position) if hasattr(other_room, 'position') else list(next(k for k,v in self.room_states.items() if v == other_room))
                        if other_pos[2] <= current_floor:
                            key_rooms.append(other_room)
                
                # If no suitable rooms found, fall back to any non-staircase rooms
                if not key_rooms:
                    for other_room in self.room_states.values():
                        if (other_room != room_state and 
                            other_room.room_type not in ["staircase_up", "staircase_down"] and
                            other_room.room_type != "hallway"):  # Still avoid hallways for keys
                            key_rooms.append(other_room)
                
                if key_rooms:
                    key_room = random.choice(key_rooms)
                    key_item = Item(name=key_required, item_type=ItemType.KEY, value=10)
                    key_room.items.append(key_item)
                    placed_keys.add(key_required)

        # Add some blocked passages (about 5% of accessible rooms, but prefer hallways)
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
        # Handle case where there aren't enough rooms
        elif len(remaining_rooms) == 0:
            remaining_rooms = all_accessible_rooms

        selected_rooms_for_passages = random.sample(remaining_rooms, min(num_blocked_passages, len(remaining_rooms)))

        for room_state in selected_rooms_for_passages:
            room_state.blocked_passages[Direction(random.choice(["north", "south", "east", "west"]))] = random.choice(["Rune", "Powder", "Crystal", "Stone", "Charm", "Sundial", "Sunday"])
            
            # Add the item needed to clear the blocked passage to an earlier area
            # Similar logic to keys above
            trigger_items = {
                "Rune": "Power Rune",
                "Powder": "Magic Powder", 
                "Crystal": "Power Crystal",
                "Stone": "Power Stone",
                "Charm": "Power Charm",
                "Sundial": "Power Sundial",
                "Sunday": "Sunday"
            }
            trigger_needed = random.choice(["Rune", "Powder", "Crystal", "Stone", "Charm", "Sundial", "Sunday"])
            item_needed = trigger_items[trigger_needed]
            
            # Find a suitable room for the trigger item (similar to key placement)
            trigger_rooms = []
            current_pos = list(room_state.position) if hasattr(room_state, 'position') else list(next(k for k,v in self.room_states.items() if v == room_state))
            current_floor = current_pos[2]
            
            for other_room in self.room_states.values():
                if (other_room != room_state and 
                    other_room.room_type not in ["staircase_up", "staircase_down"] and
                    other_room.room_type != "hallway"):  # Don't put trigger items in hallways
                    other_pos = list(other_room.position) if hasattr(other_room, 'position') else list(next(k for k,v in self.room_states.items() if v == other_room))
                    if other_pos[2] <= current_floor:
                        trigger_rooms.append(other_room)
            
            if trigger_rooms:
                trigger_room = random.choice(trigger_rooms)
                trigger_item = Item(name=item_needed, item_type=ItemType.TRIGGER, value=5)
                trigger_room.items.append(trigger_item)

    def _create_corridor(self, x1, y1, x2, y2, floor):
        """Create an L-shaped corridor between two points"""
        # Horizontal first, then vertical
        if random.choice([True, False]):  # Random choice of L-shape orientation
            # Horizontal corridor
            min_x, max_x = min(x1, x2), max(x1, x2)
            for x in range(min_x, max_x + 1):
                pos = (x, y1, floor)
                if pos not in self.room_states:
                    # Create a hallway room state
                    room_state = RoomState(pos)
                    room_state.room_type = "hallway"
                    room_state.description = "A narrow hallway connecting different areas."
                    self.room_states[pos] = room_state

            # Vertical corridor
            min_y, max_y = min(y1, y2), max(y1, y2)
            for y in range(min_y, max_y + 1):
                pos = (x2, y, floor)
                if pos not in self.room_states:
                    # Create a hallway room state
                    room_state = RoomState(pos)
                    room_state.room_type = "hallway"
                    room_state.description = "A narrow hallway connecting different areas."
                    self.room_states[pos] = room_state
        else:
            # Vertical first, then horizontal
            # Vertical corridor
            min_y, max_y = min(y1, y2), max(y1, y2)
            for y in range(min_y, max_y + 1):
                pos = (x1, y, floor)
                if pos not in self.room_states:
                    # Create a hallway room state
                    room_state = RoomState(pos)
                    room_state.room_type = "hallway"
                    room_state.description = "A narrow hallway connecting different areas."
                    self.room_states[pos] = room_state

            # Horizontal corridor
            min_x, max_x = min(x1, x2), max(x1, x2)
            for x in range(min_x, max_x + 1):
                pos = (x, y2, floor)
                if pos not in self.room_states:
                    # Create a hallway room state
                    room_state = RoomState(pos)
                    room_state.room_type = "hallway"
                    room_state.description = "A narrow hallway connecting different areas."
                    self.room_states[pos] = room_state

    def get_room_state(self, x: int, y: int, floor: int) -> Optional[RoomState]:
        """Get the room state for a specific position."""
        return self.room_states.get((x, y, floor))

    def _generate_random_item(self) -> Item:
        """Generate a random item."""
        item_types = [
            Item("Iron Sword", ItemType.WEAPON, value=50, attack_bonus=10),
            Item("Steel Sword", ItemType.WEAPON, value=100, attack_bonus=15),
            Item("Magic Sword", ItemType.WEAPON, value=200, attack_bonus=20, status_effects={"poison": 3}),
            Item("Leather Armor", ItemType.ARMOR, value=30, defense_bonus=5),
            Item("Chain Mail", ItemType.ARMOR, value=80, defense_bonus=10),
            Item("Plate Armor", ItemType.ARMOR, value=150, defense_bonus=15),
            Item("Health Potion", ItemType.CONSUMABLE, value=20, health_bonus=30),
            Item("Strength Potion", ItemType.CONSUMABLE, value=40, attack_bonus=5),
            Item("Shield", ItemType.ARMOR, value=60, defense_bonus=8),
            Item("Dagger", ItemType.WEAPON, value=25, attack_bonus=7),
            Item("Bow", ItemType.WEAPON, value=75, attack_bonus=12),
            Item("Staff", ItemType.WEAPON, value=60, attack_bonus=8, defense_bonus=3),
            Item("Magic Ring", ItemType.ARMOR, value=100, attack_bonus=5, defense_bonus=5),
            Item("Cloak", ItemType.ARMOR, value=40, defense_bonus=3, health_bonus=10),
            Item("Boots", ItemType.ARMOR, value=35, defense_bonus=2),
            Item("Helmet", ItemType.ARMOR, value=45, defense_bonus=4),
        ]
        return random.choice(item_types)

    def _generate_random_enemy(self, floor: int) -> Entity:
        """Generate a random enemy based on floor depth."""
        # Scale enemy strength based on floor
        scale = floor + 1
        enemies = [
            Entity("Goblin", 20 * scale, 5 * scale, 2 * scale),
            Entity("Orc", 35 * scale, 8 * scale, 4 * scale),
            Entity("Skeleton", 25 * scale, 6 * scale, 3 * scale),
            Entity("Zombie", 30 * scale, 7 * scale, 2 * scale),
            Entity("Spider", 15 * scale, 6 * scale, 1 * scale),
            Entity("Ogre", 50 * scale, 12 * scale, 6 * scale),
            Entity("Demon", 60 * scale, 15 * scale, 8 * scale),
            Entity("Dragon", 100 * scale, 20 * scale, 15 * scale),
            Entity("Ghost", 40 * scale, 10 * scale, 5 * scale, speed=15),
            Entity("Troll", 70 * scale, 14 * scale, 10 * scale),
            Entity("Ancient Guardian", 80 * scale, 18 * scale, 12 * scale),
        ]
        enemy = random.choice(enemies)
        # Apply scaling
        enemy.max_health *= scale
        enemy.health *= scale
        enemy.attack *= scale
        enemy.defense *= scale
        return enemy

    class RoomInfo:
        def __init__(self, x, y, width, height, floor):
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.floor = floor
            self.center_x = x + width // 2
            self.center_y = y + height // 2


class Player(Entity):
    def __init__(self):
        super().__init__("Hero", 100, 10, 5, speed=10)
        self.level = 1
        self.exp = 0
        self.exp_to_level = 100
        self.gold = 0
        self.inventory: List[Item] = []
        self.equipped_weapon: Optional[Item] = None
        self.equipped_armor: Optional[Item] = None
        self.position: Tuple[int, int, int] = (0, 0, 0)  # x, y, floor
        self.score = 0
        self.enemies_defeated = 0
        self.treasures_collected = 0
        self.floors_explored = set()
        self.rooms_explored = set()
        self.distance_traveled = 0

    def gain_exp(self, amount: int):
        """Gain experience and potentially level up."""
        self.exp += amount
        if self.exp >= self.exp_to_level:
            self.level_up()

    def level_up(self):
        """Level up the player."""
        self.level += 1
        self.exp -= self.exp_to_level
        self.exp_to_level = int(self.exp_to_level * 1.5)  # Increase exp requirement
        
        # Improve stats
        self.max_health += 20
        self.health = self.max_health
        self.attack += 5
        self.defense += 2
        
        print(f"\n*** LEVEL UP! You are now level {self.level}! ***")

    def take_item(self, item: Item):
        """Take an item."""
        self.inventory.append(item)
        self.treasures_collected += 1
        self.score += item.value

    def equip_item(self, item: Item):
        """Equip an item."""
        if item.item_type == ItemType.WEAPON:
            if self.equipped_weapon:
                # Unequip current weapon and add back to inventory
                self.inventory.append(self.equipped_weapon)
                self.attack -= self.equipped_weapon.attack_bonus
                self.defense -= self.equipped_weapon.defense_bonus
            self.equipped_weapon = item
            self.attack += item.attack_bonus
            self.defense += item.defense_bonus
        elif item.item_type == ItemType.ARMOR:
            if self.equipped_armor:
                # Unequip current armor and add back to inventory
                self.inventory.append(self.equipped_armor)
                self.attack -= self.equipped_armor.attack_bonus
                self.defense -= self.equipped_armor.defense_bonus
                self.max_health -= self.equipped_armor.health_bonus
                self.health = min(self.health, self.max_health)  # Don't exceed max health
            self.equipped_armor = item
            self.attack += item.attack_bonus
            self.defense += item.defense_bonus
            self.max_health += item.health_bonus
            self.health = min(self.health, self.max_health)  # Heal up to new max if needed

    def unequip_item(self, item_type: str):
        """Unequip an item."""
        if item_type.lower() == "weapon" and self.equipped_weapon:
            self.inventory.append(self.equipped_weapon)
            self.attack -= self.equipped_weapon.attack_bonus
            self.defense -= self.equipped_weapon.defense_bonus
            self.equipped_weapon = None
        elif item_type.lower() == "armor" and self.equipped_armor:
            self.inventory.append(self.equipped_armor)
            self.attack -= self.equipped_armor.attack_bonus
            self.defense -= self.equipped_armor.defense_bonus
            self.max_health -= self.equipped_armor.health_bonus
            self.health = min(self.health, self.max_health)  # Don't exceed max health
            self.equipped_armor = None

    def get_total_attack(self):
        """Get total attack including equipped items."""
        total = self.attack
        if self.equipped_weapon:
            total += self.equipped_weapon.attack_bonus
        return total

    def get_total_defense(self):
        """Get total defense including equipped items."""
        total = self.defense
        if self.equipped_armor:
            total += self.equipped_armor.defense_bonus
        return total

    def get_total_health_bonus(self):
        """Get total health bonus from equipped items."""
        total = 0
        if self.equipped_armor:
            total += self.equipped_armor.health_bonus
        return total

    def travel_to(self, new_position: Tuple[int, int, int]):
        """Move to a new position and update stats."""
        old_pos = self.position
        self.position = new_position
        
        # Calculate distance traveled (Manhattan distance)
        dist = abs(new_position[0] - old_pos[0]) + abs(new_position[1] - old_pos[1]) + abs(new_position[2] - old_pos[2])
        self.distance_traveled += dist
        
        # Record explored floor and room
        self.floors_explored.add(new_position[2])
        self.rooms_explored.add(new_position)


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
            self.player.position = (0, 0, 0)

    def move_player(self, direction: Direction):
        """Move the player in a direction if possible."""
        if direction in self.current_room_state.locked_doors:
            key_name = self.current_room_state.locked_doors[direction]
            print(f"🔒 This way is locked by a magical barrier. You need a {key_name} to proceed.")
            # Check if player has the key
            for item in self.player.inventory:
                if item.name == key_name and item.item_type == ItemType.KEY:
                    print(f"✨ You use the {key_name} to unlock the magical barrier!")
                    del self.current_room_state.locked_doors[direction]
                    break
            else:
                print(f"🔑 You don't have the required key: {key_name}")
                print(f"💡 Hint: Look for {key_name}s in earlier areas of the dungeon.")
                return False

        if direction in self.current_room_state.blocked_passages:
            trigger_name = self.current_room_state.blocked_passages[direction]
            print(f"🚧 This way is blocked by ancient magic. You need a {trigger_name} to proceed.")
            # Check if player has the trigger item
            for item in self.player.inventory:
                if item.name == trigger_name:
                    print(f"✨ You use the {trigger_name} to dispel the magical blockage!")
                    del self.current_room_state.blocked_passages[direction]
                    break
            else:
                print(f"🔮 You don't have the required item: {trigger_name}")
                print(f"💡 Hint: Search for {trigger_name}s in rooms before reaching this area.")
                return False

        # Handle special directions (stairs)
        if direction == Direction.UP and self.current_room_state.has_stairs_up:
            target_pos = self.current_room_state.stairs_up_target
            if target_pos:
                self.current_room_state = self.dungeon.room_states[target_pos]
                self.player.travel_to(target_pos)
                print("⬆️  You climb up the stairs...")
                # Process monster AI after moving
                self.process_monster_ai()
                return True
        elif direction == Direction.DOWN and self.current_room_state.has_stairs_down:
            target_pos = self.current_room_state.stairs_down_target
            if target_pos:
                self.current_room_state = self.dungeon.room_states[target_pos]
                self.player.travel_to(target_pos)
                print("⬇️  You descend down the stairs...")
                # Process monster AI after moving
                self.process_monster_ai()
                return True
        elif direction in self.current_room_state.connections:
            new_pos = self.current_room_state.connections[direction]
            self.current_room_state = self.dungeon.room_states[new_pos]
            self.player.travel_to(new_pos)
            # Process monster AI after moving
            self.process_monster_ai()
            return True
        
        print(f"❌ You cannot move {direction.value}.")
        return False

    def look_around(self):
        """Look around the current room."""
        print(f"\n--- {self.current_room_state.description} ---")
        
        # Show items in the room
        if self.current_room_state.items:
            print("\nItems in the room:")
            for i, item in enumerate(self.current_room_state.items):
                print(f"  {i+1}. {item.name} (Value: {item.value})")
        else:
            print("\nNo items in this room.")
        
        # Show entities (monsters) in the room
        living_entities = [e for e in self.current_room_state.entities if e.is_alive()]
        if living_entities:
            print("\nCreatures in the room:")
            for i, entity in enumerate(living_entities):
                print(f"  {i+1}. {entity.name} (HP: {entity.health}/{entity.max_health}, Attack: {entity.attack}, Defense: {entity.defense})")
        else:
            print("\nNo creatures in this room.")
        
        # Show NPCs in the room
        if self.current_room_state.npcs:
            print("\nNPCs in the room:")
            for i, npc in enumerate(self.current_room_state.npcs):
                print(f"  {i+1}. {npc.name}")
        else:
            print("\nNo NPCs in this room.")
        
        # Show adjacent room information
        print("\nAdjacent areas:")
        for direction in Direction:
            # Check if this is a stair direction
            if direction == Direction.DOWN and getattr(self.current_room_state, 'has_stairs_down', False) and getattr(self.current_room_state, 'stairs_down_target', None):
                print(f"  📥 {direction.value.capitalize()}: stairs down to next floor")
            elif direction == Direction.UP and getattr(self.current_room_state, 'has_stairs_up', False) and getattr(self.current_room_state, 'stairs_up_target', None):
                print(f"  📤 {direction.value.capitalize()}: stairs up to previous floor")
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
                elif getattr(adj_room_state, 'room_type', '') == "artifact":
                    adj_desc = "A mystical chamber with a legendary artifact!"
                elif getattr(adj_room_state, 'room_type', '') == "npc":
                    adj_desc = "A room with a mysterious stranger."
                else:
                    adj_desc = "An empty, quiet room."
                
                print(f"  {direction.value.capitalize()}: {adj_desc}")
            elif direction in self.current_room_state.locked_doors:
                key_needed = self.current_room_state.locked_doors[direction]
                print(f"  🔒 {direction.value.capitalize()}: MAGICAL BARRIER (Need {key_needed})")
            elif direction in self.current_room_state.blocked_passages:
                trigger_needed = self.current_room_state.blocked_passages[direction]
                print(f"  🚧 {direction.value.capitalize()}: MAGIC BLOCKED (Need {trigger_needed})")
            else:
                print(f"  ❌ {direction.value.capitalize()}: blocked")

    def attack_enemy(self, enemy_index: int) -> bool:
        """Attack an enemy in the current room."""
        # Filter for living enemies only
        living_enemies = [e for e in self.current_room_state.entities if e.is_alive()]
        
        if not living_enemies:
            print("There are no enemies here to attack.")
            return False
        
        # Adjust enemy_index since the game displays enemies starting from 1
        adjusted_index = enemy_index - 1
        
        if 0 <= adjusted_index < len(living_enemies):
            enemy = living_enemies[adjusted_index]
            print(f"You attack the {enemy.name}!")
            
            # Calculate damage considering player's equipment
            player_attack = self.player.get_total_attack()
            damage_to_enemy = max(1, player_attack - enemy.defense)
            damage_taken = max(1, enemy.attack - self.player.get_total_defense())
            
            # Apply damage
            enemy_damage = enemy.take_damage(damage_to_enemy)
            self.player.take_damage(damage_taken)
            
            print(f"You deal {enemy_damage} damage to the {enemy.name}.")
            print(f"The {enemy.name} hits you for {damage_taken} damage.")
            
            # Apply status effects from equipped weapon
            if self.player.equipped_weapon:
                for effect, duration in self.player.equipped_weapon.status_effects.items():
                    if effect not in enemy.active_status_effects:
                        enemy.active_status_effects[effect] = duration
                        print(f"The {enemy.name} is affected by {effect}!")
            
            # Apply enemy status effects to player
            enemy.apply_status_effects()
            
            if not enemy.is_alive():
                print(f"You defeated the {enemy.name}!")
                self.player.gain_exp(enemy.max_health // 2)  # Gain EXP based on enemy size
                self.player.gold += random.randint(5, 20)  # Drop some gold
                self.player.enemies_defeated += 1
                self.player.score += enemy.max_health  # Score based on enemy difficulty
                # Potentially drop an item
                if random.random() < 0.3:  # 30% chance to drop an item
                    dropped_item = self.dungeon._generate_random_item()
                    self.current_room_state.items.append(dropped_item)
                    print(f"The {enemy.name} dropped: {dropped_item.name}!")
                # Process monster AI after combat
                self.process_monster_ai()
                return True
            else:
                print(f"The {enemy.name} has {enemy.health}/{enemy.max_health} HP remaining.")
                
            if not self.player.is_alive():
                print("You have been defeated...")
                return False
            
            # Process monster AI after combat
            self.process_monster_ai()
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
            print(f"You take the {item.name}.")
            self.player.take_item(item)
            self.current_room_state.items.remove(item)
            # Process monster AI after taking an item (noise might attract attention)
            self.process_monster_ai()
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
            return npc.interact(self.player)
        else:
            print("Invalid NPC selection.")
            return False

    def equip_item(self, item_index: int) -> bool:
        """Equip an item from the inventory."""
        # Adjust item_index since the game displays items starting from 1
        adjusted_index = item_index - 1
        
        if 0 <= adjusted_index < len(self.player.inventory):
            item = self.player.inventory[adjusted_index]
            # Check if it's equippable
            if item.item_type in [ItemType.WEAPON, ItemType.ARMOR]:
                self.player.equip_item(item)
                self.player.inventory.remove(item)
                print(f"You equipped the {item.name}.")
                return True
            else:
                print(f"You cannot equip the {item.name}.")
                return False
        else:
            print("Invalid item selection.")
            return False

    def unequip_item(self, item_type: str) -> bool:
        """Unequip an item."""
        if item_type.lower() not in ["weapon", "armor"]:
            print("Please specify a valid item type to unequip: 'weapon' or 'armor'.")
            return False
        
        if (item_type.lower() == "weapon" and not self.player.equipped_weapon) or \
           (item_type.lower() == "armor" and not self.player.equipped_armor):
            print(f"You don't have a {item_type.lower()} equipped.")
            return False
        
        self.player.unequip_item(item_type.lower())
        print(f"You unequipped your {item_type.lower()}.")
        return True

    def _is_in_line_of_sight(self, pos1: Tuple[int, int, int], pos2: Tuple[int, int, int]) -> bool:
        """Check if there's a clear line of sight between two positions (same floor)."""
        if pos1[2] != pos2[2]:  # Different floors
            return False
            
        x1, y1, z1 = pos1
        x2, y2, z2 = pos2
        
        # Check if they're on the same floor and within reasonable distance
        distance = abs(x2 - x1) + abs(y2 - y1)
        if distance > 10:  # Limit line of sight to 10 tiles
            return False
            
        # Use a simple ray-casting algorithm for line of sight
        # Check each cell along the straight line between pos1 and pos2
        dx = x2 - x1
        dy = y2 - y1
        
        # Number of steps is the maximum of the differences
        steps = max(abs(dx), abs(dy))
        
        if steps == 0:
            return True  # Same position
            
        # Calculate increments
        x_inc = dx / steps
        y_inc = dy / steps
        
        # Check each point along the line
        for i in range(int(steps) + 1):
            x = round(x1 + x_inc * i)
            y = round(y1 + y_inc * i)
            current_pos = (x, y, z1)
            
            # If this position doesn't exist in the dungeon, there's no line of sight
            if current_pos not in self.dungeon.room_states:
                return False
                
            # If we've reached the destination, continue checking
            if current_pos == pos2:
                continue
                
        # If we've made it through all intermediate positions without hitting a wall, there's line of sight
        return True

    def _get_adjacent_positions(self, pos: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
        """Get all valid adjacent positions from a given position."""
        x, y, z = pos
        adjacent = []
        
        # Check all four directions
        for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:  # North, South, East, West
            new_pos = (x + dx, y + dy, z)
            if new_pos in self.dungeon.room_states:
                adjacent.append(new_pos)
                
        return adjacent

    def _move_monster_towards_player(self, monster_entity, current_room, monster_pos):
        """Move a monster toward the player if in line of sight."""
        player_pos = self.player.position
        
        # Check if monster can see player
        if self._is_in_line_of_sight(monster_pos, player_pos):
            # Find shortest path to player using simple BFS-like approach
            visited = set()
            queue = [monster_pos]
            visited.add(monster_pos)
            predecessors = {monster_pos: None}
            
            # Search for player position up to a certain depth
            max_depth = 8  # Don't search too far
            depth = 0
            found_path = False
            
            while queue and depth < max_depth:
                next_queue = []
                
                for pos in queue:
                    if pos == player_pos:
                        found_path = True
                        break
                        
                    # Check adjacent positions
                    for next_pos in self._get_adjacent_positions(pos):
                        if next_pos not in visited:
                            visited.add(next_pos)
                            predecessors[next_pos] = pos
                            next_queue.append(next_pos)
                            
                if found_path:
                    break
                    
                queue = next_queue
                depth += 1
            
            # If path found, move monster one step toward player
            if found_path and player_pos in predecessors:
                # Reconstruct path back to find next step
                current = player_pos
                path = []
                while current is not None:
                    path.append(current)
                    current = predecessors.get(current)
                
                path.reverse()
                
                # Move monster to the next position in the path (skip current position)
                if len(path) > 1:
                    next_pos = path[1]  # First step after current position
                    
                    # Only move if the next position is different from current
                    if next_pos != monster_pos:
                        # Move the monster to the new room
                        new_room = self.dungeon.room_states[next_pos]
                        
                        # Remove monster from current room only if it's still there
                        # This check is crucial to prevent double-removal
                        if monster_entity in current_room.entities:
                            current_room.entities.remove(monster_entity)
                        
                        # Add monster to new room only if it's not already there
                        if monster_entity not in new_room.entities:
                            new_room.entities.append(monster_entity)
                        
                        return True  # Successfully moved
                    
        return False  # No movement occurred

    def process_monster_ai(self):
        """Process AI for all monsters in the dungeon."""
        player_pos = self.player.position
        
        # Create a list of all monsters to move to avoid issues with modifying lists during iteration
        monsters_to_process = []
        
        # First, collect all monsters with their current room and position
        for pos, room in self.dungeon.room_states.items():
            living_monsters = [entity for entity in room.entities if entity.is_alive() and entity.name != "Player"]
            for monster in living_monsters:
                monsters_to_process.append((monster, room, pos))
        
        # Now process each monster
        for monster, room, pos in monsters_to_process:
            # Only process if the monster is still in this room (hasn't been moved by another monster's movement)
            if monster in room.entities:
                self._move_monster_towards_player(monster, room, pos)

    def show_inventory(self):
        """Show player's inventory."""
        print("\n--- Inventory ---")
        if not self.player.inventory:
            print("Your inventory is empty.")
        else:
            for i, item in enumerate(self.player.inventory):
                status = ""
                if item == self.player.equipped_weapon:
                    status = " [equipped as weapon]"
                elif item == self.player.equipped_armor:
                    status = " [equipped as armor]"
                print(f"{i+1}. {item.name}{status}")

    def show_stats(self):
        """Show player's stats."""
        print("\n--- 🦸 Hero's Stats ---")
        print(f"Level: {self.player.level}")
        print(f"HP: {self.player.health}/{self.player.max_health + self.player.get_total_health_bonus()}")
        print(f"Attack: {self.player.get_total_attack()}")
        print(f"Defense: {self.player.get_total_defense()}")
        print(f"EXP: {self.player.exp}/{self.player.exp_to_level}")
        print(f"Gold: {self.player.gold}")
        print(f"Position: Floor {self.player.position[2] + 1}, ({self.player.position[0]}, {self.player.position[1]})")
        print(f"Score: {self.player.score}")
        print(f"Enemies Defeated: {self.player.enemies_defeated}")
        print(f"Treasures Collected: {self.player.treasures_collected}")
        print(f"Floors Explored: {len(self.player.floors_explored)}")
        print(f"Rooms Explored: {len(self.player.rooms_explored)}")
        print(f"Distance Traveled: {self.player.distance_traveled}")
        
        weapon_name = self.player.equipped_weapon.name if self.player.equipped_weapon else "None"
        armor_name = self.player.equipped_armor.name if self.player.equipped_armor else "None"
        print(f"Weapon: {weapon_name} equipped")
        print(f"Armor: {armor_name} equipped")
        
        # Additional helpful information
        if self.player.position[2] == self.dungeon.floors - 1:
            print(f"🎯 You are on the deepest floor! Look for the Artifact of Power.")
        else:
            print(f"🧭 Explore deeper to find stairs leading down.")
        
        # Show number of keys in inventory
        keys_in_inv = [item for item in self.player.inventory if item.item_type == ItemType.KEY]
        if keys_in_inv:
            key_names = [key.name for key in keys_in_inv]
            print(f"🔑 Keys in inventory: {', '.join(key_names)}")
        
        # Show number of trigger items in inventory
        triggers_in_inv = [item for item in self.player.inventory if item.item_type == ItemType.TRIGGER]
        if triggers_in_inv:
            trigger_names = [trigger.name for trigger in triggers_in_inv]
            print(f"🔮 Magical items: {', '.join(trigger_names)}")

    def rest(self):
        """Rest to recover health."""
        recovery = self.player.max_health // 4  # Recover 25% of max health
        self.player.health = min(self.player.max_health + self.player.get_total_health_bonus(), self.player.health + recovery)
        print(f"You rest and recover {recovery} HP. Current HP: {self.player.health}/{self.player.max_health + self.player.get_total_health_bonus()}.")

    def save_game(self, filename: str = "savegame.json"):
        """Save the game state to a file."""
        game_state = {
            "player": {
                "name": self.player.name,
                "level": self.player.level,
                "health": self.player.health,
                "max_health": self.player.max_health,
                "attack": self.player.attack,
                "defense": self.player.defense,
                "exp": self.player.exp,
                "exp_to_level": self.player.exp_to_level,
                "gold": self.player.gold,
                "position": self.player.position,
                "score": self.player.score,
                "enemies_defeated": self.player.enemies_defeated,
                "treasures_collected": self.player.treasures_collected,
                "floors_explored": list(self.player.floors_explored),
                "rooms_explored": list(self.player.rooms_explored),
                "distance_traveled": self.player.distance_traveled,
                "inventory": [
                    {"name": item.name, "type": item.item_type.value, "value": item.value,
                     "attack_bonus": item.attack_bonus, "defense_bonus": item.defense_bonus,
                     "health_bonus": item.health_bonus, "status_effects": item.status_effects}
                    for item in self.player.inventory
                ],
                "equipped_weapon": self.player.equipped_weapon.name if self.player.equipped_weapon else None,
                "equipped_armor": self.player.equipped_armor.name if self.player.equipped_armor else None
            },
            "dungeon_seed": self.dungeon.seed,
            "current_room_position": self.player.position  # Save the current room position
        }
        
        with open(filename, 'w') as f:
            json.dump(game_state, f, indent=2)

    def load_game(self, filename: str = "savegame.json") -> bool:
        """Load the game state from a file."""
        try:
            with open(filename, 'r') as f:
                game_state = json.load(f)
            
            # Restore player state (handle both old and new save formats)
            self.player.level = game_state["player"]["level"]
            self.player.health = game_state["player"]["health"]
            self.player.max_health = game_state["player"]["max_health"]
            self.player.attack = game_state["player"]["attack"]
            self.player.defense = game_state["player"]["defense"]
            
            # Handle both old and new experience key names
            if "exp" in game_state["player"]:
                self.player.exp = game_state["player"]["exp"]
            elif "experience" in game_state["player"]:
                self.player.exp = game_state["player"]["experience"]
            else:
                self.player.exp = 0
            
            if "exp_to_level" in game_state["player"]:
                self.player.exp_to_level = game_state["player"]["exp_to_level"]
            elif "experience_to_next_level" in game_state["player"]:
                self.player.exp_to_level = game_state["player"]["experience_to_next_level"]
            else:
                self.player.exp_to_level = 100
            
            self.player.gold = game_state["player"]["gold"]
            self.player.position = tuple(game_state["player"]["position"])
            self.player.score = game_state["player"]["score"]
            self.player.enemies_defeated = game_state["player"]["enemies_defeated"]
            self.player.treasures_collected = game_state["player"]["treasures_collected"]
            self.player.floors_explored = set(game_state["player"]["floors_explored"])
            self.player.rooms_explored = set(tuple(pos) if isinstance(pos, list) else pos for pos in game_state["player"]["rooms_explored"])
            self.player.distance_traveled = game_state["player"]["distance_traveled"]
            
            # Restore inventory
            self.player.inventory = []
            for item_data in game_state["player"]["inventory"]:
                item_type = ItemType(item_data["type"])
                item = Item(
                    name=item_data["name"],
                    item_type=item_type,
                    value=item_data["value"],
                    attack_bonus=item_data["attack_bonus"],
                    defense_bonus=item_data["defense_bonus"],
                    health_bonus=item_data["health_bonus"],
                    status_effects=item_data["status_effects"]
                )
                self.player.inventory.append(item)
            
            # Restore equipped items
            if game_state["player"]["equipped_weapon"]:
                for item in self.player.inventory:
                    if item.name == game_state["player"]["equipped_weapon"]:
                        self.player.equipped_weapon = item
                        self.player.inventory.remove(item)
                        break
            
            if game_state["player"]["equipped_armor"]:
                for item in self.player.inventory:
                    if item.name == game_state["player"]["equipped_armor"]:
                        self.player.equipped_armor = item
                        self.player.inventory.remove(item)
                        break
            
            # Handle both old and new dungeon formats
            if "dungeon_seed" in game_state:
                # New format - regenerate dungeon with the same seed
                self.dungeon = SeededDungeon(seed=game_state["dungeon_seed"])
                # Set current room based on saved position
                self.player.position = tuple(game_state["player"]["position"])
                self.current_room_state = self.dungeon.get_room_state(*self.player.position)
            elif "dungeon" in game_state:
                # Old format - regenerate dungeon with a new seed
                # Since we can't recreate the exact same dungeon from the old format,
                # we'll create a new one but find a suitable starting position
                seed = random.randint(0, 1000000)
                self.dungeon = SeededDungeon(seed=seed)
                # Find a suitable starting room in the new dungeon
                # Look for a room without stairs down to start in
                starting_pos = None
                for pos, room_state in self.dungeon.room_states.items():
                    if not getattr(room_state, 'has_stairs_down', False):
                        starting_pos = pos
                        self.current_room_state = room_state
                        break
                else:
                    # If no suitable room found, default to (0, 0, 0)
                    starting_pos = (0, 0, 0)
                    self.current_room_state = self.dungeon.get_room_state(0, 0, 0)
                
                self.player.position = starting_pos
            
            # Ensure current_room_state exists (fallback if position not found)
            if self.current_room_state is None:
                # Find a suitable room to start in
                for pos, room_state in self.dungeon.room_states.items():
                    if not getattr(room_state, 'has_stairs_down', False):
                        self.current_room_state = room_state
                        self.player.position = pos
                        break
                else:
                    # Default fallback
                    self.current_room_state = self.dungeon.get_room_state(0, 0, 0)
                    self.player.position = (0, 0, 0)
            
            print("Game loaded successfully!")
            return True
        except FileNotFoundError:
            print("No save file found.")
            return False
        except Exception as e:
            print(f"Error loading game: {e}")
            return False

    def visualize_floor(self, floor_num=None):
        """Visualize the current floor of the dungeon."""
        if floor_num is None:
            # Get current floor from player position
            current_floor = self.player.position[2]
        else:
            current_floor = floor_num
        
        print(f"\n--- FLOOR {current_floor + 1} VISUALIZATION (Seed: {self.dungeon.seed}) ---")
        
        # Create a grid representation of the floor
        grid = [[' ' for _ in range(self.dungeon.width)] for _ in range(self.dungeon.height)]
        
        # Mark rooms and special features on the grid
        for (x, y, f), room_state in self.dungeon.room_states.items():
            if f == current_floor:
                # Determine symbol based on room properties
                symbol = self._get_symbol_for_room_state(room_state, x, y, current_floor)
                if 0 <= x < self.dungeon.width and 0 <= y < self.dungeon.height:
                    grid[y][x] = symbol
        
        # Print the grid
        for row in grid:
            print(''.join(row))
        
        # Print legend
        print("\nLegend:")
        print("  . = Empty Room")
        print("  - = Hallway")
        print("  $ = Treasure Room")
        print("  M = Monster Room")
        print("  T = Trap Room")
        print("  N = NPC Room")
        print("  A = Artifact Room")
        print("  S = Staircase Room")
        print("  @ = Player Position")
        print("  # = Locked Door")
        print("  % = Blocked Passage")

    def _get_symbol_for_room_state(self, room_state, x, y, floor):
        """Get a symbol for a room state."""
        # Check if this position is the player's position
        if self.player.position == (x, y, floor):
            return '@'  # Player position
        
        # Check for locked doors and blocked passages first (these are special features that override room type)
        if len(room_state.locked_doors) > 0:
            return '#'  # Locked door (takes precedence over room type)
        elif len(room_state.blocked_passages) > 0:
            return '%'  # Blocked passage (takes precedence over room type)
        
        # Check for stairs next (also special features)
        if getattr(room_state, 'has_stairs_up', False) or getattr(room_state, 'has_stairs_down', False):
            return 'S'  # Staircase room (takes precedence over basic room types)
        
        # Check for special room types
        if room_state.room_type == "artifact":
            return 'A'
        elif room_state.room_type == "treasure":
            return '$'
        elif room_state.room_type == "monster":
            return 'M'
        elif room_state.room_type == "trap":
            return 'T'
        elif room_state.room_type == "npc":
            return 'N'
        elif room_state.room_type == "hallway":
            return '-'  # Only show as hallway if no obstacles
        elif room_state.room_type == "staircase_up" or room_state.room_type == "staircase_down":
            return 'S'  # Staircase room
        else:
            # Default room symbol
            return '.'


def main():
    import sys
    
    print("=== TERMINAL DUNGEON CRAWLER (SEED-BASED) ===")
    print(f"Dungeon Seed: {random.randint(0, 1000000)}")
    print("Current Status:")
    
    # Check if a command was provided as an argument
    args = sys.argv[1:]  # Exclude script name
    
    # Initialize game (try to load if exists, otherwise start new)
    game = SeededGameEngine()
    loaded = game.load_game()  # Attempt to load existing game, returns True if successful
    
    # If no save was found, we have a new game with random dungeon
    # If save was loaded, we have the saved state
    
    if not args:
        # Interactive mode
        print("\nCommands:")
        print("  move <direction> - Move north, south, east, west, up, or down")
        print("  attack <number> - Attack enemy number in room")
        print("  take <number> - Take item number from room")
        print("  equip <number> - Equip item number from inventory")
        print("  unequip <weapon|armor> - Unequip weapon or armor")
        print("  talk <number> - Talk to NPC number in room")
        print("  look - Look around the current room")
        print("  inventory - View your inventory")
        print("  stats - View your character stats")
        print("  map - Visualize the current floor of the dungeon")
        print("  map <number> - Visualize a specific floor of the dungeon")
        print("  help/hints - Show helpful tips and hints")
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
        return
    
    # Process command
    command = ' '.join(args).strip().lower()
    
    if command == "quit":
        pass
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
        print("Game saved!")
    elif command == "load":
        game.load_game()
    elif command == "help" or command == "hints":
        print("\n📖 HELP & HINTS:")
        print("• Explore all directions to find items, enemies, and stairs")
        print("• Look for keys (🔑) to unlock magical barriers (🔒)")
        print("• Find trigger items (🔮) to clear magical blocks (🚧)")
        print("• Equip weapons and armor to improve your stats")
        print("• Defeat enemies to gain experience and treasures")
        print("• Talk to NPCs to get quests and rewards")
        print("• Navigate deeper floors to find better treasures")
        print("• Your goal: Reach the deepest floor and find the Artifact of Power!")
        print("• Use 'map' to visualize the current floor layout")
        print("• Use 'stats' to check your progress and inventory")
    elif command == "map" or command.startswith("map "):
        # Handle map command - can be just 'map' for current floor or 'map <floor>' for specific floor
        if command == "map":
            # Visualize current floor
            game.visualize_floor()
        else:
            # Extract floor number from command like "map 1"
            try:
                floor_arg = command.split()[1]
                floor_num = int(floor_arg) - 1  # Convert to 0-based indexing
                game.visualize_floor(floor_num)
            except (ValueError, IndexError):
                print("Invalid floor number. Use 'map' for current floor or 'map <number>' for specific floor.")
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
    else:
        print("Unknown command. Type 'help' for available commands.")


if __name__ == "__main__":
    main()