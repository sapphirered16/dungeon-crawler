"""
Batch command processor for the dungeon crawler game
Allows processing multiple commands in sequence
"""

import sys
import time
import shlex
sys.path.insert(0, '.')  # Add current directory to path

from new_game_engine import SeededGameEngine as GameEngine, Direction


class BatchProcessor:
    def __init__(self):
        self.game = GameEngine()
        # Try to load existing game state
        self.game.load_game()
    
    def process_batch_commands(self, commands):
        """
        Process a list of commands in sequence
        """
        print("=== BATCH COMMAND PROCESSOR ===")
        print(f"Processing {len(commands)} commands...\n")
        
        for i, command in enumerate(commands, 1):
            print(f"[{i}/{len(commands)}] Executing: {command}")
            
            # Process the command
            try:
                self._execute_single_command(command.strip())
                
                # Brief pause to make output readable
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error executing command '{command}': {e}")
                continue
        
        print(f"\nCompleted processing {len(commands)} commands.")
        print("\nCurrent Status:")
        self.game.show_stats()
        
        # Auto-save after batch processing
        self.game.save_game()
        print("Game saved after batch processing.")
    
    def _execute_single_command(self, command):
        """
        Execute a single command (similar to main function logic)
        """
        command = command.lower().strip()
        
        if command in ["quit", "exit"]:
            print("Exiting batch mode...")
            return
        
        elif command.startswith("move "):
            direction_str = command[5:].strip()
            try:
                direction = Direction(direction_str)
                self.game.move_player(direction)
            except ValueError:
                print(f"Invalid direction: {direction_str}")
        
        elif command.startswith("attack "):
            try:
                enemy_num = int(command[7:])
                self.game.attack_enemy(enemy_num)
            except ValueError:
                print("Please specify a valid enemy number to attack.")
        
        elif command.startswith("take "):
            try:
                item_num = int(command[5:])
                self.game.take_item(item_num)
            except ValueError:
                print("Please specify a valid item number to take.")
        
        elif command.startswith("equip "):
            try:
                item_num = int(command[6:])
                self.game.equip_item(item_num)
            except ValueError:
                print("Please specify a valid item number to equip.")
        
        elif command.startswith("unequip "):
            item_type = command[8:].strip().lower()
            if item_type in ["weapon", "armor"]:
                self.game.unequip_item(item_type)
            else:
                print("Please specify a valid item type to unequip: 'weapon' or 'armor'.")
        
        elif command.startswith("talk "):
            try:
                npc_num = int(command[5:])
                self.game.talk_to_npc(npc_num)
            except ValueError:
                print("Please specify a valid NPC number to talk to.")
        
        elif command == "look":
            self.game.look_around()
        
        elif command == "inventory":
            self.game.show_inventory()
        
        elif command == "stats":
            self.game.show_stats()
        
        elif command == "rest":
            self.game.rest()
        
        elif command == "save":
            self.game.save_game()
            print("Game saved.")
        
        elif command == "load":
            if self.game.load_game():
                print("Game loaded.")
            else:
                print("No save file found.")
        
        else:
            print(f"Unknown command: {command}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_processor.py <command1> <command2> ...")
        print("Example: python batch_processor.py 'move north' 'move east' 'attack 1' stats")
        print("Note: Use quotes around commands with spaces")
        return
    
    # Get commands from command line arguments
    commands = sys.argv[1:]
    
    # Create batch processor and execute commands
    processor = BatchProcessor()
    processor.process_batch_commands(commands)


if __name__ == "__main__":
    main()