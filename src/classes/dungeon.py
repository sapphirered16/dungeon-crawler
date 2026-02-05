"""Dungeon class for the dungeon crawler game."""

import random
from typing import Dict, List, Tuple, Any
from .room import RoomState
from .item import Item
from .base import ItemType, Direction
from .map_effects import MapEffect, MapEffectType, MapEffectManager
from ..data.data_loader import DataProvider


class SeededDungeon:
    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
        self.seed = seed
        self.room_states = {}  # {(x, y, z): RoomState}
        self.map_effects = MapEffectManager()
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
                
            # Create new room with all available room types including fillers
            # BUT exclude "artifact" room type during initial generation since 
            # the special artifact room is created separately in _connect_stairs_properly
            room_types = ["empty", "treasure", "monster", "trap", "npc", 
                         "storage", "bunk", "kitchen", "library", "workshop", "garden"]
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
        
        # Populate rooms with items and entities BEFORE adding obstacles
        # This ensures items are available before any obstacles are placed
        self._populate_floor_rooms(floor)
        
        # Now add obstacles but in a logical way ensuring required items are available
        # First, sort positions by distance from starting area to create a logical flow
        # Find the actual starting room (the one that was originally created at (12, 12, 0))
        start_positions = [pos for pos in positions if pos == (12, 12, 0)]
        
        if start_positions:
            start_pos = start_positions[0]
            # Calculate distances from start to create logical progression
            distances = {}
            queue = [(start_pos, 0)]
            visited = set()
            
            while queue:
                current_pos, dist = queue.pop(0)
                if current_pos in visited:
                    continue
                visited.add(current_pos)
                distances[current_pos] = dist
                
                # Add connected rooms to queue
                for direction, connected_pos in self.room_states[current_pos].connections.items():
                    if connected_pos not in visited:
                        queue.append((connected_pos, dist + 1))
        else:
            # If no start position found, just use all positions with arbitrary distances
            distances = {pos: i for i, pos in enumerate(positions)}
        
        # Sort positions by distance to create progression from early to late areas
        sorted_positions = sorted(positions, key=lambda pos: distances.get(pos, 0))
        
        # Add locked doors and blocked passages in a logical progression
        # Place obstacles only between rooms where required items already exist in earlier rooms
        for pos in sorted_positions:
            # For locked doors, only place them if we can ensure the key exists in an earlier room
            if random.random() < 0.1:  # 10% chance
                available_dirs = [d for d in Direction if d not in [Direction.UP, Direction.DOWN] and 
                                 d in self.room_states[pos].connections]
                if available_dirs:
                    direction = random.choice(available_dirs)
                    
                    # Check if a key exists in earlier rooms in the progression
                    current_dist = distances.get(pos, 0)
                    key_exists = False
                    
                    # Check if any room with a key is earlier in the progression
                    for check_pos in sorted_positions:
                        if distances.get(check_pos, 0) < current_dist:
                            # Check if this room has a key item
                            for item in self.room_states[check_pos].items:
                                if "Key" in item.name:
                                    key_exists = True
                                    break
                        if key_exists:
                            break
                    
                    # If no key exists in earlier rooms, add one to an earlier room
                    if not key_exists:
                        # Add a key to an earlier room in the progression
                        earlier_rooms = [p for p in sorted_positions if distances.get(p, 0) < current_dist]
                        if earlier_rooms:
                            key_room = random.choice(earlier_rooms)
                            
                            # Add a key to this room - get from data provider
                            from .item import Item
                            from .base import ItemType
                            
                            # Get available keys from data provider
                            available_keys = [item for item in self.data_provider.get_items() if item.get("type", "").upper() == "KEY"]
                            if available_keys:
                                key_data = random.choice(available_keys)
                                # Add the key to the earlier room
                                key_item = Item(
                                    name=key_data["name"],
                                    item_type=ItemType.KEY,
                                    value=key_data.get("value", 0),
                                    description=key_data.get("description", f"Unlocks doors that require a {key_data['name']}"),
                                    attack_bonus=key_data.get("attack_bonus", 0),
                                    defense_bonus=key_data.get("defense_bonus", 0),
                                    status_effects=key_data.get("status_effects", {})
                                )
                                self.room_states[key_room].add_item(key_item)
                            else:
                                # Fallback to hardcoded values
                                key_options = ["Iron Key", "Silver Key", "Golden Key", "Ancient Key"]
                                key_name = random.choice(key_options)
                                
                                # Add the key to the earlier room
                                key_item = Item(
                                    name=key_name,
                                    item_type=ItemType.KEY,
                                    value={"Iron Key": 10, "Silver Key": 15, "Golden Key": 25, "Ancient Key": 50}[key_name],
                                    description=f"Unlocks doors that require a {key_name}"
                                )
                                self.room_states[key_room].add_item(key_item)
                    
                    # Add locked door requiring a key - get from data provider
                    available_keys = [item["name"] for item in self.data_provider.get_items() if item.get("type", "").upper() == "KEY"]
                    if available_keys:
                        key_name = random.choice(available_keys)
                        self.room_states[pos].locked_doors[direction] = key_name
                    else:
                        self.room_states[pos].locked_doors[direction] = "Silver Key"  # Fallback
            
            # Similar logic for blocked passages
            if random.random() < 0.05:  # 5% chance
                available_dirs = [d for d in Direction if d not in [Direction.UP, Direction.DOWN] and 
                                 d in self.room_states[pos].connections]
                if available_dirs:
                    direction = random.choice(available_dirs)
                    
                    # Check if a trigger item exists in earlier rooms in the progression
                    current_dist = distances.get(pos, 0)
                    trigger_exists = False
                    
                    # Check if any room with a trigger item is earlier in the progression
                    for check_pos in sorted_positions:
                        if distances.get(check_pos, 0) < current_dist:
                            # Check if this room has a trigger item
                            for item in self.room_states[check_pos].items:
                                if item.item_type.value in ["trigger", "key"]:
                                    trigger_exists = True
                                    break
                        if trigger_exists:
                            break
                    
                    # If no trigger exists in earlier rooms, add one to an earlier room
                    if not trigger_exists:
                        # Add a trigger to an earlier room in the progression
                        earlier_rooms = [p for p in sorted_positions if distances.get(p, 0) < current_dist]
                        if earlier_rooms:
                            trigger_room = random.choice(earlier_rooms)
                            
                            # Add a trigger item to this room - get from data provider
                            from .item import Item
                            from .base import ItemType
                            
                            # Get available triggers from data provider
                            available_triggers = [item for item in self.data_provider.get_items() if item.get("type", "").upper() == "TRIGGER"]
                            if available_triggers:
                                trigger_data = random.choice(available_triggers)
                                # Add the trigger to the earlier room
                                trigger_item = Item(
                                    name=trigger_data["name"],
                                    item_type=ItemType.TRIGGER,
                                    value=trigger_data.get("value", 0),
                                    description=trigger_data.get("description", f"Can be used to clear blocked passages"),
                                    attack_bonus=trigger_data.get("attack_bonus", 0),
                                    defense_bonus=trigger_data.get("defense_bonus", 0),
                                    status_effects=trigger_data.get("status_effects", {})
                                )
                                self.room_states[trigger_room].add_item(trigger_item)
                            else:
                                # Fallback to hardcoded values
                                trigger_item = Item(
                                    name="Power Rune",
                                    item_type=ItemType.TRIGGER,
                                    value=5,
                                    description="Can be used to clear blocked passages"
                                )
                                self.room_states[trigger_room].add_item(trigger_item)
                    
                    # Add blocked passage requiring a trigger item - get from data provider
                    available_triggers = [item["name"] for item in self.data_provider.get_items() if item.get("type", "").upper() == "TRIGGER"]
                    if available_triggers:
                        trigger_name = random.choice(available_triggers)
                        self.room_states[pos].blocked_passages[direction] = trigger_name
                    else:
                        self.room_states[pos].blocked_passages[direction] = "Power Rune"  # Fallback

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
                other_types = ["empty", "treasure", "monster", "npc"]  # Removed "artifact" to prevent artifact rooms elsewhere
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
                    # Repopulate with the new room type logic
                    continue  # Continue to the next room to be repopulated with the new type
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
            dungeon.map_effects = MapEffectManager.from_dict(data["map_effects"])
        else:
            # For backward compatibility, create a new map effects manager
            dungeon.map_effects = MapEffectManager()
        
        return dungeon