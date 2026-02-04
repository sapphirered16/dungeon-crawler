"""Command processor for the dungeon crawler game."""

import re
from typing import List, Tuple, Optional
from .classes.base import Direction
from .game_engine import SeededGameEngine


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
            'save': self.save_command,
            'load': self.load_command,
            'quit': self.quit_command,
            'q': self.quit_command,
            'exit': self.quit_command,
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
            return True
        
        # Look for command in mapping
        if cmd in self.command_map:
            try:
                return self.command_map[cmd](args)
            except Exception as e:
                print(f"❌ Error processing command '{cmd}': {str(e)}")
                return True
        else:
            print(f"❌ Unknown command: '{cmd}'. Type 'help' for available commands.")
            return True

    def help_command(self, args: List[str]) -> bool:
        """Show help information."""
        print("\n📖 Available Commands:")
        print("  help/h/?          - Show this help message")
        print("  stats             - Show player statistics")
        print("  look/l            - Look around the current room")
        print("  go/move <dir>     - Move in a direction (north/south/east/west/up/down)")
        print("  attack <num>      - Attack monster number <num>")
        print("  take/get <num>    - Take item number <num>")
        print("  equip <num>       - Equip item number <num>")
        print("  use <num>         - Use consumable item number <num>")
        print("  inventory/i       - Show inventory")
        print("  map               - Show current floor map")
        print("  save              - Save game")
        print("  load              - Load game")
        print("  quit/q/exit       - Quit game")
        print("\n💡 Tips:")
        print("  - You can move directly by typing direction names (e.g., 'north')")
        print("  - Items and monsters are numbered in room descriptions")
        print("  - Type 'look' to see what's in the current room")
        return True

    def stats_command(self, args: List[str]) -> bool:
        """Show player statistics."""
        self.game_engine.show_stats()
        return True

    def look_command(self, args: List[str]) -> bool:
        """Look around the current room."""
        self.game_engine.look_around()
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
            if 1 <= item_num <= len(self.game_engine.player.inventory):
                item = self.game_engine.player.inventory[item_num - 1]
                if item.item_type == 'consumable':
                    # Use consumable (for example, healing potions)
                    if "health" in item.description.lower() or "potion" in item.name.lower():
                        heal_amount = min(item.value, self.game_engine.player.max_health - self.game_engine.player.health)
                        self.game_engine.player.heal(heal_amount)
                        print(f"🧪 Used {item.name}, healed {heal_amount} HP.")
                        # Remove used item
                        self.game_engine.player.inventory.remove(item)
                    else:
                        print(f"🧪 Used {item.name}.")
                else:
                    print(f"❌ You can't use {item.name} directly. Try equipping it instead.")
            else:
                print(f"❌ Invalid item number: {item_num}.")
        except ValueError:
            print(f"❌ Invalid item number: {args[0]}.")
        
        return True

    def inventory_command(self, args: List[str]) -> bool:
        """Show player inventory."""
        if not self.game_engine.player.inventory:
            print("🎒 Your inventory is empty.")
        else:
            print("\n🎒 Inventory:")
            for i, item in enumerate(self.game_engine.player.inventory, 1):
                print(f"  {i}. {item.name} (Value: {item.value})")
        
        if self.game_engine.player.equipped_weapon:
            print(f"\n⚔️  Equipped Weapon: {self.game_engine.player.equipped_weapon.name}")
        else:
            print("\n⚔️  Equipped Weapon: None")
        
        if self.game_engine.player.equipped_armor:
            print(f"🛡️  Equipped Armor: {self.game_engine.player.equipped_armor.name}")
        else:
            print("🛡️  Equipped Armor: None")
        
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
        print("👋 Thanks for playing! Goodbye!")
        return False  # Return False to indicate game should exit