#!/usr/bin/env python3
"""Main entry point for the dungeon crawler game."""

import sys
import argparse
import os
sys.path.append(os.path.dirname(__file__))  # Add the src directory to the path

from new_game_engine import SeededGameEngine
from command_processor import CommandProcessor


def main():
    # Import at the beginning to avoid scope issues
    import random
    
    parser = argparse.ArgumentParser(description="Dungeon Crawler Game")
    parser.add_argument("--seed", type=int, help="Set the random seed for dungeon generation")
    parser.add_argument("--newgame", action="store_true", help="Start a new game (ignores any saved game)")
    parser.add_argument("command", nargs="?", help="Optional command to run (for single command execution)")
    parser.add_argument("args", nargs="*", help="Additional arguments for the command")
    
    args = parser.parse_args()
    
    # Handle newgame command
    if args.command == "newgame" or args.newgame:
        print("🆕 Starting a new game...")
        
        # Use the seed from args.seed if provided, otherwise generate a random one
        seed = args.seed
        if seed is None:
            seed = random.randint(10000, 99999)
            print(f"🎲 Generated random seed: {seed}")
        else:
            print(f"🎲 Using provided seed: {seed}")
        
        # Create a new game engine with the seed
        game = SeededGameEngine(seed=seed)
        
        # Fully generate the dungeon with all items, enemies, NPCs, obstacles, etc.
        # This ensures everything is pre-generated and deterministic
        print("🗺️  Generating full dungeon with all content...")
        
        # The game engine constructor should already generate the full dungeon
        # based on the seed, but let's ensure it's fully populated
        game.initialize_full_dungeon()
        
        # Save the fully generated game
        game.save_game()
        print("💾 New game with full dungeon saved to savegame.json")
        return  # Exit after creating new game
    
    # Create game engine
    seed = args.seed or None
    game = SeededGameEngine(seed=seed)
    
    # Default behavior: load game automatically if save file exists
    import os
    if os.path.exists("savegame.json"):
        try:
            game.load_game()
            print("📂 Game loaded from savegame.json")
        except Exception as e:
            print(f"⚠️  Could not load save file: {e}. Starting new game.")
            if seed is not None:
                game = SeededGameEngine(seed=seed)
    # If no save file exists, continue with the newly created game
    
    # Create command processor
    command_processor = CommandProcessor(game)
    
    # If a command was provided, execute it and exit
    if args.command:
        # Combine command and args into a single string
        full_command = args.command
        if args.args:
            full_command += " " + " ".join(args.args)
        
        # Execute the command
        command_processor.process_command(full_command)
        return
    
    # Otherwise, run in interactive mode
    print("🏰 Welcome to the Dungeon Crawler! 🐉")
    print("Type 'help' for available commands.\n")
    
    # Show initial room
    command_processor.process_command('look')
    print()
    
    # Main game loop
    game_running = True
    while game_running and not game.is_game_over():
        try:
            # Get user input
            command = input(" >> ").strip()
            
            # Process command
            game_running = command_processor.process_command(command)
            
        except KeyboardInterrupt:
            print("\n\n👋 Game interrupted. Goodbye!")
            break
        except EOFError:
            break
    
    # Game over message
    if game.is_game_over():
        if game.player.victory:
            print("\n🎉 CONGRATULATIONS! You have conquered the dungeon! 🏆")
        elif not game.player.is_alive():
            print("\n💀 You have been defeated... Better luck next time! 😵")
        else:
            print(f"\nFinal Score: {game.player.score}")
    else:
        pass


if __name__ == "__main__":
    main()