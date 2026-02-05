#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, 'src')

from src.game_engine import SeededGameEngine
from src.command_processor import CommandProcessor

def main():
    print('🏰 TERMINAL DUNGEON CRAWLER 🐉')
    print('===============================')
    
    # Get seed from command line argument or generate random
    seed = None
    if len(sys.argv) > 1:
        try:
            seed = int(sys.argv[1])
        except ValueError:
            print(f'Invalid seed: {sys.argv[1]}, using random seed')
            seed = None
    
    # Create game instance
    game = SeededGameEngine(seed)
    processor = CommandProcessor(game)
    
    print(f'Dungeon Seed: {game.seed}')
    print()
    
    # Show initial room
    print('You enter the dungeon...')
    processor.process_command('look')
    print()
    
    # Main game loop
    while not game.is_game_over():
        try:
            command = input('> ').strip()
            if not command:
                continue
            
            # Process command
            continue_game = processor.process_command(command)
            if not continue_game:
                break
            
            print()  # Extra line for readability
            
        except KeyboardInterrupt:
            print('\n\n👋 Thanks for playing! Goodbye!')
            break
        except EOFError:
            print('\n\n👋 Thanks for playing! Goodbye!')
            break
    
    if game.player.victory:
        print('\n🎉 CONGRATULATIONS! You have conquered the dungeon! 🏆')
    elif not game.player.is_alive():
        print('\n💀 You have been defeated... Better luck next time! 😵')
    else:
        print('\n👋 Thanks for playing! Come back anytime!')

if __name__ == '__main__':
    main()