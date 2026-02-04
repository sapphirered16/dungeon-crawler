"""
Improved dungeon generator with more thematic variety
"""

import random
from enum import Enum
from typing import List, Dict, Optional, Tuple
from game_engine import Room, Enemy, Item, ItemType, Direction


class RoomTheme(Enum):
    """Different thematic room types"""
    CAVERN = "cavern"
    CASTLE = "castle"
    FOREST = "forest"
    UNDERWATER = "underwater"
    MAGICAL = "magical"
    GENERIC = "generic"


class ThemedRoom(Room):
    """Extended Room class with thematic elements"""
    def __init__(self, x: int, y: int, floor: int, theme: RoomTheme = RoomTheme.GENERIC):
        super().__init__(x, y, floor)
        self.theme = theme
        self.thematic_description = self._generate_thematic_description()
        self.environmental_effects = self._generate_environmental_effects()
    
    def _generate_thematic_description(self):
        """Generate a thematic description based on the room theme"""
        descriptions = {
            RoomTheme.CAVERN: [
                "A dark cavern with water dripping from stalactites.",
                "Rough stone walls surround this underground chamber.",
                "Echoes bounce off the cave walls.",
                "Ancient markings are etched into the rocky surface.",
                "The air is cool and damp."
            ],
            RoomTheme.CASTLE: [
                "Stone walls with banners hanging from the ceiling.",
                "Torchlight flickers against the ancient stones.",
                "Footsteps echo in the stone corridor.",
                "Dust covers the cobblestone floor.",
                "Arrow slits let in dim light from outside."
            ],
            RoomTheme.FOREST: [
                "Sunlight filters through a canopy of leaves.",
                "Moss grows on fallen logs and rocks.",
                "Birds chirp in the distance.",
                "Fresh earth scent fills the air.",
                "Vines and roots twist through the space."
            ],
            RoomTheme.UNDERWATER: [
                "Crystalline formations glow softly underwater.",
                "Fish swim past the magical bubble.",
                "Water flows gently through this chamber.",
                "Seaweed sways with the current.",
                "Pearlescent shells decorate the walls."
            ],
            RoomTheme.MAGICAL: [
                "Shimmering runes float in the air.",
                "Crystals pulse with magical energy.",
                "The laws of physics seem different here.",
                "Spells linger in the atmosphere.",
                "Magical energies swirl around you."
            ],
            RoomTheme.GENERIC: [
                "A standard dungeon room.",
                "An ordinary chamber.",
                "A typical room in the dungeon.",
                "Nothing special about this area.",
                "A basic room in the complex."
            ]
        }
        return random.choice(descriptions[self.theme])
    
    def _generate_environmental_effects(self):
        """Generate environmental effects based on theme"""
        effects = {
            RoomTheme.CAVERN: {
                "light_level": "dim",
                "acoustic": "echoing",
                "movement_penalty": 0
            },
            RoomTheme.CASTLE: {
                "light_level": "moderate",
                "acoustic": "standard",
                "movement_penalty": 0
            },
            RoomTheme.FOREST: {
                "light_level": "dappled",
                "acoustic": "rustling",
                "movement_penalty": 0
            },
            RoomTheme.UNDERWATER: {
                "light_level": "dim",
                "acoustic": "muffled",
                "movement_penalty": 1  # Slower movement underwater
            },
            RoomTheme.MAGICAL: {
                "light_level": "bright",
                "acoustic": "humming",
                "movement_penalty": 0
            },
            RoomTheme.GENERIC: {
                "light_level": "standard",
                "acoustic": "standard",
                "movement_penalty": 0
            }
        }
        return effects.copy()


class ImprovedDungeonGenerator:
    """Enhanced dungeon generator with thematic variety"""
    
    def __init__(self, width: int = 30, height: int = 30, floors: int = 3):
        self.width = width
        self.height = height
        self.floors = floors
        self.rooms: Dict[Tuple[int, int, int], ThemedRoom] = {}
        self.room_layouts = {}
    
    def generate_dungeon(self):
        """Generate a themed dungeon with varied room types"""
        # Themes for each floor to create distinct sections
        floor_themes = [
            RoomTheme.CASTLE,    # Floor 1 - Castle ruins
            RoomTheme.CAVERN,    # Floor 2 - Underground caverns
            RoomTheme.MAGICAL    # Floor 3 - Magical realm
        ]
        
        for floor in range(self.floors):
            theme = floor_themes[floor % len(floor_themes)]
            
            # Create rooms with thematic variety
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
                    
                    # Create themed rooms for each cell in the room rectangle
                    for rx in range(room_info.x, room_info.x + room_info.width):
                        for ry in range(room_info.y, room_info.y + room_info.height):
                            # Vary the theme slightly within the floor
                            cell_theme = theme
                            if random.random() < 0.1:  # 10% chance of variation
                                # Pick a random theme that's not the main one
                                other_themes = [t for t in RoomTheme if t != theme]
                                if other_themes:
                                    cell_theme = random.choice(other_themes)
                            
                            room = ThemedRoom(rx, ry, floor, cell_theme)
                            
                            # Set room type based on position in room
                            if rx == room_info.x or rx == room_info.x + room_info.width - 1 or \
                               ry == room_info.y or ry == room_info.y + room_info.height - 1:
                                room.room_type = "hallway"  # Border cells treated as hallway
                            else:
                                # Center cells - determine type
                                rand = random.random()
                                if rand < 0.1:
                                    room.room_type = "treasure"
                                elif rand < 0.3:
                                    room.room_type = "monster"
                                elif rand < 0.4:
                                    room.room_type = "trap"
                                elif rand < 0.45:  # 5% chance for NPC with quest
                                    room.room_type = "npc"
                                else:
                                    room.room_type = "empty"
                            
                            # Add thematic content based on room type and theme
                            self._add_thematic_content(room)
                            
                            self.rooms[(rx, ry, floor)] = room
            
            # Connect rooms with hallways
            for i in range(len(rooms_info) - 1):
                room1 = rooms_info[i]
                room2 = rooms_info[i + 1]
                
                # Create L-shaped corridor between room centers
                self._create_corridor(room1.center_x, room1.center_y, 
                                    room2.center_x, room2.center_y, floor)
            
            # Ensure good connectivity
            if len(rooms_info) > 1:
                for i in range(len(rooms_info)):
                    j = random.randint(0, len(rooms_info) - 1)
                    if i != j:
                        self._create_corridor(rooms_info[i].center_x, rooms_info[i].center_y,
                                            rooms_info[j].center_x, rooms_info[j].center_y, floor)
        
        # Now create connections between adjacent accessible rooms
        for (x, y, floor), room in self.rooms.items():
            for dx, dy, direction in [(0, -1, Direction.NORTH), (0, 1, Direction.SOUTH),
                                      (1, 0, Direction.EAST), (-1, 0, Direction.WEST)]:
                neighbor_pos = (x + dx, y + dy, floor)
                if neighbor_pos in self.rooms:  # Only connect if the neighbor exists
                    room.connect(direction, self.rooms[neighbor_pos])
        
        # Add stairs between floors
        self._add_floor_connections()
        
        # Add locked doors and blocked passages for puzzle elements
        self._add_puzzle_elements()
    
    def _add_thematic_content(self, room: ThemedRoom):
        """Add thematic content to a room based on its type and theme"""
        if room.room_type == "treasure":
            # Add themed treasure based on room theme
            if room.theme == RoomTheme.MAGICAL:
                room.items.append(self._generate_magical_item())
            elif room.theme == RoomTheme.CAVERN:
                room.items.append(self._generate_cavern_item())
            else:
                room.items.append(self._generate_generic_treasure())
        
        elif room.room_type == "monster":
            # Add themed enemies based on room theme
            enemy = self._generate_themed_enemy(room.theme, room.floor)
            room.entities.append(enemy)
        
        elif room.room_type == "trap":
            # Add environmental hazards based on theme
            if room.theme == RoomTheme.CAVERN:
                trap_desc = "A pit trap camouflaged with loose stones."
            elif room.theme == RoomTheme.CASTLE:
                trap_desc = "Pressure plates that trigger crossbow bolts."
            elif room.theme == RoomTheme.MAGICAL:
                trap_desc = "A magical ward that discharges energy."
            else:
                trap_desc = "A simple snare trap."
            
            # Add trap as an item or environmental effect
            trap_item = Item(f"{room.theme.value.title()} Trap", ItemType.CONSUMABLE, value=0)
            room.items.append(trap_item)
    
    def _generate_magical_item(self):
        """Generate a magical-themed item"""
        magical_items = [
            ("Enchanted Crystal", ItemType.WEAPON, 50, 10, 2, 0, "magical"),
            ("Wizard's Robe", ItemType.ARMOR, 40, 2, 5, 15, "magical"),
            ("Potion of Healing", ItemType.CONSUMABLE, 20, 0, 0, 25, "healing"),
            ("Spell Scroll", ItemType.CONSUMABLE, 30, 15, 0, 0, "magic_boost")
        ]
        item_data = random.choice(magical_items)
        name, item_type, value, atk, df, hp, special = item_data
        return Item(name, item_type, value, atk, df, hp, special)
    
    def _generate_cavern_item(self):
        """Generate a cavern-themed item"""
        cavern_items = [
            ("Glowing Mushroom", ItemType.CONSUMABLE, 10, 0, 0, 10, "illumination"),
            ("Cave Pearl", ItemType.CONSUMABLE, 25, 0, 0, 0, "valuable"),
            ("Stone Club", ItemType.WEAPON, 15, 8, 0, 0, "heavy"),
            ("Leather Wrapped Shield", ItemType.ARMOR, 20, 0, 7, 5, "protective")
        ]
        item_data = random.choice(cavern_items)
        name, item_type, value, atk, df, hp, special = item_data
        return Item(name, item_type, value, atk, df, hp, special)
    
    def _generate_generic_treasure(self):
        """Generate a generic treasure item"""
        treasures = [
            ("Gold Coin", ItemType.CONSUMABLE, 5, 0, 0, 0),
            ("Health Potion", ItemType.CONSUMABLE, 15, 0, 0, 20),
            ("Iron Sword", ItemType.WEAPON, 30, 12, 0, 0),
            ("Leather Armor", ItemType.ARMOR, 25, 0, 8, 10)
        ]
        name, item_type, value, atk, df, hp = random.choice(treasures)
        return Item(name, item_type, value, atk, df, hp)
    
    def _generate_themed_enemy(self, theme: RoomTheme, floor: int):
        """Generate an enemy themed to the room"""
        # Base stats scaled by floor
        scale_factor = 1 + (floor * 0.3)
        
        if theme == RoomTheme.CAVERN:
            enemies = [
                ("Cave Bat", int(15 * scale_factor), int(6 * scale_factor), int(1 * scale_factor), int(15 * scale_factor), 1, 3),
                ("Rock Golem", int(40 * scale_factor), int(10 * scale_factor), int(8 * scale_factor), int(40 * scale_factor), 3, 7),
                ("Cave Troll", int(35 * scale_factor), int(12 * scale_factor), int(5 * scale_factor), int(35 * scale_factor), 2, 6)
            ]
        elif theme == RoomTheme.MAGICAL:
            enemies = [
                ("Shadow Wraith", int(25 * scale_factor), int(8 * scale_factor), int(2 * scale_factor), int(25 * scale_factor), 2, 5),
                ("Magical Construct", int(30 * scale_factor), int(9 * scale_factor), int(6 * scale_factor), int(30 * scale_factor), 3, 6),
                ("Arcane Elemental", int(35 * scale_factor), int(11 * scale_factor), int(4 * scale_factor), int(35 * scale_factor), 4, 8)
            ]
        elif theme == RoomTheme.CASTLE:
            enemies = [
                ("Skeleton Warrior", int(20 * scale_factor), int(7 * scale_factor), int(3 * scale_factor), int(20 * scale_factor), 2, 5),
                ("Ghost Knight", int(30 * scale_factor), int(10 * scale_factor), int(4 * scale_factor), int(30 * scale_factor), 3, 7),
                ("Animated Armor", int(35 * scale_factor), int(8 * scale_factor), int(7 * scale_factor), int(35 * scale_factor), 4, 8)
            ]
        else:
            # Generic enemies
            enemies = [
                ("Goblin", int(18 * scale_factor), int(6 * scale_factor), int(1 * scale_factor), int(18 * scale_factor), 1, 4),
                ("Orc", int(30 * scale_factor), int(9 * scale_factor), int(4 * scale_factor), int(30 * scale_factor), 3, 7),
                ("Zombie", int(25 * scale_factor), int(7 * scale_factor), int(2 * scale_factor), int(25 * scale_factor), 1, 5)
            ]
        
        enemy_data = random.choice(enemies)
        name, health, attack, defense, exp, gold_min, gold_max = enemy_data
        
        return Enemy(name, health, attack, defense, exp, gold_min, gold_max)
    
    def _create_corridor(self, x1, y1, x2, y2, floor):
        """Create an L-shaped corridor between two points"""
        # Horizontal first, then vertical
        if random.choice([True, False]):  # Random choice of L-shape orientation
            # Horizontal corridor
            min_x, max_x = min(x1, x2), max(x1, x2)
            for x in range(min_x, max_x + 1):
                pos = (x, y1, floor)
                if pos not in self.rooms:
                    # Randomly assign a theme to corridors
                    theme = random.choice(list(RoomTheme))
                    room = ThemedRoom(x, y1, floor, theme)
                    room.room_type = "hallway"
                    self.rooms[pos] = room
            
            # Vertical corridor
            min_y, max_y = min(y1, y2), max(y1, y2)
            for y in range(min_y, max_y + 1):
                pos = (x2, y, floor)
                if pos not in self.rooms:
                    theme = random.choice(list(RoomTheme))
                    room = ThemedRoom(x2, y, floor, theme)
                    room.room_type = "hallway"
                    self.rooms[pos] = room
        else:
            # Vertical first, then horizontal
            # Vertical corridor
            min_y, max_y = min(y1, y2), max(y1, y2)
            for y in range(min_y, max_y + 1):
                pos = (x1, y, floor)
                if pos not in self.rooms:
                    theme = random.choice(list(RoomTheme))
                    room = ThemedRoom(x1, y, floor, theme)
                    room.room_type = "hallway"
                    self.rooms[pos] = room
            
            # Horizontal corridor
            min_x, max_x = min(x1, x2), max(x1, x2)
            for x in range(min_x, max_x + 1):
                pos = (x, y2, floor)
                if pos not in self.rooms:
                    theme = random.choice(list(RoomTheme))
                    room = ThemedRoom(x, y2, floor, theme)
                    room.room_type = "hallway"
                    self.rooms[pos] = room

    def _add_floor_connections(self):
        """Add stairs between floors, placing them in more challenging locations"""
        for floor in range(self.floors - 1):  # Connect each floor to the one below it
            # Find a room on the current floor that is accessible
            current_floor_rooms_with_connections = []
            next_floor_rooms_with_connections = []
            
            for pos, room in self.rooms.items():
                if pos[2] == floor and len(room.connections) > 0:
                    current_floor_rooms_with_connections.append(pos)
            
            for pos, room in self.rooms.items():
                if pos[2] == floor + 1 and len(room.connections) > 0:
                    next_floor_rooms_with_connections.append(pos)
            
            if current_floor_rooms_with_connections and next_floor_rooms_with_connections:
                # Instead of using the first room (which might be near the start), 
                # select a room that's deeper in the dungeon by choosing from the middle/later half
                # Sort rooms by their position to simulate depth (using Manhattan distance from origin)
                sorted_rooms = sorted(current_floor_rooms_with_connections, 
                                    key=lambda pos: abs(pos[0]) + abs(pos[1]))
                
                # Select a room from the latter half of the sorted list (deeper in dungeon)
                if len(sorted_rooms) > 1:
                    # Choose from the last third of rooms to ensure it's not near the start
                    start_idx = max(0, len(sorted_rooms) - max(1, len(sorted_rooms) // 3))
                    current_room_pos = random.choice(sorted_rooms[start_idx:])
                else:
                    current_room_pos = current_floor_rooms_with_connections[0]
                
                # For the next floor, place the stairs up in a non-starting area as well
                sorted_next_rooms = sorted(next_floor_rooms_with_connections, 
                                        key=lambda pos: abs(pos[0]) + abs(pos[1]))
                
                if len(sorted_next_rooms) > 1:
                    start_idx = max(0, len(sorted_next_rooms) - max(1, len(sorted_next_rooms) // 3))
                    next_room_pos = random.choice(sorted_next_rooms[start_idx:])
                else:
                    next_room_pos = next_floor_rooms_with_connections[0]
                
                current_room = self.rooms[current_room_pos]
                next_room = self.rooms[next_room_pos]
                
                # Mark rooms as having stairs
                current_room.has_stairs_down = True
                current_room.stairs_down_target = next_room
                next_room.has_stairs_up = True
                next_room.stairs_up_target = current_room

    def _add_puzzle_elements(self):
        """Add locked doors and blocked passages"""
        all_accessible_rooms = [room for room in self.rooms.values() if len(room.connections) > 0]
        
        # Add locked doors (about 8% of accessible rooms)
        num_locked_doors = max(1, len(all_accessible_rooms) // 12)
        selected_rooms_for_doors = random.sample(all_accessible_rooms, min(num_locked_doors, len(all_accessible_rooms)))
        
        for room in selected_rooms_for_doors:
            available_directions = []
            for direction, connected_room in room.connections.items():
                if not ((direction == Direction.UP and room.has_stairs_up) or 
                       (direction == Direction.DOWN and room.has_stairs_down)):
                    available_directions.append(direction)
            
            if available_directions:
                direction_to_lock = random.choice(available_directions)
                key_types = ["Iron Key", "Silver Key", "Golden Key", "Themed Key", "Mystic Key"]
                key_required = random.choice(key_types)
                
                # Make key name thematic if possible
                if room.theme != RoomTheme.GENERIC:
                    key_required = f"{room.theme.value.title()} {key_required.replace('Themed ', '')}"
                
                room.locked_doors[direction_to_lock] = key_required
                
                # Add the corresponding key to some other room
                other_rooms = [r for r in all_accessible_rooms if r != room]
                if other_rooms:
                    key_room = random.choice(other_rooms)
                    key_item = Item(name=key_required, item_type=ItemType.KEY, value=15)
                    key_room.items.append(key_item)

    class RoomInfo:
        def __init__(self, x, y, width, height, floor):
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.floor = floor
            self.center_x = x + width // 2
            self.center_y = y + height // 2


# Example usage
if __name__ == "__main__":
    generator = ImprovedDungeonGenerator(width=25, height=25, floors=3)
    generator.generate_dungeon()
    
    print(f"Dungeon generated with {len(generator.rooms)} rooms across {generator.floors} floors")
    
    # Show a sample of rooms
    sample_rooms = list(generator.rooms.items())[:5]
    for pos, room in sample_rooms:
        print(f"Room at {pos}: Theme={room.theme.value}, Type={room.room_type}, Description='{room.thematic_description}'")