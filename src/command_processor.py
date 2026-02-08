"""Command processor for the dungeon crawler game."""

import re
from typing import List, Tuple, Optional
from classes.base import Direction
from new_game_engine import SeededGameEngine


class CommandProcessor:
    def __init__(self, game_engine: SeededGameEngine):
        self.game_engine = game_engine
        self.command_map = {
            'help': self.help_command,
            'h': self.help_command,
            '?': self.help_command,
            'stats': self.stats_command,
            'look': self.look_command,
            'go': self.go_command,
            'move': self.move_command,
            'attack': self.attack_command,
            'fight': self.attack_command,
            'take': self.take_command,
            'get': self.take_command,
            'equip': self.equip_command,
            'use': self.use_command,
            'inventory': self.inventory_command,
            'i': self.inventory_command,
            'map': self.map_command,
            'local': self.local_map_command,
            'lm': self.local_map_command,
            'talk': self.talk_command,
            'speak': self.talk_command,
            'save': self.save_command,
            'load': self.load_command,
            'clear': self.clear_command,
            'log': self.log_command,
            'history': self.log_command,
            'quit': self.quit_command,
            'q': self.quit_command,
            'exit': self.quit_command,
            'items': self.items_map_command,
            'item': self.items_map_command,
            'stairs': self.stairs_command,
            'staircase': self.stairs_command,
            'levels': self.stairs_command,
        }

    def process_command(self, command: str) -> bool:
        """Process a command string and execute the appropriate action.
        
        Args:
            command: The command string entered by the user
            
        Returns:
            True if the game should continue, False if it should exit
        """
        command = command.strip().lower()
        
        if not command:
            return True
        
        # Split command into parts
        parts = command.split()
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Check for direction shortcuts
        if cmd in ['north', 'south', 'east', 'west', 'up', 'down']:
            direction = Direction(cmd)
            success = self.game_engine.move_player(direction)
            if not success:
                print(f"❌ You cannot move {direction.value}.")
            else:
                # Auto-save after successful movement
                self.game_engine.save_game()
                # Show the local map after movement
                try:
                    # Debug: print that we're trying to show the map
                    print("📍 Showing map after movement...")
                    # Get the current room if it exists, or find the nearest room
                    if hasattr(self.game_engine, 'current_room') and self.game_engine.current_room:
                        # Show the room description and local map
                        self.game_engine.look_around_with_map()
                    else:
                        # If no current room, just show the local map around player position
                        print("\n📍 Local Map:")
                        self.game_engine.show_local_map_no_legend()
                except Exception as e:
                    print(f"⚠️  Error showing local map after movement: {e}")
            return True
        
        # Look for command in mapping
        if cmd in self.command_map:
            try:
                result = self.command_map[cmd](args)
                # Auto-save after most commands (except save/load/help which manage state themselves)
                if cmd not in ['save', 'load', 'help', 'h', '?', 'quit', 'q', 'exit']:
                    self.game_engine.save_game()
                return result
            except Exception as e:
                print(f"❌ Error processing command '{cmd}': {str(e)}")
                return True
        else:
            print(f"❌ Unknown command: '{cmd}'. Type 'help' for available commands.")
            return True

    def help_command(self, args: List[str]) -> bool:
        """Show help information with dense formatting."""
        print("┌─ COMMANDS ─────────────────────────────────────────────────────────────────┐")
        print("│ help/h/?           │ Show this help message                       │")
        print("│ stats              │ Show player statistics (dense format)             │")
        print("│ look/l             │ Look around current room + local map              │")
        print("│ go/move n/s/e/w/u/d│ Move in direction                              │")
        print("│ attack <num>        │ Attack monster <num>                             │")
        print("│ take/get <num>      │ Take item <num> from room                        │")
        print("│ equip <num>        │ Equip item <num> from inventory                  │")
        print("│ use <num>          │ Use consumable <num> from inventory               │")
        print("│ inventory/i        │ Show inventory (dense format)                    │")
        print("│ talk/speak <num>    │ Talk to NPC <num> in room                        │")
        print("│ map                │ Show full current floor map                     │")
        print("│ local/lm           │ Show 5x5 local map around player                 │")
        print("│ items/item         │ Show map with item locations                     │")
        print("│ stairs/staircase    │ Show stair locations on current floor               │")
        print("│ save               │ Save game to savegame.json                       │")
        print("│ load               │ Load game from savegame.json                     │")
        print("│ clear              │ Delete save and log files                      │")
        print("│ log/history <num>   │ View last <num> log lines (default: 10)          │")
        print("│ quit/q/exit        │ Exit game                                      │")
        print("├─ TIPS ──────────────────────────────────────────────────────────────────┤")
        print("│ • Move: n/s/e/w/u/d • Room: numbered items/monsters/NPCs                │")
        print("│ • 'local' = 5x5 map  • 'items' = item locs • 'log' = history    │")
        print("└────────────────────────────────────────────────────────────────────────┘")
        return True

    def stats_command(self, args: List[str]) -> bool:
        """Show player statistics."""
        self.game_engine.show_stats()
        return True

    def look_command(self, args: List[str]) -> bool:
        """Look around the current room."""
        self.game_engine.look_around_with_map()
        return True

    def go_command(self, args: List[str]) -> bool:
        """Move in a specified direction."""
        if not args:
            print("❌ Please specify a direction (north/south/east/west/up/down).")
            return True
        
        try:
            direction = Direction(args[0])
            success = self.game_engine.move_player(direction)
            if not success:
                print(f"❌ You cannot move {direction.value}.")
        except ValueError:
            print(f"❌ Invalid direction: {args[0]}. Valid directions are: north, south, east, west, up, down")
        
        return True

    move_command = go_command  # Alias for move command

    def attack_command(self, args: List[str]) -> bool:
        """Attack a monster."""
        if not args:
            print("❌ Please specify which monster to attack (by number).")
            return True
        
        try:
            monster_num = int(args[0])
            success = self.game_engine.attack_enemy(monster_num)
            if not success:
                print("❌ Failed to attack that monster.")
        except ValueError:
            print(f"❌ Invalid monster number: {args[0]}.")
        
        return True

    def take_command(self, args: List[str]) -> bool:
        """Take an item."""
        if not args:
            print("❌ Please specify which item to take (by number).")
            return True
        
        try:
            item_num = int(args[0])
            success = self.game_engine.take_item(item_num)
            if not success:
                print("❌ Failed to take that item.")
        except ValueError:
            print(f"❌ Invalid item number: {args[0]}.")
        
        return True

    def equip_command(self, args: List[str]) -> bool:
        """Equip an item."""
        if not args:
            print("❌ Please specify which item to equip (by number).")
            return True
        
        try:
            item_num = int(args[0])
            if 1 <= item_num <= len(self.game_engine.player.inventory):
                item = self.game_engine.player.inventory[item_num - 1]
                self.game_engine.player.equip_item(item)
                print(f"装备 Equipped {item.name}.")
            else:
                print(f"❌ Invalid item number: {item_num}.")
        except ValueError:
            print(f"❌ Invalid item number: {args[0]}.")
        
        return True

    def use_command(self, args: List[str]) -> bool:
        """Use an item."""
        if not args:
            print("❌ Please specify which item to use (by number).")
            return True
        
        try:
            item_num = int(args[0])
            success = self.game_engine.use_item(item_num)
            # The use_item method already handles success/failure messages
        except ValueError:
            print(f"❌ Invalid item number: {args[0]}.")
        
        return True

    def inventory_command(self, args: List[str]) -> bool:
        """Show player inventory with dense formatting."""
        # Filter out Stair objects from inventory display
        from classes.new_dungeon import Stair
        inventory_items = [item for item in self.game_engine.player.inventory if not isinstance(item, Stair)]
        
        if not inventory_items:
            print("┌─ INVENTORY ─────────────────────────────────────────────────────────┐")
            print("│                    (empty)                                      │")
            print("└────────────────────────────────────────────────────────────────┘")
        else:
            print("┌─ INVENTORY ─────────────────────────────────────────────────────────┐")
            for i, item in enumerate(inventory_items, 1):
                equipped = "*" if item == self.game_engine.player.equipped_weapon or item == self.game_engine.player.equipped_armor else " "
                value_str = f"VAL:{item.value:>3}" if item.value > 0 else ""
                type_str = f"TYPE:{item.item_type.value[:3]:>3}" if hasattr(item, 'item_type') else "TYPE:---"
                print(f"│ {equipped}{i:>2}. {item.name:<20} {type_str} {value_str:<8} │")
            
            weapon = self.game_engine.player.equipped_weapon.name if self.game_engine.player.equipped_weapon else "None"
            armor = self.game_engine.player.equipped_armor.name if self.game_engine.player.equipped_armor else "None"
            print(f"├─ WPN:{weapon:<15} ARM:{armor:<15} ─────────────────────┘")
        
        return True

    def map_command(self, args: List[str]) -> bool:
        """Show the map of the current floor."""
        if args and len(args) == 1:
            try:
                floor_num = int(args[0])
                self.game_engine.visualize_floor(floor_num - 1)  # Convert to 0-indexed
            except ValueError:
                print(f"❌ Invalid floor number: {args[0]}.")
        else:
            self.game_engine.visualize_floor()
        return True

    def save_command(self, args: List[str]) -> bool:
        """Save the game."""
        self.game_engine.save_game()
        return True

    def load_command(self, args: List[str]) -> bool:
        """Load the game."""
        self.game_engine.load_game()
        return True

    def quit_command(self, args: List[str]) -> bool:
        """Quit the game."""
        return False  # Return False to indicate game should exit

    def talk_command(self, args: List[str]) -> bool:
        """Talk to an NPC."""
        if not args:
            print("❌ Please specify which NPC to talk to (by number).")
            return True
        
        try:
            npc_num = int(args[0])
            success = self.game_engine.talk_to_npc(npc_num)
            if not success:
                print("❌ Failed to talk to that NPC.")
        except ValueError:
            print(f"❌ Invalid NPC number: {args[0]}.")
        
        return True

    def clear_command(self, args: List[str]) -> bool:
        """Clear save files and log files."""
        print("⚠️  WARNING: This will permanently delete all save files and log files.")
        confirm = input("Type 'YES' to confirm: ").strip()
        
        if confirm == "YES":
            self.game_engine.clear_save_and_logs()
        else:
            print("❌ Clear operation cancelled.")
        
        return True

    def log_command(self, args: List[str]) -> bool:
        """View game log history."""
        lines = 20  # Default number of lines
        
        if args and len(args) == 1:
            try:
                lines = int(args[0])
                if lines <= 0:
                    print("❌ Please specify a positive number of lines to show.")
                    return True
            except ValueError:
                print(f"❌ Invalid number: {args[0]}.")
                return True
        
        self.game_engine.view_log_history(lines)
        return True

    def local_map_command(self, args: List[str]) -> bool:
        """Show a 5x5 map around the player."""
        self.game_engine.show_local_map()
        return True

    def stairs_command(self, args: List[str]) -> bool:
        """Show locations of stairs on the current floor."""
        print("\n🪜 STAIRS LOCATION MAP")
        print("Showing locations of rooms with stairs...")
        self.game_engine.show_stairs_locations()
        return True

    def items_map_command(self, args: List[str]) -> bool:
        """Show a map highlighting locations with items."""
        print("\n🔍 ITEM LOCATION MAP")
        print("Showing locations of rooms that contain items...")
        if args and len(args) == 1:
            try:
                floor_num = int(args[0])
                self.game_engine.visualize_floor(floor_num - 1)  # Convert to 0-indexed
            except ValueError:
                print(f"❌ Invalid floor number: {args[0]}.")
        else:
            self.game_engine.visualize_floor()
        return True