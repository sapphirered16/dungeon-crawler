"""Main game engine for the dungeon crawler game."""

import json
import os
import random
from datetime import datetime
from typing import Tuple, List, Dict, Any
from .classes.dungeon import SeededDungeon
from .classes.character import Player
from .classes.room import RoomState
from .classes.base import Direction, Entity
from .classes.map_effects import MapEffectType
from .data.data_loader import DataProvider


class SeededGameEngine:
    def __init__(self, seed: int = None):
        self.seed = seed
        self.dungeon = SeededDungeon(seed)
        self.player = Player()
        self.current_room_state = self._find_starting_room()
        self.data_provider = DataProvider()
        
        # Track explored areas for visualization
        self.explored_positions = set()
        if self.current_room_state:
            self.explored_positions.add(self.current_room_state.pos)
        
        # Initialize logging
        self.log_file = f"dungeon_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.log_actions = []
        
        # Initialize event buffer for turn-based event logging
        self.event_buffer = []
        
        self._log_action("Game started", self.player.position)
    
    def _display_events(self):
        """Display all buffered events for the turn."""
        for event in self.event_buffer:
            print(event)
    
    def _finish_turn_display(self):
        """Finish the turn by displaying events and final state."""
        # Display all collected events
        self._display_events()
        
        # Show final room state
        self.look_around_simple()
        
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
        
        # Show active temporary buffs
        if self.player.temporary_buffs:
            temp_buffs_info = []
            if 'attack' in self.player.temporary_buffs:
                attack_buff = self.player.temporary_buffs['attack']
                attack_turns = self.player.temporary_buffs.get('attack_turns', 0)
                temp_buffs_info.append(f"+{attack_buff} attack ({attack_turns} turns)")
            if 'defense' in self.player.temporary_buffs:
                defense_buff = self.player.temporary_buffs['defense']
                defense_turns = self.player.temporary_buffs.get('defense_turns', 0)
                temp_buffs_info.append(f"+{defense_buff} defense ({defense_turns} turns)")
            if temp_buffs_info:
                print(f"⚡ Active Buffs: {', '.join(temp_buffs_info)}")
        
        # Show active status effects
        if self.player.active_status_effects:
            status_effects = [f"{effect}({duration})" for effect, duration in self.player.active_status_effects.items()]
            print(f"🌀 Status Effects: {', '.join(status_effects)}")
        
        # Show keys in inventory
        keys = [item.name for item in self.player.inventory if item.item_type.value == "key"]
        if keys:
            print(f"🔑 Keys in inventory: {', '.join(keys)}")
        
        print("🧭 Explore deeper to find stairs leading down.")

    def look_around(self):
        """Look around the current room."""
        print(f"\n--- {self.current_room_state.description} ---")
        
        # Show environmental features from map effects
        current_pos = self.player.position
        effect_descriptions = self.dungeon.map_effects.get_effect_descriptions_at_position(current_pos)
        if effect_descriptions:
            print("\nEnvironmental features:")
            for desc in effect_descriptions:
                print(f"  • {desc}")
        
        # Show items in room (only if there are items)
        if self.current_room_state.items:
            print("\nItems in the room:")
            for i, item in enumerate(self.current_room_state.items, 1):
                print(f"  {i}. {item.name} (Value: {item.value})")
        
        # Show creatures in room (excluding NPCs, only if there are creatures)
        from .classes.character import NonPlayerCharacter
        creatures = []
        for e in self.current_room_state.entities:
            if e.is_alive() and e.name != "Player" and not isinstance(e, NonPlayerCharacter):
                creatures.append(e)
        
        if creatures:
            print("\nCreatures in the room:")
            for i, entity in enumerate(creatures, 1):
                print(f"  {i}. {entity.name} (HP: {entity.health}/{entity.max_health}, Attack: {entity.attack}, Defense: {entity.defense})")
        
        # Show NPCs in room (only if there are NPCs)
        npcs = []
        for e in self.current_room_state.entities:
            if isinstance(e, NonPlayerCharacter) and e.is_alive():
                npcs.append(e)
        
        if npcs:
            print("\nNPCs in the room:")
            for i, npc in enumerate(npcs, 1):
                print(f"  {i}. {npc.name}")
        
        # Show available movement directions as a single sentence
        available_directions = []
        for direction in Direction:
            if direction in self.current_room_state.connections:
                available_directions.append(direction.value)
            elif direction in [Direction.UP, Direction.DOWN] and ((direction == Direction.UP and self.current_room_state.has_stairs_up) or (direction == Direction.DOWN and self.current_room_state.has_stairs_down)):
                available_directions.append(direction.value)
        
        if available_directions:
            directions_str = ", ".join(available_directions).replace("north", "North").replace("south", "South").replace("east", "East").replace("west", "West").replace("up", "Up").replace("down", "Down")
            if len(available_directions) == 1:
                print(f"\nYou are able to move {directions_str}.")
            else:
                print(f"\nYou are able to move {directions_str}.")
        else:
            print("\nYou cannot move in any direction.")
        
        # Don't show local map here - only show it for explicit look commands
        # Local map display moved to look_around_with_map method

    def look_around_with_map(self):
        """Look around the current room and show local map (for explicit look command)."""
        print(f"\n--- {self.current_room_state.description} ---")
        
        # Show environmental features from map effects
        current_pos = self.player.position
        effect_descriptions = self.dungeon.map_effects.get_effect_descriptions_at_position(current_pos)
        if effect_descriptions:
            print("\nEnvironmental features:")
            for desc in effect_descriptions:
                print(f"  • {desc}")
        
        # Show items in room (only if there are items)
        if self.current_room_state.items:
            print("\nItems in the room:")
            for i, item in enumerate(self.current_room_state.items, 1):
                print(f"  {i}. {item.name} (Value: {item.value})")
        
        # Show creatures in room (excluding NPCs, only if there are creatures)
        from .classes.character import NonPlayerCharacter
        creatures = []
        for e in self.current_room_state.entities:
            if e.is_alive() and e.name != "Player" and not isinstance(e, NonPlayerCharacter):
                creatures.append(e)
        
        if creatures:
            print("\nCreatures in the room:")
            for i, entity in enumerate(creatures, 1):
                print(f"  {i}. {entity.name} (HP: {entity.health}/{entity.max_health}, Attack: {entity.attack}, Defense: {entity.defense})")
        
        # Show NPCs in room (only if there are NPCs)
        npcs = []
        for e in self.current_room_state.entities:
            if isinstance(e, NonPlayerCharacter) and e.is_alive():
                npcs.append(e)
        
        if npcs:
            print("\nNPCs in the room:")
            for i, npc in enumerate(npcs, 1):
                print(f"  {i}. {npc.name}")
        
        # Show available movement directions as a single sentence
        available_directions = []
        for direction in Direction:
            if direction in self.current_room_state.connections:
                available_directions.append(direction.value)
            elif direction in [Direction.UP, Direction.DOWN] and ((direction == Direction.UP and self.current_room_state.has_stairs_up) or (direction == Direction.DOWN and self.current_room_state.has_stairs_down)):
                available_directions.append(direction.value)
        
        if available_directions:
            directions_str = ", ".join(available_directions).replace("north", "North").replace("south", "South").replace("east", "East").replace("west", "West").replace("up", "Up").replace("down", "Down")
            if len(available_directions) == 1:
                print(f"\nYou are able to move {directions_str}.")
            else:
                print(f"\nYou are able to move {directions_str}.")
        else:
            print("\nYou cannot move in any direction.")
        
        # Show local map (mini-map) - only for explicit look commands
        print("\n📍 Local Map:")
        self.show_local_map_no_legend()

    def look_around_simple(self):
        """Look around the current room without the mini-map (for use during turn processing)."""
        print(f"\n--- {self.current_room_state.description} ---")
        
        # Show environmental features from map effects
        current_pos = self.player.position
        effect_descriptions = self.dungeon.map_effects.get_effect_descriptions_at_position(current_pos)
        if effect_descriptions:
            print("\nEnvironmental features:")
            for desc in effect_descriptions:
                print(f"  • {desc}")
        
        # Show items in room (only if there are items)
        if self.current_room_state.items:
            print("\nItems in the room:")
            for i, item in enumerate(self.current_room_state.items, 1):
                print(f"  {i}. {item.name} (Value: {item.value})")
        
        # Show creatures in room (excluding NPCs, only if there are creatures)
        from .classes.character import NonPlayerCharacter
        creatures = []
        for e in self.current_room_state.entities:
            if e.is_alive() and e.name != "Player" and not isinstance(e, NonPlayerCharacter):
                creatures.append(e)
        
        if creatures:
            print("\nCreatures in the room:")
            for i, entity in enumerate(creatures, 1):
                print(f"  {i}. {entity.name} (HP: {entity.health}/{entity.max_health}, Attack: {entity.attack}, Defense: {entity.defense})")
        
        # Show NPCs in room (only if there are NPCs)
        npcs = []
        for e in self.current_room_state.entities:
            if isinstance(e, NonPlayerCharacter) and e.is_alive():
                npcs.append(e)
        
        if npcs:
            print("\nNPCs in the room:")
            for i, npc in enumerate(npcs, 1):
                print(f"  {i}. {npc.name}")
        
        # Show available movement directions as a single sentence
        available_directions = []
        for direction in Direction:
            if direction in self.current_room_state.connections:
                available_directions.append(direction.value)
            elif direction in [Direction.UP, Direction.DOWN] and ((direction == Direction.UP and self.current_room_state.has_stairs_up) or (direction == Direction.DOWN and self.current_room_state.has_stairs_down)):
                available_directions.append(direction.value)
        
        if available_directions:
            directions_str = ", ".join(available_directions).replace("north", "North").replace("south", "South").replace("east", "East").replace("west", "West").replace("up", "Up").replace("down", "Down")
            if len(available_directions) == 1:
                print(f"\nYou are able to move {directions_str}.")
            else:
                print(f"\nYou are able to move {directions_str}.")
        else:
            print("\nYou cannot move in any direction.")

    def _trigger_map_effects_at_current_position(self):
        """Trigger any map effects at the current player position."""
        current_pos = self.player.position
        effects_triggered = self.dungeon.map_effects.trigger_effects_at_position(current_pos, self.player)
        
        for effect_desc in effects_triggered:
            self.event_buffer.append(f"⚠️  {effect_desc}")
        
        # Check if player died due to effects
        if not self.player.is_alive():
            self.event_buffer.append("💀 You have succumbed to environmental hazards...")
        
        # Log the effect trigger
        if effects_triggered:
            self._log_action(f"Triggered map effects: {', '.join(effects_triggered)} - HP: {self.player.health}/{self.player.max_health}", current_pos)

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
            self._log_action("Tried to talk but no NPCs present", self.player.position)
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
                                self._log_action(f"Completed quest with {npc.name}, received {reward_item.name} - HP: {self.player.health}/{self.player.max_health}", self.player.position)
                                break
                            else:
                                # Player doesn't have the required item, give hint about the quest
                                print(f"\\n📜 {npc.name} has a quest for you:")
                                print(f"Quest: {quest['name']}")
                                print(f"Required: {required_item_name}")
                                print(f"Reward: {quest['reward']['name']}")
                                print(f"Description: {quest['description']}")
                                self._log_action(f"Started quest with {npc.name}: {quest['name']} - HP: {self.player.health}/{self.player.max_health}", self.player.position)
                                break
                    else:
                        print(f"{npc.name} nods politely.")
                        self._log_action(f"Talked to {npc.name} (no quest) - HP: {self.player.health}/{self.player.max_health}", self.player.position)
                    break
            
            if not npc_found_in_data:
                print(f"{npc.name} nods politely.")
                self._log_action(f"Talked to {npc.name} (no quest) - HP: {self.player.health}/{self.player.max_health}", self.player.position)
            
            return True
        else:
            print("Invalid NPC selection.")
            self._log_action("Invalid NPC selection", self.player.position)
            return False

    def move_player(self, direction: Direction):
        """Move the player in a direction if possible."""
        # Start a new turn by clearing the event buffer
        self.event_buffer = []
        
        if direction in self.current_room_state.locked_doors:
            key_name = self.current_room_state.locked_doors[direction]
            self.event_buffer.append(f"🔒 This way is locked by a magical barrier. You need a {key_name} to proceed.")
            # Check if player has the key
            for item in self.player.inventory:
                if item.name == key_name and item.item_type.value == "key":
                    self.event_buffer.append(f"✨ You use the {key_name} to unlock the magical barrier!")
                    del self.current_room_state.locked_doors[direction]
                    self._log_action(f"Used {key_name} to unlock door - HP: {self.player.health}/{self.player.max_health}", self.player.position)
                    break
            else:
                self.event_buffer.append(f"🔑 You don't have the required key: {key_name}")
                self.event_buffer.append(f"💡 Hint: Look for {key_name}s in earlier areas of the dungeon.")
                self._log_action(f"Failed to unlock door - no {key_name} - HP: {self.player.health}/{self.player.max_health}", self.player.position)
                self._display_events()
                return False

        if direction in self.current_room_state.blocked_passages:
            trigger_name = self.current_room_state.blocked_passages[direction]
            self.event_buffer.append(f"🚧 This way is blocked by ancient magic. You need a {trigger_name} to proceed.")
            # Check if player has the trigger item
            for item in self.player.inventory:
                if item.name == trigger_name:
                    self.event_buffer.append(f"✨ You use the {trigger_name} to dispel the magical blockage!")
                    del self.current_room_state.blocked_passages[direction]
                    self._log_action(f"Used {trigger_name} to unblock passage - HP: {self.player.health}/{self.player.max_health}", self.player.position)
                    break
            else:
                self.event_buffer.append(f"🔮 You don't have the required item: {trigger_name}")
                self.event_buffer.append(f"💡 Hint: Search for {trigger_name}s in rooms before reaching this area.")
                self._log_action(f"Failed to unblock passage - no {trigger_name} - HP: {self.player.health}/{self.player.max_health}", self.player.position)
                self._display_events()
                return False

        # Handle special directions (stairs)
        if direction == Direction.UP and self.current_room_state.has_stairs_up:
            target_pos = self.current_room_state.stairs_up_target
            if target_pos:
                old_pos = self.player.position
                self.current_room_state = self.dungeon.room_states[target_pos]
                self.player.travel_to(target_pos)
                # Add new position to explored areas
                self.explored_positions.add(target_pos)
                self.event_buffer.append("⬆️  You climb up the stairs...")
                self._log_action(f"Moved UP from {old_pos} to {target_pos} - HP: {self.player.health}/{self.player.max_health}", old_pos)
                # Trigger any map effects at the new position
                self._trigger_map_effects_at_current_position()
                # Process monster AI after moving
                self.process_monster_ai()
                # Update temporary buffs
                self.player.update_temporary_buffs()
                # Display all events and final state after moving
                self._display_events()
                self.look_around_simple()
                return True
        elif direction == Direction.DOWN and self.current_room_state.has_stairs_down:
            target_pos = self.current_room_state.stairs_down_target
            if target_pos:
                old_pos = self.player.position
                self.current_room_state = self.dungeon.room_states[target_pos]
                self.player.travel_to(target_pos)
                # Add new position to explored areas
                self.explored_positions.add(target_pos)
                self.event_buffer.append("⬇️  You descend down the stairs...")
                # Trigger any map effects at the new position
                self._trigger_map_effects_at_current_position()
                # Process monster AI after moving
                self.process_monster_ai()
                # Update temporary buffs
                self.player.update_temporary_buffs()
                self._log_action(f"Moved DOWN from {old_pos} to {target_pos} - HP: {self.player.health}/{self.player.max_health}", old_pos)
                # Display all events and final state after moving
                self._display_events()
                self.look_around_simple()
                return True
        elif direction in self.current_room_state.connections:
            new_pos = self.current_room_state.connections[direction]
            old_pos = self.player.position
            self.current_room_state = self.dungeon.room_states[new_pos]
            self.player.travel_to(new_pos)
            # Add new position to explored areas
            self.explored_positions.add(new_pos)
            # Trigger any map effects at the new position
            self._trigger_map_effects_at_current_position()
            # Process monster AI after moving
            self.process_monster_ai()
            # Update temporary buffs
            self.player.update_temporary_buffs()
            self._log_action(f"Moved {direction.value.upper()} from {old_pos} to {new_pos} - HP: {self.player.health}/{self.player.max_health}", old_pos)
            # Display all events and final state after moving
            self._display_events()
            self.look_around_simple()
            return True
        
        self.event_buffer.append(f"❌ You cannot move {direction.value}.")
        self._log_action(f"Tried to move {direction.value} but failed - HP: {self.player.health}/{self.player.max_health}", self.player.position)
        self._display_events()
        return False

    def attack_enemy(self, enemy_index: int) -> bool:
        """Attack an enemy in the current room."""
        # Start a new turn by clearing the event buffer
        self.event_buffer = []
        
        # Filter for living enemies only (excluding NPCs)
        from .classes.character import NonPlayerCharacter
        
        living_enemies = []
        for e in self.current_room_state.entities:
            if (e.is_alive() and 
                e.name != "Player" and 
                not isinstance(e, NonPlayerCharacter)):  # Exclude NPCs from combat
                living_enemies.append(e)
        
        if not living_enemies:
            self.event_buffer.append("There are no enemies here to attack.")
            self._log_action("Tried to attack but no enemies present", self.player.position)
            self._display_events()
            return False
        
        # Adjust enemy_index since the game displays enemies starting from 1
        adjusted_index = enemy_index - 1
        
        if 0 <= adjusted_index < len(living_enemies):
            enemy = living_enemies[adjusted_index]
            self.event_buffer.append(f"You attack the {enemy.name}!")
            
            # Calculate damage considering player's equipment
            player_attack = self.player.get_total_attack()
            damage_to_enemy = max(1, player_attack - enemy.defense)
            damage_taken = max(1, enemy.attack - self.player.get_total_defense())
            
            # Apply damage
            enemy_damage = enemy.take_damage(damage_to_enemy)
            self.player.take_damage(damage_taken)
            
            self.event_buffer.append(f"You deal {enemy_damage} damage to the {enemy.name}.")
            self.event_buffer.append(f"The {enemy.name} hits you for {damage_taken} damage.")
            
            # Apply status effects from equipped weapon
            if self.player.equipped_weapon:
                for effect, duration in self.player.equipped_weapon.status_effects.items():
                    if effect not in enemy.active_status_effects:
                        enemy.active_status_effects[effect] = duration
                        self.event_buffer.append(f"The {enemy.name} is affected by {effect}!")
            
            # Apply enemy status effects to player
            enemy.apply_status_effects()
            
            if not enemy.is_alive():
                self.event_buffer.append(f"You defeated the {enemy.name}!")
                # Get enemy definition to determine rewards
                enemy_data = self.data_provider.get_enemy_by_name(enemy.name)
                if enemy_data:
                    # Use EXP reward from enemy definition
                    exp_reward = enemy_data.get("exp_reward", enemy.max_health // 2)
                    self.player.gain_exp(exp_reward)
                    
                    # Use gold reward from enemy definition
                    gold_min = enemy_data.get("gold_min", 5)
                    gold_max = enemy_data.get("gold_max", 20)
                    gold_reward = random.randint(gold_min, gold_max)
                    self.player.gold += gold_reward
                else:
                    # Fallback values if no enemy data found
                    self.player.gain_exp(enemy.max_health // 2)
                    self.player.gold += random.randint(5, 20)
                self.player.enemies_defeated += 1
                self.player.score += enemy.max_health  # Score based on enemy difficulty
                # Process loot drops based on enemy's defined drops
                dropped_items = self._process_loot_drops(enemy)
                for dropped_item in dropped_items:
                    self.current_room_state.items.append(dropped_item)
                    self.event_buffer.append(f"The {enemy.name} dropped: {dropped_item.name}!")
                # Process monster AI after combat
                self.process_monster_ai()
                # Update temporary buffs
                self.player.update_temporary_buffs()
                self._log_action(f"Defeated {enemy.name}, dealt {enemy_damage} damage - HP: {self.player.health}/{self.player.max_health}", self.player.position)
                self._display_events()
                self.look_around_simple()
                return True
            else:
                self.event_buffer.append(f"The {enemy.name} has {enemy.health}/{enemy.max_health} HP remaining.")
                self._log_action(f"Attacked {enemy.name}, dealt {enemy_damage} damage, took {damage_taken} - HP: {self.player.health}/{self.player.max_health}", self.player.position)
                
            if not self.player.is_alive():
                self.event_buffer.append("You have been defeated...")
                self._log_action("Player defeated in combat - HP: 0/" + str(self.player.max_health), self.player.position)
                self._display_events()
                return False
            
            # Process monster AI after combat
            self.process_monster_ai()
            # Update temporary buffs
            self.player.update_temporary_buffs()
            self._display_events()
            self.look_around_simple()
            return True
        else:
            self.event_buffer.append("Invalid enemy selection.")
            self._log_action("Invalid enemy selection", self.player.position)
            self._display_events()
            return False

    def take_item(self, item_index: int) -> bool:
        """Take an item from the current room."""
        # Adjust item_index since the game displays items starting from 1
        adjusted_index = item_index - 1
        
        if 0 <= adjusted_index < len(self.current_room_state.items):
            item = self.current_room_state.items[adjusted_index]
            print(f"You take the {item.name}.")
            self.player.take_item(item)
            
            # Check if this is an artifact and if it's the final win condition
            if item.item_type.value == "artifact":
                print("🎉 CONGRATULATIONS! You have found the ultimate artifact!")
                print("✨ Your journey through the dungeon has ended in triumph!")
                print("🏆 You have achieved victory!")
                self.player.victory = True  # Mark player as having won
                print(f"\\n📊 FINAL SCORE: {self.player.score}")
                print(f"⚔️  ENEMIES DEFEATED: {self.player.enemies_defeated}")
                print(f"💎 TREASURES COLLECTED: {self.player.treasures_collected}")
                print("\\n🙏 Thanks for playing the dungeon crawler!")
                self._log_action(f"WON GAME by taking {item.name} (artifact) - HP: {self.player.health}/{self.player.max_health}", self.player.position)
                return True  # Return early to indicate game completion
            
            self.current_room_state.items.remove(item)
            # Process monster AI after taking an item (noise might attract attention)
            self.process_monster_ai()
            # Update temporary buffs
            self.player.update_temporary_buffs()
            self._log_action(f"Took item {item.name} - HP: {self.player.health}/{self.player.max_health}", self.player.position)
            return True
        else:
            print("Invalid item selection.")
            self._log_action("Invalid item selection", self.player.position)
            return False

    def use_item(self, item_index: int) -> bool:
        """Use an item from the player's inventory."""
        # Adjust item_index since the game displays inventory starting from 1
        adjusted_index = item_index - 1
        
        if 0 <= adjusted_index < len(self.player.inventory):
            item = self.player.inventory[adjusted_index]
            
            # Use the item
            result = self.player.use_item(item)
            print(result)
            
            # Process monster AI after using an item (might attract attention)
            self.process_monster_ai()
            # Update temporary buffs
            self.player.update_temporary_buffs()
            self._log_action(f"Used item {item.name} - HP: {self.player.health}/{self.player.max_health}", self.player.position)
            return True
        else:
            print("Invalid inventory item selection.")
            self._log_action("Invalid inventory item selection", self.player.position)
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
        
        # Player position
        player_x, player_y, player_z = self.player.position
        
        # Display grid
        for y in range(min_y, max_y + 1):  # Print from low Y to high Y so North (lower Y values) appears at top
            row = ""
            for x in range(min_x, max_x + 1):
                pos = (x, y, floor)
                if pos == (player_x, player_y, player_z):
                    row += "▲"  # Triangle pointing up for player
                elif pos in self.dungeon.room_states:
                    room = self.dungeon.room_states[pos]
                    # Check if this room has items and add indicator
                    if room.items:  # If room has items, mark with filled square
                        # Check if it's a hallway (connection to multiple rooms)
                        connections = len(room.connections)
                        if connections == 2:
                            # Hallway with items - use crossed lines for hallway with items
                            row += "╬"
                        else:
                            # Regular room with items - use filled square for room with items
                            row += "█"
                    else:
                        # Check if it's a hallway (connection to multiple rooms)
                        connections = len(room.connections)
                        if connections == 2:
                            # Hallway without items - use horizontal line for hallway
                            row += "─"
                        else:
                            # Regular room without items - use outlined box for empty room
                            row += "▭"
                else:
                    # Show unknown/void tiles as ░
                    if pos in self.explored_positions:
                        # If position was visited but has no room, show as empty space
                        row += "·"  # Center dot for explored empty space
                    else:
                        # Show unexplored void tiles as ░
                        row += "▓"  # Medium shade for unknown areas
            print(row)
        
        # Show legend
        print("\nLegend:")
        print("  ▭ = Room (no items)")
        print("  █ = Room/Hallway (with items)")
        print("  ─ = Hallway (no items)")
        print("  ╬ = Hallway (with items)")
        print("  ▲ = Player Position")
        print("  ▓ = Unknown Area")
        print("  · = Explored Empty Space")
        print("\nNote: Environmental hazards like traps, wet areas, etc. are not visible on this map")
        print("but will trigger when you step on those tiles.")

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
        return not self.player.is_alive() or self.player.victory

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

    def process_monster_ai(self):
        """Process AI for all monsters in the dungeon."""
        from .classes.enemy import Enemy
        from .classes.character import NonPlayerCharacter
        
        # Process each room for monster actions
        for pos, room in self.dungeon.room_states.items():
            # Create a copy of entities list to iterate over safely
            entities_copy = room.entities[:]
            
            for entity in entities_copy:
                if not entity.is_alive() or entity.name == "Player":
                    continue
                    
                # Handle NPCs separately (they don't attack)
                if isinstance(entity, NonPlayerCharacter):
                    continue  # NPCs are handled separately in the talk system
                
                # Handle enemies with their own AI logic
                if isinstance(entity, Enemy):
                    # Only report movements if enemy is in player's line of sight
                    is_in_line_of_sight = self._is_in_line_of_sight(room.pos, self.player.position)
                    
                    # Let the enemy decide its action
                    action_result = entity.take_turn(room, self.dungeon, self.player)
                    
                    if action_result["moved"] and action_result["new_position"] != pos:
                        # Move the entity to the new room
                        old_pos = pos
                        new_pos = action_result["new_position"]
                        
                        # Remove from current room
                        if entity in room.entities:
                            room.entities.remove(entity)
                        
                        # Add to new room
                        new_room = self.dungeon.room_states[new_pos]
                        if entity not in new_room.entities:
                            new_room.entities.append(entity)
                        
                        # Only add action description to event buffer if enemy is in line of sight of player
                        if action_result["action_description"] and is_in_line_of_sight:
                            self.event_buffer.append(action_result["action_description"])
                        # Don't log enemy movements - only log player interactions
                        # self._log_action(f"Enemy {entity.name} moved from {old_pos} to {new_pos}", self.player.position)
                    
                    elif action_result["attacked"]:
                        # Always add attack actions to event buffer since they affect the player
                        if action_result["action_description"]:
                            self.event_buffer.append(action_result["action_description"])
                        
                        # Check if enemy died after combat
                        if not entity.is_alive():
                            # Remove defeated enemy from room
                            if entity in room.entities:
                                room.entities.remove(entity)
                            
                            # Get enemy definition to determine rewards
                            enemy_data = self.data_provider.get_enemy_by_name(entity.name)
                            
                            if enemy_data:
                                # Use EXP reward from enemy definition
                                exp_reward = enemy_data.get("exp_reward", entity.max_health // 2)
                                self.player.gain_exp(exp_reward)
                                
                                # Use gold reward from enemy definition
                                gold_min = enemy_data.get("gold_min", 5)
                                gold_max = enemy_data.get("gold_max", 20)
                                gold_reward = random.randint(gold_min, gold_max)
                                self.player.gold += gold_reward
                            else:
                                # Fallback values if no enemy data found
                                self.player.gain_exp(entity.max_health // 2)
                                self.player.gold += random.randint(5, 20)
                            
                            self.player.enemies_defeated += 1
                            self.player.score += entity.max_health
                            
                            # Process loot drops based on enemy's defined drops
                            dropped_items = self._process_loot_drops(entity)
                            for dropped_item in dropped_items:
                                room.items.append(dropped_item)
                                # Only add drop to event buffer if player is in same room
                                if room.pos == self.player.position:
                                    self.event_buffer.append(f"掉落 The {entity.name} dropped: {dropped_item.name}!")
    
    # Helper methods removed as they are now handled in the Enemy class

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
        return self.dungeon.get_adjacent_positions(pos)

    def _process_loot_drops(self, enemy) -> List:
        """Process loot drops based on enemy's defined drops."""
        from .classes.item import Item
        from .classes.base import ItemType
        
        dropped_items = []
        
        # Get enemy definition from data provider
        enemy_data = self.data_provider.get_enemy_by_name(enemy.name)
        
        if enemy_data and "drops" in enemy_data:
            for drop in enemy_data["drops"]:
                # Roll for drop chance
                if random.random() < drop["chance"]:
                    # Get item definition from data provider
                    item_data = self.data_provider.get_item_by_name(drop["item_name"])
                    
                    if item_data:
                        # Create item based on definition
                        item = Item(
                            name=item_data["name"],
                            item_type=ItemType(item_data["type"]),
                            value=item_data.get("value", 0),
                            description=f"Dropped by {enemy.name}",
                            attack_bonus=item_data.get("attack_bonus", 0),
                            defense_bonus=item_data.get("defense_bonus", 0),
                            status_effects=item_data.get("status_effects", {})
                        )
                        dropped_items.append(item)
        else:
            # Fallback: random drop with 30% chance if no specific drops defined
            if random.random() < 0.3:
                dropped_item = self.dungeon._generate_random_item()
                dropped_items.append(dropped_item)
        
        return dropped_items

    def _log_action(self, action: str, position: Tuple[int, int, int] = None):
        """Log an action to the game log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if position is None:
            position = self.player.position
        log_entry = f"[{timestamp}] Position: {position} | Action: {action}"
        self.log_actions.append(log_entry)
        
        # Write to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

    def clear_save_and_logs(self):
        """Clear all save files and log files."""
        import glob
        
        # Clear save files
        save_files = glob.glob("savegame*.json")
        for file in save_files:
            try:
                os.remove(file)
                print(f"🗑️  Deleted save file: {file}")
            except Exception as e:
                print(f"❌ Could not delete save file {file}: {e}")
        
        # Clear log files
        log_files = glob.glob("dungeon_log_*.txt")
        for file in log_files:
            try:
                os.remove(file)
                print(f"🗑️  Deleted log file: {file}")
            except Exception as e:
                print(f"❌ Could not delete log file {file}: {e}")
        
        # Reset log actions
        self.log_actions = []
        
        print("✅ Save and log files cleared successfully!")
        print("💡 A new game session will start with a fresh save and log.")

    def view_log_history(self, lines: int = 20):
        """View the last N lines of the game log."""
        if not self.log_actions:
            print("📋 No log entries yet.")
            return
        
        print(f"\n📋 LAST {min(lines, len(self.log_actions))} LOG ENTRIES:")
        print("-" * 60)
        
        # Show the last 'lines' entries
        recent_entries = self.log_actions[-lines:]
        for entry in recent_entries:
            print(entry)
        
        print("-" * 60)
        print(f"Total log entries: {len(self.log_actions)}")

    def show_local_map(self):
        """Show a 5x5 map around the player's current position with legend."""
        player_x, player_y, player_z = self.player.position
        
        # Define the 5x5 grid centered on player
        min_x, max_x = player_x - 2, player_x + 2
        min_y, max_y = player_y - 2, player_y + 2
        
        print(f"\n📍 LOCAL MAP (5x5) around ({player_x}, {player_y}):")
        print("  " + " ".join([str(i % 10) for i in range(min_x, max_x + 1)]))
        
        for y in range(min_y, max_y + 1):  # Print from low Y to high Y so North (lower Y) appears above player
            row = f"{(y % 10)} "
            for x in range(min_x, max_x + 1):
                pos = (x, y, player_z)
                if pos == (player_x, player_y, player_z):
                    # Player position
                    row += "▲ "
                elif pos in self.dungeon.room_states:
                    room = self.dungeon.room_states[pos]
                    # Check if this room has items and add indicator
                    if room.items:  # If room has items, mark with filled square
                        # Check if it's a hallway (connection to multiple rooms)
                        connections = len(room.connections)
                        if connections == 2:
                            # Hallway with items
                            row += "╬ "
                        else:
                            # Regular room with items
                            row += "█ "
                    else:
                        # Check if it's a hallway (connection to multiple rooms)
                        connections = len(room.connections)
                        if connections == 2:
                            # Hallway without items
                            row += "─ "
                        else:
                            # Regular room without items
                            row += "▭ "
                else:
                    # Show unknown/void tiles as ░
                    if pos in self.explored_positions:
                        # If position was visited but has no room, show as empty space
                        row += "· "  # Center dot for explored empty space
                    else:
                        # Show unexplored void tiles as ░
                        row += "▓ "  # Medium shade for unknown areas
            print(row)
        
        # Show legend for full local map command
        print("\n🗺️  Legend:")
        print("  ▲ = Player")
        print("  ▭ = Room (no items)")
        print("  █ = Room/Hallway (with items)")
        print("  ─ = Hallway (no items)")
        print("  ╬ = Hallway (with items)")
        print("  ▓ = Unknown Area")
        print("  · = Explored Empty Space")

    def show_local_map_no_legend(self):
        """Show a 5x5 map around the player's current position without legend."""
        player_x, player_y, player_z = self.player.position
        
        # Define the 5x5 grid centered on player
        min_x, max_x = player_x - 2, player_x + 2
        min_y, max_y = player_y - 2, player_y + 2
        
        print("  " + " ".join([str(i % 10) for i in range(min_x, max_x + 1)]))
        
        for y in range(min_y, max_y + 1):  # Print from low Y to high Y so North (lower Y) appears above player
            row = f"{(y % 10)} "
            for x in range(min_x, max_x + 1):
                pos = (x, y, player_z)
                if pos == (player_x, player_y, player_z):
                    # Player position
                    row += "▲ "
                elif pos in self.dungeon.room_states:
                    room = self.dungeon.room_states[pos]
                    # Check if this room has items and add indicator
                    if room.items:  # If room has items, mark with filled square
                        # Check if it's a hallway (connection to multiple rooms)
                        connections = len(room.connections)
                        if connections == 2:
                            # Hallway with items
                            row += "╬ "
                        else:
                            # Regular room with items
                            row += "█ "
                    else:
                        # Check if it's a hallway (connection to multiple rooms)
                        connections = len(room.connections)
                        if connections == 2:
                            # Hallway without items
                            row += "─ "
                        else:
                            # Regular room without items
                            row += "▭ "
                else:
                    # Show unknown/void tiles as ░
                    if pos in self.explored_positions:
                        # If position was visited but has no room, show as empty space
                        row += "· "  # Center dot for explored empty space
                    else:
                        # Show unexplored void tiles as ░
                        row += "▓ "  # Medium shade for unknown areas
            print(row)