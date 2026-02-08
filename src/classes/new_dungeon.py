"""New dungeon class with proper room-based layouts for the dungeon crawler game."""

import random
import sys
import os
from typing import Dict, List, Tuple, Any, Set

# Add the parent directory to the path for imports
current_dir = os.path.dirname(__file__)
parent_dir = os.path.join(current_dir, '..')
grandparent_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, os.path.abspath(grandparent_dir))

from src.classes.room import RoomState
from src.classes.item import Item
from src.classes.base import ItemType, Direction
from src.classes.map_effects import MapEffect, MapEffectType, MapEffectManager

# Import data loader from the data module
try:
    from src.data.data_loader import DataProvider
except ImportError:
    # Fallback for when running in a different context
    from ..data.data_loader import DataProvider


class Stair:
    """Represents a single-tile stair for floor transitions."""
    def __init__(self, position: Tuple[int, int, int], direction: Direction, connects_to: Tuple[int, int, int]):
        self.position = position  # (x, y, z) position of the stair
        self.direction = direction  # UP or DOWN direction
        self.connects_to = connects_to  # (x, y, z) target position when used
        self.symbol = '↑' if direction == Direction.UP else '↓'  # Visual symbol
        self.name = f"Stone Stairs {direction.value.upper()}"  # Display name
        self.value = 0  # Stairs have no value
        self.item_type = None  # Stairs aren't regular items
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stair to dictionary for saving."""
        return {
            'position': self.position,
            'direction': self.direction.value,
            'connects_to': self.connects_to,
            'symbol': self.symbol,
            'name': self.name,
            'value': self.value,
            'item_type': 'trigger'  # Include item_type so loading doesn't fail
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Stair':
        """Create stair from dictionary for loading."""
        stair = cls(
            position=tuple(data['position']),
            direction=Direction(data['direction']),
            connects_to=tuple(data['connects_to'])
        )
        stair.name = data.get('name', f"Stone Stairs {data['direction'].upper()}")
        stair.value = data.get('value', 0)
        # Don't set item_type attribute since stairs aren't regular items
        return stair


class Room:
    """Represents a room with actual dimensions and position."""
    def __init__(self, x: int, y: int, z: int, width: int, height: int, room_type: str):
        self.x = x  # Top-left corner x coordinate
        self.y = y  # Top-left corner y coordinate
        self.z = z  # Floor number
        self.width = width
        self.height = height
        self.room_type = room_type
        self.description = ""
        self.items = []
        self.entities = []
        self.npcs = []
        self.locked_doors = {}
        self.blocked_passages = {}
        self.has_stairs_up = False
        self.has_stairs_down = False
        self.stairs_up_target = None
        self.stairs_down_target = None
        self.connections = {}  # Direction -> (x, y, z) of connected room
    
    def contains_position(self, x: int, y: int) -> bool:
        """Check if the given coordinates are inside this room."""
        return (self.x <= x < self.x + self.width and 
                self.y <= y < self.y + self.height)
    
    def get_center(self) -> Tuple[int, int, int]:
        """Get the center position of the room."""
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        return (center_x, center_y, self.z)
    
    def get_all_positions(self) -> List[Tuple[int, int]]:
        """Get all positions within this room."""
        positions = []
        for x in range(self.x, self.x + self.width):
            for y in range(self.y, self.y + self.height):
                positions.append((x, y))
        return positions


class GridCell:
    """Represents a single cell in the dungeon grid."""
    def __init__(self, cell_type='empty'):
        self.cell_type = cell_type  # 'empty', 'room', 'hallway', 'wall'
        self.room_ref = None  # Reference to the room object if this cell is part of a room
        self.items = []  # Items placed on this specific tile
        self.locked_doors = {}  # Locked doors in this cell: {direction: key_name}
        self.blocked_passages = {}  # Blocked passages in this cell: {direction: trigger_name}
        self.has_map_effect = False
        self.map_effect = None


class SeededDungeon:
    def __init__(self, seed: int = None, grid_width: int = 25, grid_height: int = 25):
        if seed is not None:
            random.seed(seed)
        self.seed = seed
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.rooms = []  # List of Room objects
        self.grid = {}  # {(x, y, z): GridCell} - represents the actual dungeon grid
        self.map_effects = MapEffectManager()
        self.data_provider = DataProvider()
        self.generate_dungeon()

    def generate_dungeon(self):
        """Generate the dungeon layout with proper rooms and hallways."""
        # Load room templates
        room_templates = self.data_provider.get_room_templates()
        
        # Determine number of floors based on room templates
        num_floors = self._determine_number_of_floors(room_templates)
        
        # Generate rooms for multiple floors
        for floor in range(num_floors):
            self._generate_floor(floor)
        
        # Ensure stairs are properly connected between all floors
        self._connect_stairs_properly()
        
        # Add special features including obstacles with logical progression
        for floor in range(num_floors):
            self._add_special_features(floor)
        
        # After all rooms and obstacles are placed, populate them with items and entities
        self._populate_all_rooms()

    def _determine_number_of_floors(self, room_templates):
        """Determine number of floors based on room template constraints and content diversity."""
        # Handle both dictionary and list formats for room templates
        if isinstance(room_templates, dict) and 'room_templates' in room_templates:
            # Dictionary format: {'room_templates': [...]}
            actual_templates = room_templates['room_templates']
        elif isinstance(room_templates, list):
            # List format: [...]
            actual_templates = room_templates
        else:
            # Default to empty list if format is unexpected
            actual_templates = []
        
        # Count different room types
        room_types = set()
        all_themes = set()
        
        for template in actual_templates:
            if "type" in template:
                room_types.add(template["type"])
            if "themes" in template and isinstance(template["themes"], list):
                all_themes.update(template["themes"])
        
        # Based on the diversity of content, suggest an appropriate number of floors
        content_diversity_score = len(room_types) + len(all_themes)
        
        # Calculate suggested floor count based on content diversity
        if content_diversity_score >= 10:
            suggested_floors = 7  # High diversity supports more floors
        elif content_diversity_score >= 7:
            suggested_floors = 5  # Medium diversity supports moderate floors
        elif content_diversity_score >= 4:
            suggested_floors = 3  # Lower diversity suggests fewer floors
        else:
            suggested_floors = 3  # Minimum recommended
        
        # Additionally, check enemy data for level progression suggestions
        enemy_types_count = len(self.data_provider.get_enemies())
        if enemy_types_count > 10:
            # More enemy types suggest a longer dungeon progression
            suggested_floors = max(suggested_floors, 5)
        elif enemy_types_count > 5:
            suggested_floors = max(suggested_floors, 4)
        
        # Limit to reasonable bounds
        suggested_floors = max(3, min(10, suggested_floors))  # Between 3 and 10 floors
        
        return suggested_floors

    def _generate_floor(self, floor: int):
        """Generate a single floor with rooms and hallways."""
        # Initialize the grid for this floor
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                self.grid[(x, y, floor)] = GridCell('empty')
        
        # Generate additional rooms with linear progression
        self._generate_linear_progression_floor(floor)
        
        # Add special features to the floor
        self._add_special_features(floor)

    def _generate_linear_progression_floor(self, floor: int):
        """Generate a floor with a linear progression path from start to end."""
        # Define room types and their size ranges
        room_configs = {
            "empty": {"min_width": 2, "max_width": 4, "min_height": 2, "max_height": 4},
            "treasure": {"min_width": 3, "max_width": 5, "min_height": 3, "max_height": 5},
            "monster": {"min_width": 3, "max_width": 6, "min_height": 3, "max_height": 6},
            "npc": {"min_width": 3, "max_width": 4, "min_height": 3, "max_height": 4},
            "storage": {"min_width": 2, "max_width": 4, "min_height": 2, "max_height": 5},
            "bunk": {"min_width": 2, "max_width": 3, "min_height": 2, "max_height": 4},
            "kitchen": {"min_width": 3, "max_width": 5, "min_height": 2, "max_height": 4},
            "library": {"min_width": 3, "max_width": 4, "min_height": 3, "max_height": 6},
            "workshop": {"min_width": 3, "max_width": 5, "min_height": 2, "max_height": 5},
            "garden": {"min_width": 3, "max_width": 6, "min_height": 3, "max_height": 4}
        }
        
        # Create start room - only floor 0 should have an entrance, other floors have generic start areas
        start_width = random.randint(3, 5)
        start_height = random.randint(3, 5)
        start_x = random.randint(2, 8)  # Near left edge
        start_y = random.randint(2, 8)  # Near top edge
        
        room_type = "entrance" if floor == 0 else "hub"  # Only first floor has entrance
        description = "The entrance to this dungeon floor. A bright light comes from behind you." if floor == 0 else "A central hub of this floor."
        
        start_room = Room(start_x, start_y, floor, start_width, start_height, room_type)
        start_room.description = description
        self.rooms.append(start_room)
        
        # Mark grid cells as part of the start room
        for x in range(start_x, start_x + start_width):
            for y in range(start_y, start_y + start_height):
                if (x, y, floor) in self.grid:
                    self.grid[(x, y, floor)].cell_type = 'room'
                    self.grid[(x, y, floor)].room_ref = start_room
        
        # Create end room (exit) near bottom of the grid
        end_width = random.randint(3, 5)
        end_height = random.randint(3, 5)
        end_x = random.randint(self.grid_width - 10, self.grid_width - 5)  # Near right edge
        end_y = random.randint(self.grid_height - 10, self.grid_height - 5)  # Near bottom edge
        
        end_room = Room(end_x, end_y, floor, end_width, end_height, "exit")
        end_room.description = "The exit of this dungeon floor. A bright light shines ahead."
        self.rooms.append(end_room)
        
        # Mark grid cells as part of the end room
        for x in range(end_x, end_x + end_width):
            for y in range(end_y, end_y + end_height):
                if (x, y, floor) in self.grid:
                    self.grid[(x, y, floor)].cell_type = 'room'
                    self.grid[(x, y, floor)].room_ref = end_room
        
        # Create main path from start to end room
        main_path_rooms = self._create_main_path(start_room, end_room, floor, room_configs)
        
        # Generate additional filler rooms as branches off the main path
        self._generate_branch_rooms(floor, main_path_rooms, room_configs)
        
        # Create hallways to connect the main path
        self._create_main_path_hallways(main_path_rooms, floor)

    def _create_main_path(self, start_room: Room, end_room: Room, floor: int, room_configs: dict):
        """Create the main path of rooms from start to end."""
        main_path_rooms = [start_room]
        
        # Calculate how many intermediate rooms we need based on distance
        start_center = start_room.get_center()
        end_center = end_room.get_center()
        
        # Calculate distance to determine number of intermediate rooms (ignore z coordinate for distance)
        dist_x = abs(end_center[0] - start_center[0])
        dist_y = abs(end_center[1] - start_center[1])
        total_dist = dist_x + dist_y
        
        # Number of intermediate rooms based on distance (at least 3)
        num_intermediate = max(3, total_dist // 8)
        
        # Generate intermediate rooms along the path
        prev_room = start_room
        for i in range(num_intermediate):
            # Calculate target position closer to end room
            prev_center = prev_room.get_center()
            target_x, target_y, target_z = end_center
            
            # Interpolate position along the path
            progress = (i + 1) / (num_intermediate + 1)
            mid_x = int(prev_center[0] + (target_x - prev_center[0]) * progress)
            mid_y = int(prev_center[1] + (target_y - prev_center[1]) * progress)
            
            # Add some randomness to the path
            mid_x += random.randint(-3, 3)
            mid_y += random.randint(-3, 3)
            
            # Keep within bounds
            mid_x = max(1, min(self.grid_width - 6, mid_x))
            mid_y = max(1, min(self.grid_height - 6, mid_y))
            
            # Create intermediate room
            room_type = random.choice(["empty", "treasure", "monster", "npc"])  # Main path rooms
            config = room_configs[room_type]
            width = random.randint(config["min_width"], config["max_width"])
            height = random.randint(config["min_height"], config["max_height"])
            
            # Position the room with some space for hallways
            room_x = max(0, min(mid_x - width//2, self.grid_width - width))
            room_y = max(0, min(mid_y - height//2, self.grid_height - height))
            
            # Check for overlap
            if not self._room_overlaps_existing(room_x, room_y, width, height, floor):
                room = Room(room_x, room_y, floor, width, height, room_type)
                self._assign_room_description(room)
                self.rooms.append(room)
                
                # Mark grid cells as part of the room
                for rx in range(room_x, room_x + width):
                    for ry in range(room_y, room_y + height):
                        if (rx, ry, floor) in self.grid:
                            self.grid[(rx, ry, floor)].cell_type = 'room'
                            self.grid[(rx, ry, floor)].room_ref = room
                
                main_path_rooms.append(room)
                prev_room = room
            else:
                # If we can't place the room due to overlap, adjust position and try again
                for attempt in range(50):
                    new_x = max(0, min(mid_x - width//2 + random.randint(-5, 5), self.grid_width - width))
                    new_y = max(0, min(mid_y - height//2 + random.randint(-5, 5), self.grid_height - height))
                    
                    if not self._room_overlaps_existing(new_x, new_y, width, height, floor):
                        room = Room(new_x, new_y, floor, width, height, room_type)
                        self._assign_room_description(room)
                        self.rooms.append(room)
                        
                        # Mark grid cells as part of the room
                        for rx in range(new_x, new_x + width):
                            for ry in range(new_y, new_y + height):
                                if (rx, ry, floor) in self.grid:
                                    self.grid[(rx, ry, floor)].cell_type = 'room'
                                    self.grid[(rx, ry, floor)].room_ref = room
                        
                        main_path_rooms.append(room)
                        prev_room = room
                        break
        
        # Add the end room to the main path
        main_path_rooms.append(end_room)
        
        return main_path_rooms

    def _generate_branch_rooms(self, floor: int, main_path_rooms: list, room_configs: dict):
        """Generate branch rooms that connect off the main path."""
        # Number of branch rooms to create
        num_branches = random.randint(5, 10)
        
        for _ in range(num_branches):
            # Select a random room from the main path to branch from
            main_room = random.choice(main_path_rooms)
            main_center = main_room.get_center()
            
            # Determine branch direction (perpendicular to the general path direction)
            # For now, just choose a random direction from the main room
            directions = [
                (main_center[0] + random.randint(5, 10), main_center[1]),  # Right
                (main_center[0] - random.randint(5, 10), main_center[1]),  # Left
                (main_center[0], main_center[1] + random.randint(5, 10)),  # Down
                (main_center[0], main_center[1] - random.randint(5, 10))   # Up
            ]
            
            branch_pos = random.choice(directions)
            branch_x, branch_y = branch_pos
            
            # Select room type for branch (could be quest rooms, treasure rooms, etc.)
            room_type = random.choice(["treasure", "monster", "npc", "storage", "library", "workshop", "garden"])
            config = room_configs[room_type]
            width = random.randint(config["min_width"], config["max_width"])
            height = random.randint(config["min_height"], config["max_height"])
            
            # Adjust position to fit in grid
            branch_x = max(0, min(branch_x - width//2, self.grid_width - width))
            branch_y = max(0, min(branch_y - height//2, self.grid_height - height))
            
            # Check for overlap
            if not self._room_overlaps_existing(branch_x, branch_y, width, height, floor):
                branch_room = Room(branch_x, branch_y, floor, width, height, room_type)
                self._assign_room_description(branch_room)
                self.rooms.append(branch_room)
                
                # Mark grid cells as part of the room
                for rx in range(branch_x, branch_x + width):
                    for ry in range(branch_y, branch_y + height):
                        if (rx, ry, floor) in self.grid:
                            self.grid[(rx, ry, floor)].cell_type = 'room'
                            self.grid[(rx, ry, floor)].room_ref = branch_room
                
                # Create a hallway connecting the main path room to the branch room
                self._create_hallway_between_rooms(main_room, branch_room, floor)

    def _create_main_path_hallways(self, main_path_rooms: list, floor: int):
        """Create hallways connecting the main path rooms sequentially."""
        for i in range(len(main_path_rooms) - 1):
            room1 = main_path_rooms[i]
            room2 = main_path_rooms[i + 1]
            
            # Create a hallway between consecutive rooms in the main path
            self._create_hallway_between_rooms(room1, room2, floor)

    def _room_overlaps_existing(self, x: int, y: int, width: int, height: int, floor: int) -> bool:
        """Check if a room at the given position overlaps with existing rooms."""
        # Add some padding between rooms
        padding = 2
        
        padded_x = x - padding
        padded_y = y - padding
        padded_width = width + 2 * padding
        padded_height = height + 2 * padding
        
        # Check if any cell in the padded area is already occupied
        for px in range(padded_x, padded_x + padded_width):
            for py in range(padded_y, padded_y + padded_height):
                if (px, py, floor) in self.grid:
                    cell = self.grid[(px, py, floor)]
                    if cell.cell_type == 'room':
                        return True
        
        return False

    def _assign_room_description(self, room: Room):
        """Assign a description to a room based on its type."""
        room_templates_raw = self.data_provider.get_room_templates()
        
        # Handle both dictionary and list formats for room templates
        if isinstance(room_templates_raw, dict) and 'room_templates' in room_templates_raw:
            # Dictionary format: {'room_templates': [...]}
            room_templates = room_templates_raw['room_templates']
        elif isinstance(room_templates_raw, list):
            # List format: [...]
            room_templates = room_templates_raw
        else:
            # Default to empty list if format is unexpected
            room_templates = []
        
        # Find the template for this room type
        room_template = None
        for template in room_templates:
            if isinstance(template, dict) and template.get('type') == room.room_type:
                room_template = template
                break
        
        if room_template and 'descriptions' in room_template and isinstance(room_template['descriptions'], list):
            room.description = random.choice(room_template['descriptions'])
        else:
            # Default descriptions
            defaults = {
                "hub": "A central hub of this floor.",
                "empty": "An empty room with nothing of interest.",
                "treasure": "A room filled with valuable treasures.",
                "monster": "A room inhabited by dangerous creatures.",
                "npc": "A room containing a non-player character.",
                "storage": "A storage room with various supplies.",
                "bunk": "A sleeping area with beds or resting spots.",
                "kitchen": "A room with cooking facilities and food supplies.",
                "library": "A room filled with books and scrolls.",
                "workshop": "A workshop with tools and crafting materials.",
                "garden": "A small garden with plants and herbs.",
                "entrance": "The entrance to this dungeon floor. A bright light comes from behind you.",
                "exit": "The exit of this dungeon floor. A bright light shines ahead."
            }
            room.description = defaults.get(room.room_type, f"A {room.room_type} room.")

    def _create_hallway_between_rooms(self, room1: Room, room2: Room, floor: int):
        """Create a hallway between two rooms."""
        # Get centers of both rooms
        center1 = room1.get_center()
        center2 = room2.get_center()
        
        start_x, start_y, start_z = center1
        end_x, end_y, end_z = center2
        
        # Simple L-shaped hallway: go horizontal then vertical
        if random.choice([True, False]):  # Random choice of which direction to go first
            # Horizontal then vertical
            self._create_horizontal_hallway(start_x, end_x, start_y, floor)
            self._create_vertical_hallway(start_y, end_y, end_x, floor)
        else:
            # Vertical then horizontal
            self._create_vertical_hallway(start_y, end_y, start_x, floor)
            self._create_horizontal_hallway(start_x, end_x, end_y, floor)
        
        # Add connections between rooms - determine direction based on relative positions
        dx = end_x - start_x
        dy = end_y - start_y
        
        # Determine primary direction for connection
        if abs(dx) > abs(dy):  # More horizontal movement
            if dx > 0:
                room1.connections[Direction.EAST] = (end_x, end_y, floor)
                room2.connections[Direction.WEST] = (start_x, start_y, floor)
            else:
                room1.connections[Direction.WEST] = (end_x, end_y, floor)
                room2.connections[Direction.EAST] = (start_x, start_y, floor)
        else:  # More vertical movement
            if dy > 0:
                room1.connections[Direction.SOUTH] = (end_x, end_y, floor)
                room2.connections[Direction.NORTH] = (start_x, start_y, floor)
            else:
                room1.connections[Direction.NORTH] = (end_x, end_y, floor)
                room2.connections[Direction.SOUTH] = (start_x, start_y, floor)

    def _create_horizontal_hallway(self, start_x: int, end_x: int, y: int, floor: int):
        """Create a horizontal hallway, avoiding rooms."""
        min_x, max_x = min(start_x, end_x), max(start_x, end_x)
        
        for x in range(min_x, max_x + 1):
            pos = (x, y, floor)
            if pos in self.grid:
                # Only create hallway if the cell is empty (not part of a room)
                if self.grid[pos].cell_type == 'empty':
                    self.grid[pos].cell_type = 'hallway'
                    self.grid[pos].room_ref = None  # Clear any room reference

    def _create_vertical_hallway(self, start_y: int, end_y: int, x: int, floor: int):
        """Create a vertical hallway, avoiding rooms."""
        min_y, max_y = min(start_y, end_y), max(start_y, end_y)
        
        for y in range(min_y, max_y + 1):
            pos = (x, y, floor)
            if pos in self.grid:
                # Only create hallway if the cell is empty (not part of a room)
                if self.grid[pos].cell_type == 'empty':
                    self.grid[pos].cell_type = 'hallway'
                    self.grid[pos].room_ref = None  # Clear any room reference

    def _add_special_features(self, floor: int):
        """Add special features like stairs, locked doors, etc. to a floor."""
        floor_rooms = [room for room in self.rooms if room.z == floor]
        
        # Add map effects to random positions in rooms
        self._add_map_effects(floor)
        
        # Add locked doors and blocked passages to hallway tiles
        self._add_obstacles_to_hallways(floor)
    
    def _add_obstacles_to_hallways(self, floor: int):
        """Add locked doors and blocked passages to hallway tiles between rooms with logical progression."""
        # Get all hallway positions on this floor
        hallway_positions = [(x, y, z) for (x, y, z), cell in self.grid.items() 
                             if z == floor and cell.cell_type == 'hallway']
        
        if not hallway_positions:
            return  # No hallways to add obstacles to
        
        # Get all rooms on this floor to determine logical progression order
        floor_rooms = [room for room in self.rooms if room.z == floor]
        
        # Create a logical ordering of positions based on path from start to end
        # Find start and end rooms for this floor
        start_room = None
        end_room = None
        
        for room in floor_rooms:
            if room.room_type == "entrance" or (floor == 0 and room.room_type == "hub"):
                start_room = room
                break
        
        # If no entrance, find the room closest to the start of the grid
        if not start_room and floor_rooms:
            start_room = min(floor_rooms, key=lambda r: r.x + r.y)
        
        # Order positions based on distance from start room
        position_distances = {}
        for pos in hallway_positions:
            if start_room:
                dist = abs(pos[0] - start_room.x) + abs(pos[1] - start_room.y)
            else:
                dist = pos[0] + pos[1]  # Fallback distance
            position_distances[pos] = dist
        
        # Sort hallway positions by distance (logical progression order)
        sorted_hallway_positions = sorted(hallway_positions, key=lambda pos: position_distances[pos])
        
        # Divide positions into early (first half) and late (second half)
        split_point = len(sorted_hallway_positions) // 2
        early_positions = sorted_hallway_positions[:split_point] if split_point > 0 else []
        late_positions = sorted_hallway_positions[split_point:]
        
        # Place locked doors and blocked passages on hallway tiles
        # We'll place them in later positions but ensure required items are in earlier positions
        items = self.data_provider.get_items()
        key_items = [item for item in items if item.get("type", "").lower() == "key"]
        
        # Place locked doors (magical barriers that require keys) in later positions
        num_locked_doors = min(len(late_positions), 5)  # Place up to 5 locked doors
        selected_late_hallways = random.sample(late_positions, min(num_locked_doors, len(late_positions))) if late_positions else []
        
        for pos in selected_late_hallways:
            if key_items:
                key_item = random.choice(key_items)
                direction = random.choice(list(Direction))  # Random direction for the lock
                self.grid[pos].locked_doors[direction] = key_item["name"]
                
                # Place the required key in an earlier position to ensure logical progression
                if early_positions:
                    key_pos = random.choice(early_positions)
                    key_item_obj = self._find_item_by_name(key_item["name"])
                    if key_pos in self.grid and key_item_obj:
                        self.grid[key_pos].items.append(key_item_obj)
        
        # Place blocked passages (magical barriers that require trigger items) in later positions
        remaining_late_positions = [pos for pos in late_positions if pos not in selected_late_hallways]
        num_blocked_passages = min(len(remaining_late_positions), 3)  # Place up to 3 blocked passages
        selected_blocked = random.sample(remaining_late_positions, min(num_blocked_passages, len(remaining_late_positions))) if remaining_late_positions else []
        
        for pos in selected_blocked:
            # Choose a random item as the trigger (could be any item type)
            all_items = self.data_provider.get_items()
            if all_items:
                trigger_item = random.choice(all_items)
                direction = random.choice(list(Direction))  # Random direction for the block
                self.grid[pos].blocked_passages[direction] = trigger_item["name"]
                
                # Place the required trigger item in an earlier position to ensure logical progression
                if early_positions:
                    trigger_pos = random.choice(early_positions)
                    trigger_item_obj = self._find_item_by_name(trigger_item["name"])
                    if trigger_pos in self.grid and trigger_item_obj:
                        self.grid[trigger_pos].items.append(trigger_item_obj)

    def _find_item_by_name(self, name: str):
        """Find an item object by its name."""
        items = self.data_provider.get_items()
        for item_data in items:
            if item_data["name"] == name:
                return Item(
                    name=item_data["name"],
                    item_type=ItemType(item_data.get("type", "CONSUMABLE")),
                    value=item_data.get("value", 0),
                    description=item_data.get("description", ""),
                    attack_bonus=item_data.get("attack_bonus", 0),
                    defense_bonus=item_data.get("defense_bonus", 0),
                    health_bonus=item_data.get("health_bonus", 0),
                    status_effects=item_data.get("status_effects", {}),
                    status_effect=item_data.get("status_effect"),
                    status_chance=item_data.get("status_chance", 0.0),
                    status_damage=item_data.get("status_damage", 0)
                )
        # If not found, return a basic version
        return Item(name, ItemType.KEY, 10, f"A key to unlock {name}", status_effects={})

    def _connect_stairs_properly(self):
        """Ensure stairs are properly connected between floors as single-tile objects."""
        all_floors = set(room.z for room in self.rooms)
        max_floor = max(all_floors) if all_floors else 0
        min_floor = min(all_floors) if all_floors else 0
        
        # Connect stairs between each consecutive pair of floors
        for floor in range(max_floor):  # Connect floors 0->1, 1->2, ..., (n-1)->n
            current_floor_rooms = [room for room in self.rooms if room.z == floor]
            next_floor_rooms = [room for room in self.rooms if room.z == floor + 1]
            
            if current_floor_rooms and next_floor_rooms:
                # Select a room from current floor to have stairs down
                from_room = random.choice(current_floor_rooms)
                # Select a room from next floor to have stairs up
                to_room = random.choice(next_floor_rooms)
                
                # Connect them using room centers
                from_center = from_room.get_center()
                to_center = to_room.get_center()
                
                # Add stairs to the rooms as single-tile Stair objects
                # Create the down stair on the current floor
                stair_down = Stair(
                    position=from_center,  # Where the stair object is placed
                    direction=Direction.DOWN,  # Direction of movement
                    connects_to=to_center  # Where it takes you
                )
                
                # Create the up stair on the next floor
                stair_up = Stair(
                    position=to_center,  # Where the stair object is placed
                    direction=Direction.UP,  # Direction of movement
                    connects_to=from_center  # Where it takes you
                )
                
                # Add Stair objects to the grid cells at the center of each room
                # This ensures that when a player stands on these positions, they can interact with stairs
                if from_center in self.grid:
                    self.grid[from_center].items.append(stair_down)
                    # Also add to the room's items list for backward compatibility
                    from_room.items.append(stair_down)
                
                if to_center in self.grid:
                    self.grid[to_center].items.append(stair_up)
                    # Also add to the room's items list for backward compatibility
                    to_room.items.append(stair_up)
                
                # Keep room-level flags for backward compatibility with existing code
                from_room.has_stairs_down = True
                from_room.stairs_down_target = to_center
                to_room.has_stairs_up = True
                to_room.stairs_up_target = from_center
        
        # Ensure there's a special artifact room on the deepest (highest-numbered) floor as the win condition
        deepest_floor_rooms = [room for room in self.rooms if room.z == max_floor]
        if deepest_floor_rooms:
            # Select a room on the deepest floor to be the special artifact room
            artifact_room = random.choice(deepest_floor_rooms)
            
            # Change this room to be an artifact room if it isn't already
            artifact_room.room_type = "artifact"
            artifact_room.description = "The ultimate treasure chamber. The final resting place of a powerful artifact."
            
            # Clear any existing items and ensure it has a proper artifact
            artifact_room.items.clear()
            artifact = self._generate_artifact()
            artifact_room.items.append(artifact)

    def _populate_all_rooms(self):
        """Populate all rooms with items and entities."""
        for room in self.rooms:
            self._populate_room(room)

    def _populate_room(self, room: Room):
        """Populate a single room with items and entities based on its type."""
        # Determine the lowest floor in the dungeon
        all_floors = set(r.z for r in self.rooms)
        lowest_floor = min(all_floors) if all_floors else 0
        
        # Get all positions within this room
        room_positions = room.get_all_positions()
        
        # Add items based on room type
        if room.room_type == "treasure":
            # Add 1-3 treasure items to specific positions in the room
            num_items = random.randint(1, 3)
            selected_positions = random.sample(room_positions, min(num_items, len(room_positions)))
            for pos_idx, (x, y) in enumerate(selected_positions):
                pos = (x, y, room.z)
                if pos in self.grid:
                    item = self._generate_random_item()
                    self.grid[pos].items.append(item)
        elif room.room_type == "empty":
            # Small chance to add an item in empty rooms
            if random.random() < 0.2 and room_positions:
                if random.random() < 0.5:
                    pos = random.choice(room_positions)
                    full_pos = (pos[0], pos[1], room.z)
                    if full_pos in self.grid:
                        item = self._generate_random_item()
                        self.grid[full_pos].items.append(item)
        elif room.room_type == "monster":
            # Add monsters
            num_monsters = random.randint(1, 3)
            for _ in range(num_monsters):
                monster = self._generate_random_enemy(room.z)
                room.entities.append(monster)
            # Maybe add a treasure item too
            if random.random() < 0.3 and room_positions:
                pos = random.choice(room_positions)
                full_pos = (pos[0], pos[1], room.z)
                if full_pos in self.grid:
                    item = self._generate_random_item()
                    self.grid[full_pos].items.append(item)
        elif room.room_type == "npc":
            # Add an NPC
            npc = self._generate_random_npc()
            room.npcs.append(npc)
        elif room.room_type == "artifact":
            # Add a special artifact ONLY if this is the lowest floor
            if room.z == lowest_floor and room_positions:
                pos = random.choice(room_positions)
                full_pos = (pos[0], pos[1], room.z)
                if full_pos in self.grid:
                    artifact = self._generate_artifact()
                    self.grid[full_pos].items.append(artifact)
        elif room.room_type == "storage":
            # Add 1-3 storage-related items to specific positions
            num_items = random.randint(1, 3)
            selected_positions = random.sample(room_positions, min(num_items, len(room_positions)))
            for pos_idx, (x, y) in enumerate(selected_positions):
                pos = (x, y, room.z)
                if pos in self.grid:
                    item = self._generate_random_item()
                    self.grid[pos].items.append(item)
        elif room.room_type == "bunk":
            # Add 1-2 items related to rest/sleep to specific positions
            num_items = random.randint(1, 2)
            selected_positions = random.sample(room_positions, min(num_items, len(room_positions)))
            for pos_idx, (x, y) in enumerate(selected_positions):
                pos = (x, y, room.z)
                if pos in self.grid:
                    item = self._generate_random_item()
                    self.grid[pos].items.append(item)
        elif room.room_type == "kitchen":
            # Add 1-3 food and cooking-related items to specific positions
            num_items = random.randint(1, 3)
            selected_positions = random.sample(room_positions, min(num_items, len(room_positions)))
            for pos_idx, (x, y) in enumerate(selected_positions):
                pos = (x, y, room.z)
                if pos in self.grid:
                    item = self._generate_random_item()
                    self.grid[pos].items.append(item)
        elif room.room_type == "library":
            # Add 1-2 knowledge-related items to specific positions
            num_items = random.randint(1, 2)
            selected_positions = random.sample(room_positions, min(num_items, len(room_positions)))
            for pos_idx, (x, y) in enumerate(selected_positions):
                pos = (x, y, room.z)
                if pos in self.grid:
                    item = self._generate_random_item()
                    self.grid[pos].items.append(item)
        elif room.room_type == "workshop":
            # Add 1-3 crafting/tool-related items to specific positions
            num_items = random.randint(1, 3)
            selected_positions = random.sample(room_positions, min(num_items, len(room_positions)))
            for pos_idx, (x, y) in enumerate(selected_positions):
                pos = (x, y, room.z)
                if pos in self.grid:
                    item = self._generate_random_item()
                    self.grid[pos].items.append(item)
        elif room.room_type == "garden":
            # Add 1-2 plant/herb-related items to specific positions
            num_items = random.randint(1, 2)
            selected_positions = random.sample(room_positions, min(num_items, len(room_positions)))
            for pos_idx, (x, y) in enumerate(selected_positions):
                pos = (x, y, room.z)
                if pos in self.grid:
                    item = self._generate_random_item()
                    self.grid[pos].items.append(item)

    def _generate_random_item(self) -> Item:
        """Generate a random item."""
        items = self.data_provider.get_items()
        # Filter out artifacts to avoid placing them in regular rooms
        non_artifact_items = [item for item in items if item.get("type", "").lower() != "artifact"]
        
        if non_artifact_items:
            item_data = random.choice(non_artifact_items)
            return Item(
                name=item_data["name"],
                item_type=ItemType(item_data["type"]),
                value=item_data.get("value", 0),
                description=item_data.get("description", ""),
                attack_bonus=item_data.get("attack_bonus", 0),
                defense_bonus=item_data.get("defense_bonus", 0),
                health_bonus=item_data.get("health_bonus", 0),
                status_effects=item_data.get("status_effects", {}),
                status_effect=item_data.get("status_effect"),
                status_chance=item_data.get("status_chance", 0.0),
                status_damage=item_data.get("status_damage", 0)
            )
        else:
            # Fallback item
            return Item("Health Potion", ItemType.CONSUMABLE, 20, "Restores 20 HP", status_effects={})

    def _generate_random_enemy(self, floor: int):
        """Generate a random enemy based on floor."""
        from .new_enemy import Enemy
        
        # Scale enemy strength based on floor
        enemies = self.data_provider.get_enemies()
        if enemies:
            # Filter enemies appropriate for floor level
            suitable_enemies = [e for e in enemies if e.get("min_floor", 0) <= floor]
            if not suitable_enemies:
                suitable_enemies = enemies  # Use all if none match criteria
            
            enemy_data = random.choice(suitable_enemies)
            
            # Scale stats based on floor, using scaling parameters from enemy definition if available
            # Default scaling factors if not specified in enemy data
            health_scaling = enemy_data.get("health_scaling", 10)  # How much health increases per floor
            attack_scaling = enemy_data.get("attack_scaling", 2)   # How much attack increases per floor
            defense_scaling = enemy_data.get("defense_scaling", 1) # How much defense increases per floor
            
            health = enemy_data["health"] + (floor * health_scaling)
            attack = enemy_data["attack"] + (floor * attack_scaling)
            defense = enemy_data["defense"] + (floor * defense_scaling)
            
            enemy = Enemy(
                name=enemy_data["name"],
                health=health,
                attack=attack,
                defense=defense,
                speed=enemy_data.get("speed", 10)
            )
            return enemy
        else:
            # Fallback enemy
            return Enemy("Goblin", 20 + (floor * 5), 5 + floor, 2 + floor)

    def _generate_random_npc(self):
        """Generate a random NPC."""
        from .character import NonPlayerCharacter
        
        npcs = self.data_provider.get_npcs()
        if npcs:
            npc_data = random.choice(npcs)
            # Handle new NPC structure with quest system
            if "dialogues" in npc_data and isinstance(npc_data["dialogues"], list):
                # Use a random dialogue from the dialogues list
                dialogue = [random.choice(npc_data["dialogues"])] if npc_data["dialogues"] else ["Hello, adventurer."]
            else:
                dialogue = npc_data.get("dialogue", ["Hello, adventurer."])
            
            return NonPlayerCharacter(
                name=npc_data["name"],
                health=npc_data["health"],
                attack=npc_data.get("attack", 3),  # Default attack value
                defense=npc_data.get("defense", 1),  # Default defense value
                dialogue=dialogue
            )
        else:
            # Fallback NPC
            return NonPlayerCharacter("Friendly Merchant", 10, 3, 1, ["Welcome traveler!", "Need supplies?"])

    def _generate_artifact(self) -> Item:
        """Generate a special artifact item."""
        # Get artifact items from data provider if available
        items = self.data_provider.get_items()
        artifact_items = [item for item in items if item.get("type") == "ARTIFACT"]
        
        if artifact_items:
            artifact_data = random.choice(artifact_items)
            return Item(
                name=artifact_data["name"],
                item_type=ItemType(artifact_data["type"]),
                value=artifact_data.get("value", 0),
                description=artifact_data.get("description", ""),
                attack_bonus=artifact_data.get("attack_bonus", 0),
                defense_bonus=artifact_data.get("defense_bonus", 0),
                health_bonus=artifact_data.get("health_bonus", 0),
                status_effects=artifact_data.get("status_effects", {}),
                status_effect=artifact_data.get("status_effect"),
                status_chance=artifact_data.get("status_chance", 0.0),
                status_damage=artifact_data.get("status_damage", 0)
            )
        else:
            # Fallback artifact
            return Item("Ancient Relic", ItemType.ARTIFACT, 100, "An ancient magical relic", status_effects={})

    def _add_map_effects(self, floor: int):
        """Add various map effects throughout the dungeon floor."""
        floor_rooms = [room for room in self.rooms if room.z == floor]
        
        # Add effects to random positions within rooms
        for room in floor_rooms:
            # Determine number of effects based on room size
            num_effects = max(0, room.width * room.height // 10)  # Roughly 1 effect per 10 room tiles
            
            for _ in range(num_effects):
                # Select a random position within the room
                x = random.randint(room.x, room.x + room.width - 1)
                y = random.randint(room.y, room.y + room.height - 1)
                
                # Randomly select an effect type
                effect_type = random.choice(list(MapEffectType))
                
                # Define properties based on effect type
                if effect_type == MapEffectType.TRAP:
                    # Traps have a high chance to trigger when stepped on
                    trigger_chance = 0.8
                    effect_strength = random.randint(5, 15)  # Damage amount
                    description = "This area seems dangerous - there might be hidden traps nearby."
                elif effect_type == MapEffectType.WET_AREA:
                    # Wet areas don't trigger damage but provide environmental flavor
                    trigger_chance = 0.0
                    effect_strength = 0
                    description = "The ground is wet and soggy here."
                elif effect_type == MapEffectType.POISONOUS_AREA:
                    # Poisonous areas can cause damage and status effects
                    trigger_chance = 0.6
                    effect_strength = random.randint(3, 8)  # Poison damage
                    description = "A toxic mist lingers in the air, making this area hazardous."
                elif effect_type == MapEffectType.ICY_SURFACE:
                    # Icy surfaces affect movement
                    trigger_chance = 0.3
                    effect_strength = 2  # Speed reduction amount
                    description = "The floor is covered in ice, making it treacherous to walk on."
                elif effect_type == MapEffectType.DARK_CORNER:
                    # Dark corners affect visibility (currently just descriptive)
                    trigger_chance = 0.0
                    effect_strength = 0
                    description = "Deep shadows obscure vision in this area."
                elif effect_type == MapEffectType.SLIPPERY_FLOOR:
                    # Slippery floors can cause movement issues
                    trigger_chance = 0.2
                    effect_strength = 1  # Minor effect
                    description = "The floor here is unusually slippery."
                elif effect_type == MapEffectType.LOUD_FLOOR:
                    # Loud floors alert enemies
                    trigger_chance = 0.0
                    effect_strength = 0
                    description = "The floor creaks and groans underfoot, echoing through the dungeon."
                elif effect_type == MapEffectType.MAGNETIC_FIELD:
                    # Magnetic fields affect metal items
                    trigger_chance = 0.0
                    effect_strength = 0
                    description = "A strange magnetic field tugs at metallic objects."
                
                # Create and add the map effect to the grid cell
                effect = MapEffect(
                    effect_type=effect_type,
                    position=(x, y, floor),
                    trigger_chance=trigger_chance,
                    description=description,
                    effect_strength=effect_strength
                )
                
                # Mark the grid cell as having a map effect
                if (x, y, floor) in self.grid:
                    self.grid[(x, y, floor)].has_map_effect = True
                    self.grid[(x, y, floor)].map_effect = effect
                
                # Also add to the map effects manager
                self.map_effects.add_effect(effect)

    def get_room_at_position(self, pos: Tuple[int, int, int]) -> Room:
        """Get the room at a given position."""
        x, y, z = pos
        
        # Check if the position is in the grid
        if (x, y, z) in self.grid:
            cell = self.grid[(x, y, z)]
            if cell.room_ref:
                return cell.room_ref
        
        # If not in a room, return None
        return None

    def get_cell_type_at_position(self, pos: Tuple[int, int, int]) -> str:
        """Get the cell type at a given position."""
        if pos in self.grid:
            return self.grid[pos].cell_type
        return 'empty'

    def get_map_effect_at_position(self, pos: Tuple[int, int, int]) -> MapEffect:
        """Get the map effect at a given position."""
        if pos in self.grid and self.grid[pos].has_map_effect:
            return self.grid[pos].map_effect
        return None

    def get_all_rooms_on_floor(self, floor: int) -> List[Room]:
        """Get all rooms on a specific floor."""
        return [room for room in self.rooms if room.z == floor]

    def to_dict(self) -> Dict[str, Any]:
        """Convert dungeon to dictionary for saving."""
        # For now, we'll serialize the room information
        room_data = []
        for room in self.rooms:
            # Filter out Stair objects from items list - they are handled separately
            from classes.new_dungeon import Stair
            regular_items = [item for item in room.items if not isinstance(item, Stair)]
            
            room_data.append({
                'x': room.x,
                'y': room.y,
                'z': room.z,
                'width': room.width,
                'height': room.height,
                'room_type': room.room_type,
                'description': room.description,
                'items': [item.to_dict() for item in regular_items],  # Only regular items
                'entities': [entity.to_dict() if hasattr(entity, 'to_dict') else str(entity) for entity in room.entities],
                'npcs': [npc.to_dict() if hasattr(npc, 'to_dict') else str(npc) for npc in room.npcs],
                'locked_doors': room.locked_doors,
                'blocked_passages': room.blocked_passages,
                'has_stairs_up': room.has_stairs_up,
                'has_stairs_down': room.has_stairs_down,
                'stairs_up_target': room.stairs_up_target,
                'stairs_down_target': room.stairs_down_target,
                'connections': {k.value: v for k, v in room.connections.items()}  # Convert Direction enums to values
            })
        
        return {
            "seed": self.seed,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "rooms": room_data,
            "map_effects": self.map_effects.to_dict(),
            # Serialize grid state as needed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create dungeon from dictionary for loading."""
        # This is a simplified implementation - a full implementation would need
        # to reconstruct the grid and all the relationships
        dungeon = cls(data["seed"], data["grid_width"], data["grid_height"])
        
        # Reconstruct rooms
        dungeon.rooms = []
        for room_data in data["rooms"]:
            room = Room(
                room_data['x'],
                room_data['y'],
                room_data['z'],
                room_data['width'],
                room_data['height'],
                room_data['room_type']
            )
            room.description = room_data['description']
            
            # Reconstruct items - check for Stair objects
            from .item import Item
            for item_data in room_data['items']:
                # Check if this is a Stair object by looking for stair-specific attributes
                if 'direction' in item_data and 'connects_to' in item_data:
                    # This is a Stair object
                    stair = Stair.from_dict(item_data)
                    room.items.append(stair)
                else:
                    # This is a regular Item
                    item = Item.from_dict(item_data)
                    room.items.append(item)
            
            # Reconstruct entities - check if they have enemy-specific attributes
            room.entities = []
            for entity_data in room_data['entities']:
                # Check if entity has enemy-specific attributes (ai_state indicates it's an Enemy)
                if 'ai_state' in entity_data:
                    # This is an Enemy
                    from .new_enemy import Enemy
                    enemy = Enemy.from_dict(entity_data)
                    room.entities.append(enemy)
                else:
                    # This is a generic Entity
                    from .base import Entity
                    entity = Entity.from_dict(entity_data)
                    room.entities.append(entity)
            
            # Reconstruct NPCs
            from .character import NonPlayerCharacter
            room.npcs = []
            for npc_data in room_data['npcs']:
                npc = NonPlayerCharacter.from_dict(npc_data)
                room.npcs.append(npc)
            
            # Restore other properties
            room.locked_doors = room_data['locked_doors']
            room.blocked_passages = room_data['blocked_passages']
            room.has_stairs_up = room_data['has_stairs_up']
            room.has_stairs_down = room_data['has_stairs_down']
            room.stairs_up_target = room_data['stairs_up_target']
            room.stairs_down_target = room_data['stairs_down_target']
            
            # Restore connections (convert values back to Direction enums)
            from .base import Direction
            for dir_val, target in room_data['connections'].items():
                try:
                    direction_enum = Direction(dir_val)
                    room.connections[direction_enum] = target
                except ValueError:
                    # If the value doesn't correspond to a valid Direction, skip it
                    continue
            
            dungeon.rooms.append(room)
        
        # Rebuild the grid based on rooms
        for room in dungeon.rooms:
            for x in range(room.x, room.x + room.width):
                for y in range(room.y, room.y + room.height):
                    pos = (x, y, room.z)
                    if pos not in dungeon.grid:
                        dungeon.grid[pos] = GridCell('room')
                        dungeon.grid[pos].room_ref = room
        
        # Load map effects if they exist
        if "map_effects" in data:
            dungeon.map_effects = MapEffectManager.from_dict(data["map_effects"])
        else:
            # For backward compatibility, create a new map effects manager
            dungeon.map_effects = MapEffectManager()
        
        return dungeon