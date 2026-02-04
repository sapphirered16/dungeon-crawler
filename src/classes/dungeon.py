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
        
        # Create a basic layout with a starting room
        start_pos = (12, 12, 0)  # Starting position
        start_room = RoomState(start_pos, "starting")
        start_room.description = "The entrance to the dungeon. A safe starting area."
        self.room_states[start_pos] = start_room
        
        # Generate rooms for multiple floors
        for floor in range(3):  # Generate 3 floors
            self._generate_floor(floor, start_pos if floor == 0 else None)
    
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
        
        # Add stairs between floors
        if floor < 2:  # Only add stairs if not the last floor
            # Find two random positions on this floor
            if len(positions) >= 2:
                from_pos = random.choice(positions)
                to_pos = random.choice(positions)
                
                # Make sure they're different
                while to_pos == from_pos and len(positions) > 1:
                    to_pos = random.choice(positions)
                
                # Mark as having stairs down
                self.room_states[from_pos].has_stairs_down = True
                self.room_states[from_pos].stairs_down_target = (to_pos[0], to_pos[1], floor + 1)
                
                # On the next floor, mark corresponding room as having stairs up
                next_floor_positions = [pos for pos in self.room_states.keys() if pos[2] == floor + 1]
                if next_floor_positions:
                    up_pos = random.choice(next_floor_positions)
                    self.room_states[up_pos].has_stairs_up = True
                    self.room_states[up_pos].stairs_up_target = from_pos
        
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
            return NonPlayerCharacter(
                name=npc_data["name"],
                health=npc_data["health"],
                attack=npc_data["attack"],
                defense=npc_data["defense"],
                dialogue=npc_data.get("dialogue", [])
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