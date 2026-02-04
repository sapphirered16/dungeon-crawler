"""World-related classes for the dungeon crawler game."""

from enum import Enum
from typing import Dict, List, Optional, Tuple
import random
from .entities.enemy import Enemy
from .items import Item


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    UP = "up"
    DOWN = "down"


class Room:
    def __init__(self, x: int, y: int, floor: int):
        self.x = x
        self.y = y
        self.floor = floor
        self.entities: List['Entity'] = []
        self.items: List[Item] = []
        self.connections: Dict[Direction, 'Room'] = {}
        self.room_type = "normal"
        self.description = self._generate_description()
        
        # For stairs between floors
        self.has_stairs_down = False
        self.has_stairs_up = False
        self.stairs_down_target: Optional['Room'] = None
        self.stairs_up_target: Optional['Room'] = None
        
        # For locked doors and blocked passages
        self.locked_doors: Dict[Direction, str] = {}  # Direction -> key name needed
        self.blocked_passages: Dict[Direction, str] = {}  # Direction -> trigger item needed
        # Track permanently unlocked doors and activated passages
        self.unlocked_doors: set = set()
        self.activated_passages: set = set()

    def _generate_description(self) -> str:
        """Generate a description for the room."""
        descriptions = [
            "A dark, damp chamber.",
            "An empty, quiet room.",
            "A dusty, abandoned area.",
            "A narrow corridor.",
            "A spacious hall.",
            "A cramped space.",
            "A musty-smelling chamber.",
            "A cold stone room.",
            "A warm, well-lit area.",
            "A drafty, echoing hall.",
            "A treasure room filled with gleaming objects.",
            "A room with hostile creatures lurks ahead.",
            "A room with both hostile creatures and treasures!",
        ]
        return random.choice(descriptions)

    @property
    def position(self) -> Tuple[int, int, int]:
        return (self.x, self.y, self.floor)

    def add_connection(self, direction: Direction, room: 'Room'):
        """Add a connection to another room."""
        self.connections[direction] = room
        # Also add reverse connection if it's a cardinal direction
        if direction in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
            opposite_directions = {
                Direction.NORTH: Direction.SOUTH,
                Direction.SOUTH: Direction.NORTH,
                Direction.EAST: Direction.WEST,
                Direction.WEST: Direction.EAST
            }
            room.connections[opposite_directions[direction]] = self


class Dungeon:
    def __init__(self, width: int = 20, height: int = 20, floors: int = 3):
        self.width = width
        self.height = height
        self.floors = floors
        self.rooms: Dict[Tuple[int, int, int], Room] = {}  # (x, y, floor) -> Room
        self.generate_dungeon()

    def generate_dungeon(self):
        """Generate the dungeon with rooms and connections."""
        # Create rooms in a grid pattern
        for floor in range(self.floors):
            for x in range(self.width):
                for y in range(self.height):
                    # Only create a room in about 70% of positions to create more interesting layouts
                    if random.random() < 0.7:
                        room = Room(x, y, floor)
                        self.rooms[(x, y, floor)] = room

        # Connect adjacent rooms
        for pos, room in self.rooms.items():
            x, y, floor = pos
            
            # Try connecting to adjacent rooms
            potential_connections = [
                (x + 1, y, floor, Direction.EAST),
                (x - 1, y, floor, Direction.WEST),
                (x, y + 1, floor, Direction.NORTH),
                (x, y - 1, floor, Direction.SOUTH),
            ]
            
            for new_x, new_y, new_floor, direction in potential_connections:
                if (new_x, new_y, new_floor) in self.rooms:
                    if direction not in room.connections:  # Don't duplicate connections
                        room.add_connection(direction, self.rooms[(new_x, new_y, new_floor)])

        # Add stairs between floors in a few locations
        for floor in range(self.floors - 1):
            # Place 2-3 staircases between each floor
            num_stairs = random.randint(2, 3)
            for _ in range(num_stairs):
                # Find a room on the current floor
                current_floor_rooms = [(pos, room) for pos, room in self.rooms.items() if pos[2] == floor]
                if current_floor_rooms:
                    pos, room = random.choice(current_floor_rooms)
                    x, y, f = pos
                    
                    # Find a room on the next floor
                    next_floor_rooms = [(pos, room) for pos, room in self.rooms.items() if pos[2] == floor + 1]
                    if next_floor_rooms:
                        next_pos, next_room = random.choice(next_floor_rooms)
                        nx, ny, nf = next_pos
                        
                        # Add stairs connection
                        room.has_stairs_down = True
                        next_room.has_stairs_up = True
                        room.stairs_down_target = next_room
                        next_room.stairs_up_target = room

        # Add some enemies and items to rooms
        for room in self.rooms.values():
            # Add enemies (about 20% chance)
            if random.random() < 0.2:
                enemy_types = [
                    ("Goblin", 20, 5, 2, 15, 2, 5),
                    ("Zombie", 30, 6, 3, 20, 1, 6),
                    ("Orc", 40, 8, 4, 30, 3, 8),
                    ("Skeleton", 25, 7, 2, 18, 1, 5),
                    ("Spider", 15, 4, 1, 12, 1, 3),
                    ("Dragon", 100, 15, 8, 100, 5, 15),
                ]
                enemy_data = random.choice(enemy_types)
                enemy = Enemy(
                    name=enemy_data[0],
                    health=enemy_data[1],
                    attack=enemy_data[2],
                    defense=enemy_data[3],
                    exp_reward=enemy_data[4],
                    gold_min=enemy_data[5],
                    gold_max=enemy_data[6]
                )
                room.entities.append(enemy)
            
            # Add items (about 30% chance)
            if random.random() < 0.3:
                item_chance = random.random()
                if item_chance < 0.6:  # 60% of item rooms have 1 item
                    num_items = 1
                elif item_chance < 0.9:  # 30% of item rooms have 2 items
                    num_items = 2
                else:  # 10% of item rooms have 3 items
                    num_items = 3
                
                for _ in range(num_items):
                    item_types = [
                        ("Health Potion", 5, 0, 0, 10),
                        ("Strength Potion", 3, 5, 0, 0),
                        ("Toughness Potion", 3, 0, 5, 0),
                        ("Old Sword", 15, 3, 1, 0),
                        ("Rusty Shield", 12, 0, 2, 5),
                        ("Magic Ring", 20, 2, 2, 3),
                        ("Leather Armor", 18, 0, 3, 10),
                        ("Gold Coin", 1, 0, 0, 0),
                        ("Ancient Key", 10, 0, 0, 0),
                        ("Iron Key", 10, 0, 0, 0),
                        ("Energy Orb", 8, 0, 0, 0),
                        ("Power Crystal", 8, 0, 0, 0),
                    ]
                    item_data = random.choice(item_types)
                    from .items import ItemType
                    # Determine item type based on name
                    if "Key" in item_data[0]:
                        item_type = ItemType.KEY
                    elif "Orb" in item_data[0] or "Crystal" in item_data[0] or "Rune" in item_data[0]:
                        item_type = ItemType.TRIGGER
                    elif "Potion" in item_data[0]:
                        item_type = ItemType.CONSUMABLE
                    elif "Sword" in item_data[0] or "Ring" in item_data[0]:
                        item_type = ItemType.WEAPON
                    elif "Shield" in item_data[0] or "Armor" in item_data[0]:
                        item_type = ItemType.ARMOR
                    else:
                        item_type = ItemType.CONSUMABLE
                    
                    item = Item(
                        name=item_data[0],
                        item_type=item_type,
                        value=item_data[1],
                        attack_bonus=item_data[2],
                        defense_bonus=item_data[3],
                        health_bonus=item_data[4]
                    )
                    room.items.append(item)

        # Add locked doors and blocked passages for puzzle elements
        all_accessible_rooms = [room for room in self.rooms.values() if len(room.connections) > 0]
        
        # Add some locked doors (about 10% of accessible rooms)
        num_locked_doors = max(1, len(all_accessible_rooms) // 10)
        selected_rooms_for_doors = random.sample(all_accessible_rooms, min(num_locked_doors, len(all_accessible_rooms)))
        
        # Keep track of placed keys to ensure accessibility
        placed_keys = set()
        
        for room in selected_rooms_for_doors:
            # Find a direction that has a connection but isn't stairs
            available_directions = []
            for direction, connected_room in room.connections.items():
                # Don't lock stair directions
                if not ((direction == Direction.UP and room.has_stairs_up) or 
                       (direction == Direction.DOWN and room.has_stairs_down)):
                    available_directions.append(direction)
            
            if available_directions:
                direction_to_lock = random.choice(available_directions)
                # Add locked door - require a specific key type
                key_types = ["Iron Key", "Silver Key", "Golden Key", "Ancient Key", "Crystal Key"]
                key_required = random.choice(key_types)
                room.locked_doors[direction_to_lock] = key_required
                
                # Add the corresponding key to some other room in the dungeon
                # Find a random room that's not the same room
                other_rooms = [r for r in all_accessible_rooms if r != room]
                if other_rooms:
                    key_room = random.choice(other_rooms)
                    from .items import ItemType, Item
                    key_item = Item(name=key_required, item_type=ItemType.KEY, value=10)
                    key_room.items.append(key_item)
                    placed_keys.add(key_required)

        # Add some blocked passages (about 5% of accessible rooms)
        num_blocked_passages = max(1, len(all_accessible_rooms) // 20)
        # Select from remaining rooms that don't already have locked doors
        remaining_rooms = [room for room in selected_rooms_for_doors if len(room.locked_doors) == 0]
        if len(remaining_rooms) < num_blocked_passages:
            # Add more rooms if needed
            additional_rooms = [room for room in all_accessible_rooms if room not in selected_rooms_for_doors]
            num_additional_needed = num_blocked_passages - len(remaining_rooms)
            if num_additional_needed > 0 and len(additional_rooms) > 0:
                num_to_select = min(num_additional_needed, len(additional_rooms))
                additional_selected = random.sample(additional_rooms, num_to_select)
                remaining_rooms.extend(additional_selected)
        
        selected_rooms_for_passages = random.sample(remaining_rooms, min(num_blocked_passages, len(remaining_rooms)))
        
        # Keep track of placed trigger items
        placed_triggers = set()
        
        for room in selected_rooms_for_passages:
            # Find a direction that has a connection
            available_directions = [d for d in room.connections.keys() 
                                  if not ((d == Direction.UP and room.has_stairs_up) or 
                                         (d == Direction.DOWN and room.has_stairs_down))]
            
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
                room.blocked_passages[direction_to_block] = trigger_name
                
                # Add the corresponding trigger item to some other room in the dungeon
                other_rooms = [r for r in all_accessible_rooms if r != room]
                if other_rooms:
                    trigger_room = random.choice(other_rooms)
                    from .items import ItemType, Item
                    # For "Sunday", use a special trigger item; others use TRIGGER type
                    if trigger_required == "Sunday":
                        trigger_item = Item(name=trigger_name, item_type=ItemType.TRIGGER, value=5)
                    else:
                        trigger_item = Item(name=trigger_name, item_type=ItemType.TRIGGER, value=5)
                    trigger_room.items.append(trigger_item)
                    placed_triggers.add(trigger_name)

    def get_room(self, x: int, y: int, floor: int) -> Optional[Room]:
        """Get a room at the specified coordinates."""
        return self.rooms.get((x, y, floor))

    def get_adjacent_rooms(self, x: int, y: int, floor: int) -> Dict[Direction, Room]:
        """Get adjacent rooms to the specified coordinates."""
        room = self.get_room(x, y, floor)
        if not room:
            return {}
        return room.connections.copy()