#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.new_game_engine import SeededGameEngine
from src.classes.base import Direction
import math

def head_to_stairs_game():
    print("🎮 Heading toward the down stairs at (9, 16) on floor 0...")
    
    # Create game instance
    game = SeededGameEngine(seed=12345)
    
    print(f"📍 Starting position: {game.player.position}")
    print(f"🏠 Starting room: {game.current_room.room_type if game.current_room else 'None'}")
    print(f"❤️  Player HP: {game.player.health}/{game.player.max_health}")
    print()
    
    # Target position for stairs
    target_x, target_y = 9, 16
    start_x, start_y, start_z = game.player.position
    
    # Check if we're already at the target
    current_x, current_y, current_z = game.player.position
    if current_x == target_x and current_y == target_y:
        print("🎯 Already at the stairs!")
    
    # Explore to find the down stairs
    turns = 0
    max_turns = 100
    
    while turns < max_turns and not game.is_game_over():
        turns += 1
        print(f"--- TURN {turns} ---")
        
        # Check current position
        current_x, current_y, current_z = game.player.position
        print(f"Current position: ({current_x}, {current_y}, {current_z})")
        print(f"Target position: ({target_x}, {target_y})")
        print(f"Distance: {abs(current_x - target_x) + abs(current_y - target_y)} steps")
        
        # Show current room description
        print(f"--- {game.current_room.description if game.current_room else 'Empty space'} ---")
        
        # Show stairs locations
        print("Stairs locations on current floor:")
        game.show_stairs_locations()
        
        # Check if we've reached the stairs
        if current_x == target_x and current_y == target_y:
            print("🏆 Reached the stairs location!")
            # The game should automatically take us to the next floor when we step on stairs
            # Let's continue moving in the same direction to see if we go down
            print(f"Attempting to go down from ({current_x}, {current_y}, {current_z})")
            break
        
        # Check adjacent positions to see where we can move
        adjacent = [
            (Direction.NORTH, (current_x, current_y-1, current_z)),
            (Direction.SOUTH, (current_x, current_y+1, current_z)),
            (Direction.EAST, (current_x+1, current_y, current_z)),
            (Direction.WEST, (current_x-1, current_y, current_z))
        ]
        
        available_moves = []
        for direction, pos in adjacent:
            if pos in game.dungeon.grid:
                cell = game.dungeon.grid[pos]
                # Check if there's a locked door or blocked passage that prevents movement
                current_pos = (current_x, current_y, current_z)
                if current_pos in game.dungeon.grid:
                    current_cell = game.dungeon.grid[current_pos]
                    locked_door = current_cell.locked_doors.get(direction)
                    blocked_passage = current_cell.blocked_passages.get(direction)
                    
                    if not locked_door and not blocked_passage:
                        available_moves.append((direction, pos))
        
        print(f"Moves available: {[move[0].value for move in available_moves]}")
        
        # Show local map
        print("📍 Local Map:")
        game.show_local_map_no_legend()
        
        # Show player status
        print(f"HP: {game.player.health}/{game.player.max_health}, Level: {game.player.level}")
        print(f"Position: {game.player.position}")
        print(f"Floor: {game.player.position[2]}")
        
        # If we have available moves, try to move toward the target
        if available_moves:
            # Calculate which move gets us closer to the target
            best_move = None
            min_distance = float('inf')
            
            for direction, pos in available_moves:
                dist = abs(pos[0] - target_x) + abs(pos[1] - target_y)
                if dist < min_distance:
                    min_distance = dist
                    best_move = (direction, pos)
            
            if best_move:
                direction, new_pos = best_move
                print(f"🎯 Moving toward stairs: {direction.value} to {new_pos}")
                
                # Actually move using the move_player method
                success = game.move_player(direction)
                if not success:
                    print(f"❌ Could not move {direction.value}")
            else:
                # If no move gets us closer, pick a random available move
                direction, pos = available_moves[0]
                print(f"🧭 Moving: {direction.value}")
                
                # Actually move using the move_player method
                success = game.move_player(direction)
                if not success:
                    print(f"❌ Could not move {direction.value}")
        else:
            print("❌ No available moves!")
            break
            
        print()
        
        # Process any monster AI after movement
        game.process_monster_ai()
        
        # Check if we've moved to a new floor (this happens when stepping on stairs)
        new_floor = game.player.position[2]
        if new_floor != current_z:  # We've changed floors
            print(f"🏆 FLOOR CHANGE! Moved from floor {current_z} to floor {new_floor}!")
            print(f"New position: {game.player.position}")
            if new_floor > 0:  # We've reached floor 1 (the second floor of the dungeon)
                print("🎉 Reached the second floor of the dungeon!")
                break
        
        # Check if we've won or lost
        if hasattr(game, 'game_won') and game.game_won:
            print("🏆 You won the game!")
            break
    
    print(f"🏁 Game ended after {turns} turns")
    print(f"Final HP: {game.player.health}/{game.player.max_health}")
    print(f"Level: {game.player.level}")
    print(f"Final position: {game.player.position}")
    print(f"Floor reached: {game.player.position[2]}")
    print(f"Inventory: {len(game.player.inventory)} items")
    for item in game.player.inventory:
        print(f"  - {item.name}")

if __name__ == "__main__":
    head_to_stairs_game()