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
                            pos = (rx, ry, floor)
                            
                            # Set room type based on position in room
                            if rx == room_info.x or rx == room_info.x + room_info.width - 1 or \
                               ry == room_info.y or ry == room_info.y + room_info.height - 1:
                                room_type = RoomType.HALLWAY
                            else:
                                # Center cells - determine type
                                rand = random.random()
                                if rand < 0.1:
                                    room_type = RoomType.TREASURE
                                elif rand < 0.3:
                                    room_type = RoomType.MONSTER
                                elif rand < 0.4:
                                    room_type = RoomType.TRAP
                                elif rand < 0.45:  # 5% chance for NPC
                                    room_type = RoomType.NPC
                                else:
                                    room_type = RoomType.EMPTY
                            
                            self.rooms[pos] = room_type
                            self.connections[pos] = RoomConnection()
            
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
                floor_rooms = [(x, y, z) for x, y, z in self.rooms.keys() if z == floor]
                if floor_rooms:
                    artifact_pos = random.choice(floor_rooms)
                    self.rooms[artifact_pos] = RoomType.ARTIFACT

        # Now create connections between adjacent accessible rooms
        for (x, y, floor), room_connection in self.connections.items():
            for dx, dy, direction in [(0, -1, Direction.NORTH), (0, 1, Direction.SOUTH),
                                      (1, 0, Direction.EAST), (-1, 0, Direction.WEST)]:
                neighbor_pos = (x + dx, y + dy, floor)
                if neighbor_pos in self.connections:  # Only connect if the neighbor exists
                    room_connection.connections[direction] = neighbor_pos
                    # Connect back
                    opposite_direction = {
                        Direction.NORTH: Direction.SOUTH,
                        Direction.SOUTH: Direction.NORTH,
                        Direction.EAST: Direction.WEST,
                        Direction.WEST: Direction.EAST,
                        Direction.UP: Direction.DOWN,
                        Direction.DOWN: Direction.UP
                    }[direction]
                    self.connections[neighbor_pos].connections[opposite_direction] = (x, y, floor)
        
        # Add stairs between floors (using special room flags)
        # Ensure at least one staircase exists between each pair of floors
        for floor in range(self.floors - 1):  # Connect each floor to the one below it
            # Find a room on the current floor that is accessible (has connections)
            current_floor_rooms_with_connections = []
            next_floor_rooms_with_connections = []
            
            for pos, room_connection in self.connections.items():
                if pos[2] == floor and len(room_connection.connections) > 0:  # Room is on current floor and has connections
                    current_floor_rooms_with_connections.append(pos)
            
            for pos, room_connection in self.connections.items():
                if pos[2] == floor + 1 and len(room_connection.connections) > 0:  # Room is on next floor and has connections
                    next_floor_rooms_with_connections.append(pos)
            
            if current_floor_rooms_with_connections and next_floor_rooms_with_connections:
                # Pick a connected room from each floor to place stairs
                current_room_pos = current_floor_rooms_with_connections[0]  # Use first accessible room
                next_room_pos = next_floor_rooms_with_connections[0]  # Use first accessible room on next floor
                
                current_room_connection = self.connections[current_room_pos]
                next_room_connection = self.connections[next_room_pos]
                
                # Mark rooms as having stairs and set targets
                current_room_connection.has_stairs_down = True
                current_room_connection.stairs_down_target = next_room_pos  # Going down leads to next floor room
                next_room_connection.has_stairs_up = True
                next_room_connection.stairs_up_target = current_room_pos   # Going up leads back to current floor room

        # Add locked doors and blocked passages for puzzle elements
        all_accessible_rooms = [pos for pos, conn in self.connections.items() if len(conn.connections) > 0]
        
        # Add some locked doors (about 10% of accessible rooms)
        num_locked_doors = max(1, len(all_accessible_rooms) // 10)
        selected_rooms_for_doors = random.sample(all_accessible_rooms, min(num_locked_doors, len(all_accessible_rooms)))
        
        for pos in selected_rooms_for_doors:
            room_connection = self.connections[pos]
            
            # Find a direction that has a connection but isn't stairs
            available_directions = []
            for direction, connected_pos in room_connection.connections.items():
                # Don't lock stair directions
                if not ((direction == Direction.UP and room_connection.has_stairs_up) or 
                       (direction == Direction.DOWN and room_connection.has_stairs_down)):
                    available_directions.append(direction)
            
            if available_directions:
                direction_to_lock = random.choice(available_directions)
                # Add locked door - require a specific key type
                key_types = ["Iron Key", "Silver Key", "Golden Key", "Ancient Key", "Crystal Key"]
                key_required = random.choice(key_types)
                room_connection.locked_doors[direction_to_lock] = key_required

        # Add some blocked passages (about 5% of accessible rooms)
        num_blocked_passages = max(1, len(all_accessible_rooms) // 20)
        # Select from remaining rooms that don't already have locked doors
        remaining_rooms = [pos for pos in selected_rooms_for_doors 
                          if len(self.connections[pos].locked_doors) == 0]
        if len(remaining_rooms) < num_blocked_passages:
            # Add more rooms if needed
            additional_rooms = [pos for pos in all_accessible_rooms if pos not in selected_rooms_for_doors]
            num_additional_needed = num_blocked_passages - len(remaining_rooms)
            if num_additional_needed > 0 and len(additional_rooms) > 0:
                num_to_select = min(num_additional_needed, len(additional_rooms))
                additional_selected = random.sample(additional_rooms, num_to_select)
                remaining_rooms.extend(additional_selected)
        
        selected_rooms_for_passages = random.sample(remaining_rooms, min(num_blocked_passages, len(remaining_rooms)))
        
        for pos in selected_rooms_for_passages:
            room_connection = self.connections[pos]
            
            # Find a direction that has a connection
            available_directions = [d for d in room_connection.connections.keys() 
                                  if not ((d == Direction.UP and room_connection.has_stairs_up) or 
                                         (d == Direction.DOWN and room_connection.has_stairs_down))]
            
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
                room_connection.blocked_passages[direction_to_block] = trigger_name

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
        grid = [['.' for _ in range(self.width)] for _ in range(self.height)]
        
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
        print("  . = Empty/Hallway")
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
            RoomType.HALLWAY: '.',
            RoomType.TREASURE: '$',
            RoomType.MONSTER: 'M',
            RoomType.TRAP: 'T',
            RoomType.NPC: 'N',
            RoomType.ARTIFACT: 'A'
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
        
        if connection.locked_doors:
            for direction, key in connection.locked_doors.items():
                info += f"  - {direction.value} locked (need {key})\n"
        
        if connection.blocked_passages:
            for direction, item in connection.blocked_passages.items():
                info += f"  - {direction.value} blocked (need {item})\n"
        
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