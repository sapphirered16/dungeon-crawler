#!/usr/bin/env python3
"""
Dungeon Visualizer Tool
Visualizes the dungeon layout based on a given seed for debugging purposes.
"""

import random
from enum import Enum
from typing import Dict, List, Tuple, Optional


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    UP = "up"
    DOWN = "down"


class RoomType(Enum):
    EMPTY = "empty"
    TREASURE = "treasure"
    MONSTER = "monster"
    TRAP = "trap"
    NPC = "npc"
    ARTIFACT = "artifact"
    HALLWAY = "hallway"
    STAIRCASE = "staircase"


class RoomConnection:
    def __init__(self):
        self.connections: Dict[Direction, Tuple[int, int, int]] = {}  # direction -> (x, y, floor)
        self.has_stairs_up = False
        self.has_stairs_down = False
        self.stairs_up_target = None
        self.stairs_down_target = None
        self.locked_doors: Dict[Direction, str] = {}  # direction -> key name
        self.blocked_passages: Dict[Direction, str] = {}  # direction -> trigger item name


class DungeonVisualizer:
    def __init__(self, seed: int, width: int = 30, height: int = 30, floors: int = 3):
        self.seed = seed
        self.width = width
        self.height = height
        self.floors = floors
        self.rooms: Dict[Tuple[int, int, int], RoomType] = {}
        self.connections: Dict[Tuple[int, int, int], RoomConnection] = {}
        
        # Generate the dungeon based on the seed
        self._generate_dungeon()
    
    def _generate_dungeon(self):
        """Generate the dungeon structure based on the seed"""
        # Set the random seed to ensure reproducible generation
        random.seed(self.seed)
        
        # Define room templates with specific types and characteristics
        room_templates = {
            "starting": {"width_range": (4, 6), "height_range": (4, 6), "min_count": 1, "max_count": 1},
            "treasure": {"width_range": (4, 7), "height_range": (4, 7), "min_count": 1, "max_count": 3},
            "monster": {"width_range": (5, 8), "height_range": (4, 6), "min_count": 2, "max_count": 4},
            "trap": {"width_range": (3, 5), "height_range": (3, 5), "min_count": 1, "max_count": 3},
            "npc": {"width_range": (4, 6), "height_range": (4, 6), "min_count": 0, "max_count": 2},
            "empty": {"width_range": (4, 8), "height_range": (4, 8), "min_count": 2, "max_count": 5},
            "staircase": {"width_range": (3, 4), "height_range": (3, 4), "min_count": 1, "max_count": 1}  # Per floor connection
        }
        
        for floor in range(self.floors):
            # Create rooms with spacing
            rooms_info = []
            
            # First, place required room types (starting room, staircase room)
            required_rooms = []
            
            # Place starting room on first floor only
            if floor == 0:
                start_width = random.randint(*room_templates["starting"]["width_range"])
                start_height = random.randint(*room_templates["starting"]["height_range"])
                start_x = self.width // 2 - start_width // 2
                start_y = self.height // 2 - start_height // 2
                required_rooms.append(("starting", start_x, start_y, start_width, start_height))
            
            # Place staircase room (for connecting floors)
            if floor < self.floors - 1:  # Not on the last floor
                stair_width = random.randint(*room_templates["staircase"]["width_range"])
                stair_height = random.randint(*room_templates["staircase"]["height_range"])
                stair_x = random.randint(2, self.width - stair_width - 2)
                stair_y = random.randint(2, self.height - stair_height - 2)
                required_rooms.append(("staircase", stair_x, stair_y, stair_width, stair_height))
            
            # Add required rooms to the list
            for room_type, x, y, width, height in required_rooms:
                room_info = self.RoomInfo(x, y, width, height, floor)
                rooms_info.append((room_info, room_type))
                
                # Create the room area with specific type
                for rx in range(x, x + width):
                    for ry in range(y, y + height):
                        pos = (rx, ry, floor)
                        
                        # Set room type based on template
                        if room_type == "starting":
                            room_type_enum = RoomType.EMPTY  # Starting area is safe
                        elif room_type in ["staircase", "staircase_up", "staircase_down"]:
                            room_type_enum = RoomType.STAIRCASE  # Staircase is marked as staircase in visualization
                        elif room_type == "treasure":
                            room_type_enum = RoomType.TREASURE
                        elif room_type == "monster":
                            room_type_enum = RoomType.MONSTER
                        elif room_type == "trap":
                            room_type_enum = RoomType.TRAP
                        elif room_type == "npc":
                            room_type_enum = RoomType.NPC
                        else:  # empty
                            room_type_enum = RoomType.EMPTY
                        
                        self.rooms[pos] = room_type_enum
                        self.connections[pos] = RoomConnection()
            
            # Now place additional rooms based on templates
            room_counts = {rtype: 0 for rtype in room_templates.keys()}
            
            # Count already placed required rooms
            for _, rtype in rooms_info:
                if rtype in room_counts:
                    room_counts[rtype] += 1
            
            # Place additional rooms up to the maximum count for each type
            total_attempts = 0
            max_total_rooms = random.randint(8, 15)
            
            while len(rooms_info) < max_total_rooms and total_attempts < 100:
                total_attempts += 1
                
                # Select a room type to place based on remaining quota
                available_types = []
                for rtype, limits in room_templates.items():
                    if room_counts.get(rtype, 0) < limits["max_count"]:
                        # Add the type multiple times to weight the probability
                        for _ in range(max(1, limits["max_count"] - room_counts.get(rtype, 0))):
                            available_types.append(rtype)
                
                if not available_types:
                    break  # No more room types to place
                
                room_type = random.choice(available_types)
                
                # Skip starting and staircase rooms as they're already handled
                if room_type in ["starting", "staircase"]:
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
                            
                            # Set room type based on template
                            if room_type == "treasure":
                                room_type_enum = RoomType.TREASURE
                            elif room_type == "monster":
                                room_type_enum = RoomType.MONSTER
                            elif room_type == "trap":
                                room_type_enum = RoomType.TRAP
                            elif room_type == "npc":
                                room_type_enum = RoomType.NPC
                            else:  # empty
                                room_type_enum = RoomType.EMPTY
                            
                            self.rooms[pos] = room_type_enum
                            self.connections[pos] = RoomConnection()
            
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
                treasure_rooms = [(x, y, z) for (x, y, z), room_type in self.rooms.items() 
                                if z == floor and room_type == RoomType.TREASURE]
                if treasure_rooms:
                    artifact_pos = random.choice(treasure_rooms)
                    self.rooms[artifact_pos] = RoomType.ARTIFACT
                else:
                    # If no treasure room found, place in any room on the last floor
                    floor_rooms = [(x, y, z) for x, y, z in self.rooms.keys() if z == floor]
                    if floor_rooms:
                        artifact_pos = random.choice(floor_rooms)
                        self.rooms[artifact_pos] = RoomType.ARTIFACT
            
            # Connect rooms with hallways
            if len(rooms_info) > 1:
                # Create hallways connecting rooms in sequence
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
                # Find a random room in this floor to place the artifact
                floor_rooms = [(x, y, z) for x, y, z in self.rooms.keys() if z == floor]
                if floor_rooms:
                    artifact_pos = random.choice(floor_rooms)
                    self.rooms[artifact_pos] = RoomType.ARTIFACT

        # With the new room structure, rooms are connected via hallways created earlier,
        # not through adjacent grid positions. The hallway creation already established
        # connections between rooms, so we don't need this automatic grid-based connection.
        # Rooms exist as areas in the grid and are connected via the hallway system created earlier.
        
        # Add stairs between floors (using special room flags)
        # Ensure at least one staircase exists between each pair of floors
        for floor in range(self.floors - 1):  # Connect each floor to the one below it
            # Find staircase rooms on the current and next floor
            current_floor_staircase_rooms = []
            next_floor_staircase_rooms = []
            
            for pos, room_type in self.rooms.items():
                if pos[2] == floor and room_type == RoomType.HALLWAY:  # Staircase rooms are marked as hallways
                    # Look for hallway areas that are likely staircase locations
                    # (typically smaller areas that serve as connectors)
                    current_floor_staircase_rooms.append(pos)
            
            for pos, room_type in self.rooms.items():
                if pos[2] == floor + 1 and room_type == RoomType.HALLWAY:
                    next_floor_staircase_rooms.append(pos)
            
            if current_floor_staircase_rooms and next_floor_staircase_rooms:
                # Pick a room from each floor to place stairs
                current_room_pos = current_floor_staircase_rooms[0]  # Use first staircase room
                next_room_pos = next_floor_staircase_rooms[0]  # Use first staircase room on next floor
                
                current_room_connection = self.connections[current_room_pos]
                next_room_connection = self.connections[next_room_pos]
                
                # Mark rooms as having stairs and set targets
                current_room_connection.has_stairs_down = True
                current_room_connection.stairs_down_target = next_room_pos  # Going down leads to next floor room
                next_room_connection.has_stairs_up = True
                next_room_connection.stairs_up_target = current_room_pos   # Going up leads back to current floor room

        # Add locked doors and blocked passages for puzzle elements
        all_rooms = [pos for pos, conn in self.connections.items()]
        
        # Add some locked doors (about 10% of accessible rooms)
        num_locked_doors = max(1, len(all_rooms) // 10)
        selected_rooms_for_doors = random.sample(all_rooms, min(num_locked_doors, len(all_rooms)))
        
        for pos in selected_rooms_for_doors:
            room_connection = self.connections[pos]
            
            # Since we don't have grid-based connections, we'll just mark the doors as locked without specifying directions
            # This is a simplification for the visualization
            key_types = ["Iron Key", "Silver Key", "Golden Key", "Ancient Key", "Crystal Key"]
            key_required = random.choice(key_types)
            # We'll add a flag to indicate this room has locked doors
            room_connection.locked_door_types = [key_required]

        # Add some blocked passages (about 5% of accessible rooms)
        num_blocked_passages = max(1, len(all_rooms) // 20)
        # Select from remaining rooms that don't already have locked doors
        remaining_rooms = [pos for pos in all_rooms 
                          if not hasattr(self.connections[pos], 'locked_door_types')]
        if len(remaining_rooms) < num_blocked_passages:
            # Add more rooms if needed
            additional_rooms = [pos for pos in all_rooms if pos not in selected_rooms_for_doors]
            num_additional_needed = num_blocked_passages - len(remaining_rooms)
            if num_additional_needed > 0 and len(additional_rooms) > 0:
                num_to_select = min(num_additional_needed, len(additional_rooms))
                additional_selected = random.sample(additional_rooms, num_to_select)
            remaining_rooms.extend(additional_selected)
        
        selected_rooms_for_passages = random.sample(remaining_rooms, min(num_blocked_passages, len(remaining_rooms)))
        
        for pos in selected_rooms_for_passages:
            room_connection = self.connections[pos]
            
            # Add blocked passage - require a specific trigger item
            trigger_types = ["Rune", "Powder", "Crystal", "Stone", "Charm", "Sundial", "Sunday"]
            trigger_required = random.choice(trigger_types)
            if trigger_required == "Sunday":
                # Special case for Sunday
                trigger_name = "Sunday"
            else:
                trigger_name = f"Power {trigger_required}"
            # We'll add a flag to indicate this room has blocked passages
            room_connection.blocked_passage_types = [trigger_name]

    def _create_corridor(self, x1, y1, x2, y2, floor):
        """Create an L-shaped corridor between two points"""
        # Horizontal first, then vertical
        if random.choice([True, False]):  # Random choice of L-shape orientation
            # Horizontal corridor
            min_x, max_x = min(x1, x2), max(x1, x2)
            for x in range(min_x, max_x + 1):
                pos = (x, y1, floor)
                if pos not in self.rooms:
                    self.rooms[pos] = RoomType.HALLWAY
                    self.connections[pos] = RoomConnection()
            
            # Vertical corridor
            min_y, max_y = min(y1, y2), max(y1, y2)
            for y in range(min_y, max_y + 1):
                pos = (x2, y, floor)
                if pos not in self.rooms:
                    self.rooms[pos] = RoomType.HALLWAY
                    self.connections[pos] = RoomConnection()
        else:
            # Vertical first, then horizontal
            # Vertical corridor
            min_y, max_y = min(y1, y2), max(y1, y2)
            for y in range(min_y, max_y + 1):
                pos = (x1, y, floor)
                if pos not in self.rooms:
                    self.rooms[pos] = RoomType.HALLWAY
                    self.connections[pos] = RoomConnection()
            
            # Horizontal corridor
            min_x, max_x = min(x1, x2), max(x1, x2)
            for x in range(min_x, max_x + 1):
                pos = (x, y2, floor)
                if pos not in self.rooms:
                    self.rooms[pos] = RoomType.HALLWAY
                    self.connections[pos] = RoomConnection()

    def visualize_floor(self, floor: int):
        """Visualize a specific floor of the dungeon."""
        print(f"\n--- FLOOR {floor + 1} VISUALIZATION (Seed: {self.seed}) ---")
        
        # Create a grid representation of the floor
        grid = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Mark rooms and special features on the grid
        for (x, y, f), room_type in self.rooms.items():
            if f == floor:
                # Use different symbols for different room types
                symbol = self._get_symbol_for_room_type(room_type)
                if 0 <= x < self.width and 0 <= y < self.height:
                    grid[y][x] = symbol
        
        # Print the grid
        for row in grid:
            print(''.join(row))
        
        # Print legend
        print("\nLegend:")
        print("     = Empty/Corridor")
        print("  $ = Treasure Room")
        print("  M = Monster Room")
        print("  T = Trap Room")
        print("  N = NPC Room")
        print("  A = Artifact Room")
        print("  S = Staircase")
        print("  L = Locked Door")
        print("  B = Blocked Passage")
    
    def _get_symbol_for_room_type(self, room_type: RoomType) -> str:
        """Get a symbol for a room type."""
        symbols = {
            RoomType.EMPTY: '.',
            RoomType.HALLWAY: '-',
            RoomType.TREASURE: '$',
            RoomType.MONSTER: 'M',
            RoomType.TRAP: 'T',
            RoomType.NPC: 'N',
            RoomType.ARTIFACT: 'A',
            RoomType.STAIRCASE: 'S'
        }
        return symbols.get(room_type, '?')
    
    def visualize_all_floors(self):
        """Visualize all floors of the dungeon."""
        for floor in range(self.floors):
            self.visualize_floor(floor)
    
    def get_room_info(self, x: int, y: int, floor: int) -> Optional[str]:
        """Get detailed information about a specific room."""
        pos = (x, y, floor)
        if pos not in self.rooms:
            return None
        
        room_type = self.rooms[pos]
        connection = self.connections[pos]
        
        info = f"Room ({x}, {y}, Floor {floor+1}): {room_type.value}\n"
        
        if connection.has_stairs_up:
            info += "  - Has stairs going UP\n"
        if connection.has_stairs_down:
            info += "  - Has stairs going DOWN\n"
        
        if hasattr(connection, 'locked_door_types'):
            info += f"  - Has locked doors ({connection.locked_door_types[0]})\n"
        
        if hasattr(connection, 'blocked_passage_types'):
            info += f"  - Has blocked passages ({connection.blocked_passage_types[0]})\n"
        
        return info

    class RoomInfo:
        def __init__(self, x, y, width, height, floor):
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.floor = floor
            self.center_x = x + width // 2
            self.center_y = y + height // 2


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python dungeon_visualizer.py <seed> [floor]")
        print("Example: python dungeon_visualizer.py 12345")
        print("         python dungeon_visualizer.py 12345 0  # to visualize only floor 0")
        return
    
    try:
        seed = int(sys.argv[1])
        visualizer = DungeonVisualizer(seed)
        
        if len(sys.argv) > 2:
            floor = int(sys.argv[2])
            if 0 <= floor < visualizer.floors:
                visualizer.visualize_floor(floor)
            else:
                print(f"Floor {floor} is out of range. Valid floors: 0-{visualizer.floors-1}")
        else:
            # Visualize all floors
            visualizer.visualize_all_floors()
    
    except ValueError:
        print("Please provide a valid integer seed.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()