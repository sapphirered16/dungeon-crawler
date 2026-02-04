"""Dungeon class for the dungeon crawler game."""

import random
from typing import Dict, List, Tuple, Any
from .room import RoomState
from .item import Item
from .base import ItemType, Direction
from ..data.data_loader import DataProvider


class SeededDungeon:
    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
        self.seed = seed
        self.room_states = {}  # {(x, y, z): RoomState}
        self.data_provider = DataProvider()
        self.generate_dungeon()

    def generate_dungeon(self):
        """Generate the dungeon layout."""
        # Load room templates
        room_templates = self.data_provider.get_room_templates()
        
        # Determine number of floors based on room templates
        # Analyze room templates to determine how many floors are needed
        num_floors = self._determine_number_of_floors(room_templates)
        
        # Create a basic layout with a starting room
        start_pos = (12, 12, 0)  # Starting position
        start_room = RoomState(start_pos, "starting")
        start_room.description = "The entrance to the dungeon. A safe starting area."
        self.room_states[start_pos] = start_room
        
        # Generate rooms for multiple floors
        for floor in range(num_floors):  # Generate floors based on room templates
            self._generate_floor(floor, start_pos if floor == 0 else None)
        
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
    
    def _generate_floor(self, floor: int, starting_pos: Tuple[int, int, int] = None):
        """Generate a single floor of the dungeon."""
        # Determine starting position for this floor
        if floor == 0 and starting_pos:
            current_pos = starting_pos
        else:
            # Offset for new floor
            current_pos = (12, 12, floor)
        
        # Generate room clusters
        num_rooms = random.randint(20, 40)
        
        # Create a central hub for the floor
        if current_pos not in self.room_states:
            hub_room = RoomState(current_pos, "hub")
            hub_room.description = "A central hub of this floor."
            self.room_states[current_pos] = hub_room
        
        # Generate rooms radiating from the hub
        generated_positions = {current_pos}
        
        for _ in range(num_rooms - 1):
            # Find a position adjacent to an existing room
            existing_pos = random.choice(list(generated_positions))
            direction = random.choice(list(Direction))
            
            # Calculate new position
            x, y, z = existing_pos
            if direction == Direction.NORTH:
                new_pos = (x, y - 1, z)
            elif direction == Direction.SOUTH:
                new_pos = (x, y + 1, z)
            elif direction == Direction.EAST:
                new_pos = (x + 1, y, z)
            elif direction == Direction.WEST:
                new_pos = (x - 1, y, z)
            else:
                continue  # Skip up/down for now
            
            # Skip if position already exists
            if new_pos in self.room_states:
                continue
                
            # Create new room
            room_types = ["empty", "treasure", "monster", "trap", "npc", "artifact"]
            room_type = random.choice(room_types)
            
            new_room = RoomState(new_pos, room_type)
            self.room_states[new_pos] = new_room
            generated_positions.add(new_pos)
            
            # Connect the rooms
            self._connect_rooms(existing_pos, new_pos)
        
        # Add special features to the floor
        self._add_special_features(floor)
    
    def _connect_rooms(self, pos1: Tuple[int, int, int], pos2: Tuple[int, int, int]):
        """Connect two adjacent rooms."""
        x1, y1, z1 = pos1
        x2, y2, z2 = pos2
        
        # Determine direction from pos1 to pos2
        if x2 == x1 + 1 and y2 == y1 and z2 == z1:
            direction = Direction.EAST
            opposite = Direction.WEST
        elif x2 == x1 - 1 and y2 == y1 and z2 == z1:
            direction = Direction.WEST
            opposite = Direction.EAST
        elif x2 == x1 and y2 == y1 + 1 and z2 == z1:
            direction = Direction.SOUTH
            opposite = Direction.NORTH
        elif x2 == x1 and y2 == y1 - 1 and z2 == z1:
            direction = Direction.NORTH
            opposite = Direction.SOUTH
        else:
            return  # Not adjacent
        
        # Connect the rooms
        if pos1 in self.room_states:
            self.room_states[pos1].connections[direction] = pos2
        if pos2 in self.room_states:
            self.room_states[pos2].connections[opposite] = pos1

    def _add_special_features(self, floor: int):
        """Add special features like stairs, locked doors, etc. to a floor."""
        positions = [pos for pos in self.room_states.keys() if pos[2] == floor]
        
        # Note: Stairs between floors are handled in _connect_stairs_properly method
        # which is called after all floors are generated
        
        # Add locked doors and blocked passages
        for pos in positions:
            # Random chance to add locked door
            if random.random() < 0.1:  # 10% chance
                available_dirs = [d for d in Direction if d not in [Direction.UP, Direction.DOWN] and 
                                 d in self.room_states[pos].connections]
                if available_dirs:
                    direction = random.choice(available_dirs)
                    # Add locked door requiring a key
                    self.room_states[pos].locked_doors[direction] = "Silver Key"
            
            # Random chance to add blocked passage
            if random.random() < 0.05:  # 5% chance
                available_dirs = [d for d in Direction if d not in [Direction.UP, Direction.DOWN] and 
                                 d in self.room_states[pos].connections]
                if available_dirs:
                    direction = random.choice(available_dirs)
                    # Add blocked passage requiring a trigger item
                    self.room_states[pos].blocked_passages[direction] = "Rune"
        
        # Populate rooms with items and entities
        self._populate_floor_rooms(floor)

    def _populate_floor_rooms(self, floor: int):
        """Populate rooms on a floor with items and entities."""
        positions = [pos for pos in self.room_states.keys() if pos[2] == floor]
        
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
                # Add a trap item that might be useful
                if random.random() < 0.5:
                    item = self._generate_trap_item()
                    room.add_item(item)
            elif room.room_type == "artifact":
                # Add a special artifact
                artifact = self._generate_artifact()
                room.add_item(artifact)
    
    def _generate_random_item(self) -> Item:
        """Generate a random item."""
        items = self.data_provider.get_items()
        if items:
            item_data = random.choice(items)
            return Item(
                name=item_data["name"],
                item_type=ItemType(item_data["type"]),
                value=item_data.get("value", 0),
                description=item_data.get("description", ""),
                attack_bonus=item_data.get("attack_bonus", 0),
                defense_bonus=item_data.get("defense_bonus", 0),
                status_effect=item_data.get("status_effect"),
                status_chance=item_data.get("status_chance", 0.0),
                status_damage=item_data.get("status_damage", 0)
            )
        else:
            # Fallback item
            return Item("Health Potion", ItemType.CONSUMABLE, 20, "Restores 20 HP")

    def _generate_random_enemy(self, floor: int):
        """Generate a random enemy based on floor."""
        from .character import Entity
        
        # Scale enemy strength based on floor
        enemies = self.data_provider.get_enemies()
        if enemies:
            # Filter enemies appropriate for floor level
            suitable_enemies = [e for e in enemies if e.get("min_floor", 0) <= floor]
            if not suitable_enemies:
                suitable_enemies = enemies  # Use all if none match criteria
            
            enemy_data = random.choice(suitable_enemies)
            
            # Scale stats based on floor
            health = enemy_data["health"] + (floor * 10)
            attack = enemy_data["attack"] + (floor * 2)
            defense = enemy_data["defense"] + floor
            
            enemy = Entity(
                name=enemy_data["name"],
                health=health,
                attack=attack,
                defense=defense,
                speed=enemy_data.get("speed", 10)
            )
            return enemy
        else:
            # Fallback enemy
            return Entity("Goblin", 20 + (floor * 5), 5 + floor, 2 + floor)

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
        artifact_items = [item for item in items if item.get("type") == "artifact"]
        
        if artifact_items:
            artifact_data = random.choice(artifact_items)
            return Item(
                name=artifact_data["name"],
                item_type=ItemType(artifact_data["type"]),
                value=artifact_data.get("value", 0),
                description=artifact_data.get("description", ""),
                attack_bonus=artifact_data.get("attack_bonus", 0),
                defense_bonus=artifact_data.get("defense_bonus", 0),
                status_effect=artifact_data.get("status_effect"),
                status_chance=artifact_data.get("status_chance", 0.0),
                status_damage=artifact_data.get("status_damage", 0)
            )
        else:
            # Fallback artifact
            return Item("Ancient Relic", ItemType.ARTIFACT, 100, "An ancient magical relic")

    def get_room_at(self, pos: Tuple[int, int, int]) -> RoomState:
        """Get the room at a given position."""
        return self.room_states.get(pos)

    def to_dict(self) -> Dict[str, Any]:
        """Convert dungeon to dictionary for saving."""
        return {
            "seed": self.seed,
            "room_states": {str(pos): room.to_dict() for pos, room in self.room_states.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create dungeon from dictionary for loading."""
        dungeon = cls(data["seed"])
        dungeon.room_states = {}
        
        for pos_str, room_data in data["room_states"].items():
            pos = tuple(int(x) for x in pos_str.strip('()').split(','))
            dungeon.room_states[pos] = RoomState.from_dict(room_data)
        
        return dungeon