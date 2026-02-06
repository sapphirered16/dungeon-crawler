#!/usr/bin/env python3
"""Main entry point for the dungeon crawler game."""

import sys
import argparse
from .new_game_engine import SeededGameEngine
from .command_processor import CommandProcessor


def main():
    parser = argparse.ArgumentParser(description="Dungeon Crawler Game")
    parser.add_argument("--seed", type=int, help="Set the random seed for dungeon generation")
    parser.add_argument("--load", action="store_true", help="Load a saved game")
    parser.add_argument("command", nargs="?", help="Optional command to run (for single command execution)")
    parser.add_argument("args", nargs="*", help="Additional arguments for the command")
    
    args = parser.parse_args()
    
    # Create game engine
    seed = args.seed or None
    game = SeededGameEngine(seed=seed)
    
    # Load game if requested
    if args.load:
        game.load_game()
    
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