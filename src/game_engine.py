"""Main game engine for the dungeon crawler game."""

import json
import os
import random
from typing import Tuple, List, Dict, Any
from .classes.dungeon import SeededDungeon
from .classes.character import Player
from .classes.room import RoomState
from .classes.base import Direction, Entity
from .data.data_loader import DataProvider


class SeededGameEngine:
    def __init__(self, seed: int = None):
        self.seed = seed
        self.dungeon = SeededDungeon(seed)
        self.player = Player()
        self.current_room_state = self._find_starting_room()
        self.data_provider = DataProvider()
        
    def _find_starting_room(self):
        """Find the starting room (z=0 floor)."""
        for pos, room in self.dungeon.room_states.items():
            if pos[2] == 0:  # First floor
                self.player.travel_to(pos)
                return room
        # If no room found on floor 0, create one
        start_pos = (12, 12, 0)
        start_room = self.dungeon.room_states[start_pos]
        self.player.travel_to(start_pos)
        return start_room

    def show_stats(self):
        """Display player statistics."""
        print("\n--- 🦸 Hero's Stats ---")
        print(f"Level: {self.player.level}")
        print(f"HP: {self.player.health}/{self.player.max_health}")
        print(f"Attack: {self.player.get_total_attack()}")
        print(f"Defense: {self.player.get_total_defense()}")
        print(f"EXP: {self.player.exp}/{self.player.exp_to_next_level}")
        print(f"Gold: {self.player.gold}")
        print(f"Position: Floor {self.player.position[2] + 1}, {self.player.position[:2]}")
        print(f"Score: {self.player.score}")
        print(f"Enemies Defeated: {self.player.enemies_defeated}")
        print(f"Treasures Collected: {self.player.treasures_collected}")
        print(f"Floors Explored: {self.player.floors_explored}")
        print(f"Rooms Explored: {len(self.player.rooms_explored)}")
        print(f"Distance Traveled: {self.player.distance_traveled}")
        
        if self.player.equipped_weapon:
            print(f"Weapon: {self.player.equipped_weapon.name}")
        else:
            print("Weapon: None equipped")
        
        if self.player.equipped_armor:
            print(f"Armor: {self.player.equipped_armor.name}")
        else:
            print("Armor: None equipped")
        
        # Show keys in inventory
        keys = [item.name for item in self.player.inventory if item.item_type.value == "key"]
        if keys:
            print(f"🔑 Keys in inventory: {', '.join(keys)}")
        
        print("🧭 Explore deeper to find stairs leading down.")

    def look_around(self):
        """Look around the current room."""
        print(f"\n--- {self.current_room_state.description} ---")
        
        # Show items in room
        if self.current_room_state.items:
            print("\nItems in the room:")
            for i, item in enumerate(self.current_room_state.items, 1):
                print(f"  {i}. {item.name} (Value: {item.value})")
        else:
            print("\nNo items in this room.")
        
        # Show creatures in room (excluding NPCs)
        from .classes.character import NonPlayerCharacter
        creatures = []
        for e in self.current_room_state.entities:
            if e.is_alive() and e.name != "Player" and not isinstance(e, NonPlayerCharacter):
                creatures.append(e)
        
        if creatures:
            print("\nCreatures in the room:")
            for i, entity in enumerate(creatures, 1):
                print(f"  {i}. {entity.name} (HP: {entity.health}/{entity.max_health}, Attack: {entity.attack}, Defense: {entity.defense})")
        else:
            print("\nNo creatures in this room.")
        
        # Show NPCs in room
        npcs = []
        for e in self.current_room_state.entities:
            if isinstance(e, NonPlayerCharacter) and e.is_alive():
                npcs.append(e)
        
        if npcs:
            print("\nNPCs in the room:")
            for i, npc in enumerate(npcs, 1):
                print(f"  {i}. {npc.name}")
        else:
            print("\nNo NPCs in this room.")
        
        # Show adjacent areas
        print("\nAdjacent areas:")
        for direction in Direction:
            if direction in self.current_room_state.connections:
                connected_pos = self.current_room_state.connections[direction]
                connected_room = self.dungeon.get_room_at(connected_pos)
                if connected_room:
                    print(f"  {direction.value.capitalize()}: {connected_room.description}")
            elif direction == Direction.UP and self.current_room_state.has_stairs_up:
                print(f"  Up: Stairs leading up.")
            elif direction == Direction.DOWN and self.current_room_state.has_stairs_down:
                print(f"  Down: Stairs leading down.")
            else:
                print(f"  {direction.value.capitalize()}: blocked")

    def talk_to_npc(self, npc_index: int) -> bool:
        """Talk to an NPC in the current room."""
        from .classes.character import NonPlayerCharacter
        from .classes.item import Item
        from .classes.base import ItemType
        
        # Get all NPCs in the room
        npcs = []
        for e in self.current_room_state.entities:
            if isinstance(e, NonPlayerCharacter) and e.is_alive():
                npcs.append(e)
        
        if not npcs:
            print("There are no NPCs here to talk to.")
            return False
        
        # Adjust index since the game displays NPCs starting from 1
        adjusted_index = npc_index - 1
        
        if 0 <= adjusted_index < len(npcs):
            npc = npcs[adjusted_index]
            
            # Get NPC dialogue
            dialogue = npc.get_dialogue()
            print(f"{npc.name} says: \"{dialogue}\"")
            
            # Check for quests in the NPC data
            # First, we need to load the NPC's quest data
            # We'll check if this NPC has quest data in our data provider
            npc_found_in_data = False
            for npc_template in self.data_provider.get_npcs():
                if npc_template["name"] == npc.name:
                    npc_found_in_data = True
                    if "quests" in npc_template and npc_template["quests"]:
                        # Check if player has the required item for any quest
                        for quest in npc_template["quests"]:
                            required_item_name = quest["target_item"]
                            
                            # Check if player has the required item
                            has_required_item = False
                            required_item = None
                            for item in self.player.inventory:
                                if item.name == required_item_name:
                                    has_required_item = True
                                    required_item = item
                                    break
                            
                            if has_required_item:
                                # Player has the required item, offer to complete quest
                                print(f"\\n🎁 {npc.name} recognizes the {required_item_name}!")
                                print(f"Quest: {quest['name']}")
                                print(f"Description: {quest['description']}")
                                
                                # Give the reward
                                reward_data = quest["reward"]
                                reward_item = Item(
                                    name=reward_data["name"],
                                    item_type=ItemType(reward_data["type"].lower()),
                                    value=reward_data["value"],
                                    description=f"Quest reward: {reward_data['name']}",
                                    attack_bonus=reward_data.get("attack_bonus", 0),
                                    defense_bonus=reward_data.get("defense_bonus", 0)
                                )
                                
                                print(f"💰 {npc.name} gives you: {reward_item.name}!")
                                self.player.take_item(reward_item)
                                
                                # Remove the required item from player inventory
                                self.player.inventory.remove(required_item)
                                print(f"🔄 {required_item_name} was exchanged for the reward.")
                                
                                # Note: In a full implementation, we might want to track completed quests
                                # to prevent re-completion, but for now we'll just complete it
                                break
                            else:
                                # Player doesn't have the required item, give hint about the quest
                                print(f"\\n📜 {npc.name} has a quest for you:")
                                print(f"Quest: {quest['name']}")
                                print(f"Required: {required_item_name}")
                                print(f"Reward: {quest['reward']['name']}")
                                print(f"Description: {quest['description']}")
                                break
                    else:
                        print(f"{npc.name} nods politely.")
                    break
            
            if not npc_found_in_data:
                print(f"{npc.name} nods politely.")
            
            return True
        else:
            print("Invalid NPC selection.")
            return False

    def move_player(self, direction: Direction):
        """Move the player in a direction if possible."""
        if direction in self.current_room_state.locked_doors:
            key_name = self.current_room_state.locked_doors[direction]
            print(f"🔒 This way is locked by a magical barrier. You need a {key_name} to proceed.")
            # Check if player has the key
            for item in self.player.inventory:
                if item.name == key_name and item.item_type.value == "key":
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

    def attack_enemy(self, enemy_index: int) -> bool:
        """Attack an enemy in the current room."""
        # Filter for living enemies only (excluding NPCs)
        from .classes.character import NonPlayerCharacter
        
        living_enemies = []
        for e in self.current_room_state.entities:
            if (e.is_alive() and 
                e.name != "Player" and 
                not isinstance(e, NonPlayerCharacter)):  # Exclude NPCs from combat
                living_enemies.append(e)
        
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

    def visualize_floor(self, floor: int = None):
        """Visualize the current floor or a specific floor."""
        if floor is None:
            floor = self.player.position[2]
        
        print(f"\n--- FLOOR {floor + 1} VISUALIZATION (Seed: {self.seed}) ---")
        
        # Get all positions on this floor
        floor_positions = {pos: room for pos, room in self.dungeon.room_states.items() if pos[2] == floor}
        
        if not floor_positions:
            print("No rooms on this floor.")
            return
        
        # Determine bounds
        xs = [pos[0] for pos in floor_positions.keys()]
        ys = [pos[1] for pos in floor_positions.keys()]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Create grid representation
        grid = {}
        for pos, room in floor_positions.items():
            x, y, z = pos
            grid[(x, y)] = room
        
        # Player position
        player_x, player_y, player_z = self.player.position
        
        # Display grid
        for y in range(min_y, max_y + 1):
            row = ""
            for x in range(min_x, max_x + 1):
                if (x, y) == (player_x, player_y):
                    row += "@"
                elif (x, y) in grid:
                    room = grid[(x, y)]
                    # Use first letter of room type as symbol
                    if room.room_type == "treasure":
                        row += "$"
                    elif room.room_type == "monster":
                        row += "M"
                    elif room.room_type == "trap":
                        row += "T"
                    elif room.room_type == "npc":
                        row += "N"
                    elif room.room_type == "artifact":
                        row += "A"
                    elif room.room_type.startswith("stair"):  # stairs up or down
                        row += "S"
                    else:
                        # Check if it's a hallway (connection to multiple rooms)
                        connections = len(room.connections)
                        if connections > 2:
                            row += "."
                        elif connections == 2:
                            # Likely a hallway
                            row += "-"
                        else:
                            row += "."
                else:
                    row += " "
            print(row)
        
        # Show legend
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

    def save_game(self, filename: str = "savegame.json"):
        """Save the current game state."""
        game_state = {
            "seed": self.seed,
            "dungeon": self.dungeon.to_dict(),
            "player": self.player.to_dict(),
            "current_room_pos": self.player.position
        }
        
        with open(filename, 'w') as f:
            json.dump(game_state, f, indent=2)
        
        print(f"💾 Game saved to {filename}")

    def load_game(self, filename: str = "savegame.json"):
        """Load a saved game state."""
        if not os.path.exists(filename):
            print(f"❌ Save file {filename} does not exist.")
            return
        
        with open(filename, 'r') as f:
            game_state = json.load(f)
        
        self.seed = game_state["seed"]
        self.dungeon = SeededDungeon.from_dict(game_state["dungeon"])
        self.player = Player.from_dict(game_state["player"])
        
        # Set current room based on player position
        current_pos = tuple(game_state["current_room_pos"])
        self.current_room_state = self.dungeon.room_states[current_pos]
        
        print(f"📂 Game loaded from {filename}")

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return not self.player.is_alive()

    def get_game_status(self) -> Dict[str, Any]:
        """Get the current game status."""
        return {
            "player_alive": self.player.is_alive(),
            "player_position": self.player.position,
            "player_level": self.player.level,
            "player_hp": self.player.health,
            "enemies_defeated": self.player.enemies_defeated,
            "treasures_collected": self.player.treasures_collected,
            "floors_explored": self.player.floors_explored,
            "current_floor": self.player.position[2]
        }

    # Monster AI Implementation
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
        """Get adjacent positions to a given position."""
        x, y, z = pos
        adjacent = []
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # West, East, North, South
            new_pos = (x + dx, y + dy, z)
            if new_pos in self.dungeon.room_states:
                adjacent.append(new_pos)
        
        return adjacent