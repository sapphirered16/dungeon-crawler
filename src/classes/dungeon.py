"""Dungeon class for the dungeon crawler game with proper room-based layouts."""

import random
from typing import Dict, List, Tuple, Any, Set
from .room import RoomState
from .item import Item
from .base import ItemType, Direction
from .map_effects import MapEffect, MapEffectType, MapEffectManager
from ..data.data_loader import DataProvider


class Rect:
    """Rectangle class to represent rooms with dimensions."""
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    @property
    def left(self):
        return self.x
    
    @property
    def right(self):
        return self.x + self.width
    
    @property
    def top(self):
        return self.y
    
    @property
    def bottom(self):
        return self.y + self.height
    
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def intersects(self, other) -> bool:
        """Check if this rectangle intersects with another."""
        return (
            self.left < other.right and
            self.right > other.left and
            self.top < other.bottom and
            self.bottom > other.top
        )


class Room:
    """Represents a room with dimensions and position."""
    def __init__(self, rect: Rect, room_type: str = "empty", floor: int = 0):
        self.rect = rect
        self.room_type = room_type
        self.floor = floor
        self.center_x, self.center_y = rect.center()
        self.id = f"{self.center_x}_{self.center_y}_{floor}"  # Unique identifier
    
    def contains(self, x: int, y: int) -> bool:
        """Check if coordinates are inside this room."""
        return (self.rect.x <= x < self.rect.x + self.rect.width and 
                self.rect.y <= y < self.rect.y + self.rect.height)


class Hallway:
    """Represents a hallway connection between two rooms."""
    def __init__(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], floor: int = 0):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.floor = floor
        self.path = self._calculate_path()
    
    def _calculate_path(self) -> List[Tuple[int, int]]:
        """Calculate L-shaped path between two points."""
        start_x, start_y = self.start_pos
        end_x, end_y = self.end_pos
        
        path = []
        # Horizontal segment
        if start_x < end_x:
            for x in range(start_x, end_x + 1):
                path.append((x, start_y))
        else:
            for x in range(start_x, end_x - 1, -1):
                path.append((x, start_y))
        
        # Vertical segment
        if start_y != end_y:
            # Start from the end of horizontal segment
            intermediate_x = end_x
            if start_y < end_y:
                for y in range(start_y + 1, end_y + 1):
                    path.append((intermediate_x, y))
            else:
                for y in range(start_y - 1, end_y - 1, -1):
                    path.append((intermediate_x, y))
        
        return path


class SeededDungeon:
    def __init__(self, seed: int = None, grid_width: int = 30, grid_height: int = 30, min_spacing: int = 1):
        if seed is not None:
            random.seed(seed)
        self.seed = seed
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.min_spacing = min_spacing  # Minimum space between rooms
        self.room_states = {}  # {(x, y, z): RoomState}
        self.rooms_by_id = {}  # {room_id: Room}
        self.hallways = []  # List of Hallway objects
        self.map_effects = MapEffectManager()
        self.data_provider = DataProvider()
        self.generate_dungeon()

    def generate_dungeon(self):
        """Generate the dungeon layout with actual room dimensions and hallways."""
        # Load room templates
        room_templates = self.data_provider.get_room_templates()
        
        # Determine number of floors based on room templates
        num_floors = self._determine_number_of_floors(room_templates)
        
        # Generate rooms for multiple floors
        for floor in range(num_floors):
            self._generate_floor(floor, floor == 0)  # Mark first floor as starting floor
        
        # Connect rooms with hallways
        self._connect_rooms_with_hallways()
        
        # Establish tile-to-tile connections for movement
        self._establish_tile_connections()
        
        # Ensure stairs are properly connected between all floors
        self._connect_stairs_properly()

    def _determine_number_of_floors(self, room_templates):
        """Determine number of floors based on room template constraints and content diversity."""
        # Analyze the room templates and other data sources to determine appropriate number of floors
        
        # The room_templates is a dict with 'room_templates' key containing the list of templates
        actual_templates = room_templates['room_templates']
        
        # Check if we have data that suggests floor ranges
        # For now, we'll use a combination of factors:
        # 1. Diversity of room types
        # 2. Thematic variety
        # 3. Content availability
        
        # Count different room types
        room_types = set(template["type"] for template in actual_templates)
        
        # Count different themes
        all_themes = set()
        for template in actual_templates:
            all_themes.update(template["themes"])
        
        # Based on the diversity of content, suggest an appropriate number of floors
        # More diverse content can support more floors with thematic variety
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
    
    def _connect_stairs_properly(self):
        """Ensure stairs are properly connected between floors."""
        # Determine the total number of floors from the generated dungeon
        all_floors = set(pos[2] for pos in self.room_states.keys())
        max_floor = max(all_floors) if all_floors else 0
        min_floor = min(all_floors) if all_floors else 0
        
        # Connect stairs between each consecutive pair of floors
        for floor in range(max_floor):  # Connect floors 0->1, 1->2, ..., (n-1)->n
            # Get all rooms on current floor
            current_floor_rooms = [pos for pos in self.room_states.keys() if pos[2] == floor]
            next_floor_rooms = [pos for pos in self.room_states.keys() if pos[2] == floor + 1]
            
            if current_floor_rooms and next_floor_rooms:
                # Select a room from current floor to have stairs down
                from_room_pos = random.choice(current_floor_rooms)
                # Select a room from next floor to have stairs up
                to_room_pos = random.choice(next_floor_rooms)
                
                # Connect them
                self.room_states[from_room_pos].has_stairs_down = True
                self.room_states[from_room_pos].stairs_down_target = to_room_pos
                self.room_states[to_room_pos].has_stairs_up = True
                self.room_states[to_room_pos].stairs_up_target = from_room_pos
        
        # Ensure there's a special artifact room on the deepest (highest-numbered) floor as the win condition
        deepest_floor_rooms = [pos for pos in self.room_states.keys() if pos[2] == max_floor]
        if deepest_floor_rooms:
            # Select a room on the deepest floor to be the special artifact room
            artifact_room_pos = random.choice(deepest_floor_rooms)
            artifact_room = self.room_states[artifact_room_pos]
            
            # Change this room to be an artifact room if it isn't already
            artifact_room.room_type = "artifact"
            artifact_room.description = "The ultimate treasure chamber. The final resting place of a powerful artifact."
            
            # Clear any existing items and ensure it has a proper artifact
            artifact_room.items.clear()
            artifact = self._generate_artifact()
            artifact_room.add_item(artifact)
    
    def _generate_floor(self, floor: int, is_starting_floor: bool = False):
        """Generate a single floor with actual dimensional rooms."""
        # Create a list of rooms for this floor
        rooms = []
        
        # Generate room dimensions and positions
        num_rooms = random.randint(15, 25)  # Fewer rooms due to larger size
        
        # Define possible room dimensions (width, height)
        room_sizes = [(3, 3), (4, 3), (3, 4), (4, 4), (5, 4), (4, 5), (5, 5), (6, 4), (4, 6)]
        
        # First, create the starting/hub room if this is the starting floor
        if is_starting_floor:
            start_width, start_height = random.choice([(4, 4), (5, 4), (4, 5)])
            start_x = self.grid_width // 2 - start_width // 2
            start_y = self.grid_height // 2 - start_height // 2
            start_rect = Rect(start_x, start_y, start_width, start_height)
            start_room = Room(start_rect, "hub", floor)
            rooms.append(start_room)
            self.rooms_by_id[start_room.id] = start_room
        
        # Generate remaining rooms
        attempts = 0
        max_attempts = 1000  # Prevent infinite loops
        
        while len(rooms) < num_rooms and attempts < max_attempts:
            attempts += 1
            
            # Choose room dimensions
            width, height = random.choice(room_sizes)
            
            # Try to place the room randomly on the grid
            max_x = self.grid_width - width - self.min_spacing * 2
            max_y = self.grid_height - height - self.min_spacing * 2
            
            if max_x <= 0 or max_y <= 0:
                continue  # Grid too small for this room size
                
            x = random.randint(self.min_spacing, max_x)
            y = random.randint(self.min_spacing, max_y)
            
            new_rect = Rect(x, y, width, height)
            
            # Check if this rectangle intersects with any existing room
            valid_placement = True
            for existing_room in rooms:
                # Calculate expanded rectangles to account for minimum spacing
                expanded_new = Rect(
                    new_rect.x - self.min_spacing,
                    new_rect.y - self.min_spacing,
                    new_rect.width + 2 * self.min_spacing,
                    new_rect.height + 2 * self.min_spacing
                )
                
                if expanded_new.intersects(existing_room.rect):
                    valid_placement = False
                    break
            
            if valid_placement:
                # Determine room type (avoid "artifact" for initial generation)
                room_types = ["empty", "treasure", "monster", "trap", "npc", 
                             "storage", "bunk", "kitchen", "library", "workshop", "garden"]
                room_type = random.choice(room_types)
                
                new_room = Room(new_rect, room_type, floor)
                rooms.append(new_room)
                self.rooms_by_id[new_room.id] = new_room
        
        # Create RoomState objects for each tile in each room
        for room in rooms:
            for x in range(room.rect.x, room.rect.x + room.rect.width):
                for y in range(room.rect.y, room.rect.y + room.rect.height):
                    pos = (x, y, floor)
                    room_state = RoomState(pos, room.room_type)
                    room_state.description = self._get_room_description(room.room_type)
                    self.room_states[pos] = room_state
        
        # Add special features to the floor
        self._add_special_features(floor)

    def _get_room_description(self, room_type: str) -> str:
        """Generate a description for a room based on its type."""
        descriptions = {
            "hub": "A central hub of this floor.",
            "empty": "An empty, quiet room.",
            "treasure": "A room filled with treasures and valuable items.",
            "monster": "A room that houses dangerous creatures.",
            "trap": "A room that seems to contain hidden dangers.",
            "npc": "A room occupied by a non-player character.",
            "storage": "A storage area filled with various items.",
            "bunk": "A sleeping area with beds and personal belongings.",
            "kitchen": "A kitchen with cooking utensils and ingredients.",
            "library": "A library filled with books and scrolls.",
            "workshop": "A workshop with tools and crafting materials.",
            "garden": "A garden with plants and herbs growing in it."
        }
        return descriptions.get(room_type, "An unremarkable room.")
    
    def _connect_rooms_with_hallways(self):
        """Connect rooms with hallways using minimum spanning tree approach."""
        # Get all rooms grouped by floor
        rooms_by_floor = {}
        for room_id, room in self.rooms_by_id.items():
            if room.floor not in rooms_by_floor:
                rooms_by_floor[room.floor] = []
            rooms_by_floor[room.floor].append(room)
        
        # For each floor, connect rooms
        for floor, rooms in rooms_by_floor.items():
            if len(rooms) < 2:
                continue  # Need at least 2 rooms to connect
            
            # Create a list of all possible connections with their costs
            connections = []
            for i, room1 in enumerate(rooms):
                for j, room2 in enumerate(rooms[i+1:], i+1):
                    center1 = room1.rect.center()
                    center2 = room2.rect.center()
                    cost = abs(center1[0] - center2[0]) + abs(center1[1] - center2[1])  # Manhattan distance
                    connections.append((cost, room1, room2))
            
            # Sort connections by cost (first element of tuple)
            connections.sort(key=lambda x: x[0])
            
            # Use Union-Find to create minimum spanning tree
            parent = {room.id: room.id for room in rooms}
            
            def find_parent(room_id):
                if parent[room_id] != room_id:
                    parent[room_id] = find_parent(parent[room_id])
                return parent[room_id]
            
            def union(room1_id, room2_id):
                root1 = find_parent(room1_id)
                root2 = find_parent(room2_id)
                if root1 != root2:
                    parent[root1] = root2
                    return True
                return False
            
            # Add connections to form MST
            connected_count = 1
            for cost, room1, room2 in connections:
                if union(room1.id, room2.id):
                    hallway = Hallway(room1.rect.center(), room2.rect.center(), floor)
                    self.hallways.append(hallway)
                    
                    # Add hallway tiles to the dungeon map
                    for x, y in hallway.path:
                        pos = (x, y, floor)
                        if pos not in self.room_states:
                            hallway_room = RoomState(pos, "hallway")
                            hallway_room.description = "A narrow hallway connecting different parts of the dungeon."
                            self.room_states[pos] = hallway_room
                    
                    connected_count += 1
                    if connected_count == len(rooms):
                        break  # All rooms are connected

    def _establish_tile_connections(self):
        """Establish directional connections between adjacent tiles."""
        # For each position in the dungeon, check its neighbors and create connections
        for pos, room_state in self.room_states.items():
            x, y, z = pos
            
            # Check all 4 directions (North, South, East, West)
            potential_neighbors = [
                ((x, y - 1, z), Direction.NORTH),  # North
                ((x, y + 1, z), Direction.SOUTH),  # South
                ((x + 1, y, z), Direction.EAST),   # East
                ((x - 1, y, z), Direction.WEST),   # West
            ]
            
            for neighbor_pos, direction in potential_neighbors:
                if neighbor_pos in self.room_states:
                    # Establish bidirectional connection
                    room_state.connections[direction] = neighbor_pos

    def _add_special_features(self, floor: int):
        """Add special features like locked doors, etc. to a floor."""
        positions = [pos for pos in self.room_states.keys() if pos[2] == floor]
        
        # Add 3-5 filler rooms to each floor
        filler_room_types = ["storage", "bunk", "kitchen", "library", "workshop", "garden"]
        num_filler_rooms = random.randint(3, 5)
        
        # Select random positions to convert to filler rooms
        selected_positions = random.sample(positions, min(num_filler_rooms, len(positions)))
        
        for pos in selected_positions:
            # Choose a random filler room type
            filler_type = random.choice(filler_room_types)
            self.room_states[pos].room_type = filler_type
            
            # Get a random description for the chosen room type
            room_templates = self.data_provider.get_room_templates()['room_templates']
            room_template = next((template for template in room_templates if template['type'] == filler_type), None)
            if room_template:
                description = random.choice(room_template['descriptions'])
                self.room_states[pos].description = description
        
        # Add map effects to random positions
        self._add_map_effects(floor)
        
        # Populate rooms with items and entities
        self._populate_floor_rooms(floor)

    def _populate_floor_rooms(self, floor: int):
        """Populate rooms on a floor with items and entities."""
        positions = [pos for pos in self.room_states.keys() if pos[2] == floor]
        
        # Determine the lowest floor in the dungeon
        all_floors = set(pos[2] for pos in self.room_states.keys())
        lowest_floor = min(all_floors) if all_floors else 0
        
        for pos in positions:
            room = self.room_states[pos]
            
            # Add items based on room type
            if room.room_type == "treasure":
                # Add 1-3 treasure items
                for _ in range(random.randint(1, 3)):
                    item = self._generate_random_item()
                    room.add_item(item)
            elif room.room_type == "empty":
                # Small chance to add an item in empty rooms
                if random.random() < 0.2:
                    if random.random() < 0.5:
                        item = self._generate_random_item()
                        room.add_item(item)
            elif room.room_type == "monster":
                # Add monsters
                num_monsters = random.randint(1, 3)
                for _ in range(num_monsters):
                    monster = self._generate_random_enemy(floor)
                    room.add_entity(monster)
                # Maybe add a treasure item too
                if random.random() < 0.3:
                    item = self._generate_random_item()
                    room.add_item(item)
            elif room.room_type == "npc":
                # Add an NPC
                npc = self._generate_random_npc()
                room.add_npc(npc)
            elif room.room_type == "trap":
                # Convert trap rooms to other types, since we now have map effects for traps
                other_types = ["empty", "treasure", "monster", "npc"]
                room.room_type = random.choice(other_types)
            elif room.room_type == "artifact":
                # Add a special artifact ONLY if this is the lowest floor
                if floor == lowest_floor:
                    artifact = self._generate_artifact()
                    room.add_item(artifact)
                else:
                    # If this is not the lowest floor, convert to a different room type
                    other_types = ["empty", "treasure", "monster", "npc"]
                    room.room_type = random.choice(other_types)
            elif room.room_type == "storage":
                # Add 1-3 storage-related items
                for _ in range(random.randint(1, 3)):
                    item = self._generate_random_item()
                    room.add_item(item)
            elif room.room_type == "bunk":
                # Add 1-2 items related to rest/sleep
                for _ in range(random.randint(1, 2)):
                    item = self._generate_random_item()
                    room.add_item(item)
            elif room.room_type == "kitchen":
                # Add food and cooking-related items
                for _ in range(random.randint(1, 3)):
                    item = self._generate_random_item()
                    room.add_item(item)
            elif room.room_type == "library":
                # Add 1-2 knowledge-related items
                for _ in range(random.randint(1, 2)):
                    item = self._generate_random_item()
                    room.add_item(item)
            elif room.room_type == "workshop":
                # Add 1-3 crafting/tool-related items
                for _ in range(random.randint(1, 3)):
                    item = self._generate_random_item()
                    room.add_item(item)
            elif room.room_type == "garden":
                # Add 1-2 plant/herb-related items
                for _ in range(random.randint(1, 2)):
                    item = self._generate_random_item()
                    room.add_item(item)
            elif room.room_type == "hallway":
                # Hallways generally remain empty, but occasionally add minor items
                if random.random() < 0.05:  # 5% chance
                    item = self._generate_random_item()
                    room.add_item(item)
    
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
        from .enemy import Enemy
        
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

    def _generate_trap_item(self) -> Item:
        """Generate an item related to traps."""
        trap_items = [
            ("Thieves' Tools", ItemType.TOOL, 30, "Allows disarming of simple traps"),
            ("Trap Detector", ItemType.TOOL, 50, "Detects hidden traps in adjacent rooms"),
            ("Shield Potion", ItemType.CONSUMABLE, 40, "Provides temporary protection from traps")
        ]
        name, item_type, value, desc = random.choice(trap_items)
        return Item(name, item_type, value, desc)

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
        positions = [pos for pos in self.room_states.keys() if pos[2] == floor]
        
        # Determine number of effects based on floor size
        num_effects = max(1, len(positions) // 5)  # Roughly 1 effect per 5 rooms
        
        for _ in range(num_effects):
            # Select a random position
            pos = random.choice(positions)
            
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
            
            # Create and add the map effect
            effect = MapEffect(
                effect_type=effect_type,
                position=pos,
                trigger_chance=trigger_chance,
                description=description,
                effect_strength=effect_strength
            )
            
            self.map_effects.add_effect(effect)

    def get_room_at(self, pos: Tuple[int, int, int]) -> RoomState:
        """Get the room at a given position."""
        return self.room_states.get(pos)

    def get_room_info(self, pos: Tuple[int, int, int]) -> Dict[str, Any]:
        """Get detailed information about a room at a given position."""
        room_state = self.get_room_at(pos)
        if not room_state:
            return None
        
        # Find which dimensional room this position belongs to
        room_id = f"{pos[0]}_{pos[1]}_{pos[2]}"
        dimensional_room = None
        for room in self.rooms_by_id.values():
            if room.floor == pos[2] and room.contains(pos[0], pos[1]):
                dimensional_room = room
                break
        
        return {
            "room_state": room_state,
            "dimensional_room": dimensional_room,
            "is_hallway": room_state.room_type == "hallway"
        }

    def get_adjacent_positions(self, pos: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
        """Get all adjacent positions to a given position."""
        x, y, z = pos
        adjacent = []
        
        # Check all 4 directions (North, South, East, West)
        potential_moves = [
            (x, y - 1, z),  # North
            (x, y + 1, z),  # South
            (x + 1, y, z),  # East
            (x - 1, y, z),  # West
        ]
        
        for adj_pos in potential_moves:
            if adj_pos in self.room_states:
                adjacent.append(adj_pos)
        
        return adjacent

    def to_dict(self) -> Dict[str, Any]:
        """Convert dungeon to dictionary for saving."""
        return {
            "seed": self.seed,
            "room_states": {str(pos): room.to_dict() for pos, room in self.room_states.items()},
            "map_effects": self.map_effects.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create dungeon from dictionary for loading."""
        dungeon = cls(data["seed"])
        dungeon.room_states = {}
        
        for pos_str, room_data in data["room_states"].items():
            pos = tuple(int(x) for x in pos_str.strip('()').split(','))
            dungeon.room_states[pos] = RoomState.from_dict(room_data)
        
        # Load map effects if they exist
        if "map_effects" in data:
            from .map_effects import MapEffectManager
            dungeon.map_effects = MapEffectManager.from_dict(data["map_effects"])
        else:
            # For backward compatibility, create a new map effects manager
            dungeon.map_effects = MapEffectManager()
        
        return dungeon