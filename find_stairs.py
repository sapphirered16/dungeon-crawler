#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.new_game_engine import SeededGameEngine
from src.classes.base import Direction
import random

def find_stairs_game():
    print("🎮 Continuing dungeon exploration to find stairs to 2nd floor...")
    
    # Create game instance
    game = SeededGameEngine(seed=12345)
    
    print(f"📍 Starting position: {game.player.position}")
    print(f"🏠 Starting room: {game.current_room.room_type if game.current_room else 'None'}")
    print(f"❤️  Player HP: {game.player.health}/{game.player.max_health}")
    print()
    
    # Explore for a number of turns to find stairs
    turns = 0
    max_turns = 50
    
    while turns < max_turns and not game.is_game_over():
        turns += 1
        print(f"--- TURN {turns} ---")
        
        # Check if current room has stairs up
        current_pos = game.player.position
        if current_pos in game.dungeon.grid:
            current_cell = game.dungeon.grid[current_pos]
            if current_cell.room_ref and hasattr(current_cell.room_ref, 'has_stairs_up') and current_cell.room_ref.has_stairs_up:
                print(" staircase going UP! Attempting to go to next floor...")
                # Try to go up - this would normally be handled by a command
                # Since the game engine may not have a direct method, let's look at available moves
                pass
        
        # Show current room description
        print(f"--- {game.current_room.description if game.current_room else 'Empty space'} ---")
        
        # Show stairs locations
        print("Stairs locations on current floor:")
        game.show_stairs_locations()
        
        # Check adjacent positions to see where we can move
        px, py, pz = game.player.position
        adjacent = [
            (Direction.NORTH, (px, py-1, pz)),
            (Direction.SOUTH, (px, py+1, pz)),
            (Direction.EAST, (px+1, py, pz)),
            (Direction.WEST, (px-1, py, pz))
        ]
        
        available_moves = []
        for direction, pos in adjacent:
            if pos in game.dungeon.grid:
                cell = game.dungeon.grid[pos]
                # Check if there's a locked door or blocked passage that prevents movement
                current_pos = (px, py, pz)
                if current_pos in game.dungeon.grid:
                    current_cell = game.dungeon.grid[current_pos]
                    locked_door = current_cell.locked_doors.get(direction)
                    blocked_passage = current_cell.blocked_passages.get(direction)
                    
                    if not locked_door and not blocked_passage:
                        available_moves.append(direction)
        
        print(f"Moves available: {[direction.value for direction in available_moves]}")
        
        # Show local map
        print("📍 Local Map:")
        game.show_local_map_no_legend()
        
        # Show player status
        print(f"HP: {game.player.health}/{game.player.max_health}, Level: {game.player.level}")
        print(f"Position: {game.player.position}")
        print(f"Floor: {game.player.position[2]}")
        
        # Try to take any items in the current location
        current_pos = game.player.position
        if current_pos in game.dungeon.grid:
            cell = game.dungeon.grid[current_pos]
            if cell.items:
                print(f"📦 Found {len(cell.items)} items in this location!")
                # Take the first item
                if len(cell.items) > 0:
                    result = game.take_item(1)  # Takes first item
                    print(f"Taken item: {result}")
        
        # Move in a direction
        if available_moves:
            # Try to prioritize directions that might lead to stairs
            # Look for directions that have stairs nearby in the room data
            directions_with_stairs_nearby = []
            for direction in available_moves:
                # Calculate where this direction leads
                if direction == Direction.NORTH:
                    new_pos = (px, py-1, pz)
                elif direction == Direction.SOUTH:
                    new_pos = (px, py+1, pz)
                elif direction == Direction.EAST:
                    new_pos = (px+1, py, pz)
                elif direction == Direction.WEST:
                    new_pos = (px-1, py, pz)
                
                if new_pos in game.dungeon.grid:
                    cell = game.dungeon.grid[new_pos]
                    if cell.room_ref and (getattr(cell.room_ref, 'has_stairs_up', False) or getattr(cell.room_ref, 'has_stairs_down', False)):
                        directions_with_stairs_nearby.append(direction)
            
            if directions_with_stairs_nearby:
                chosen_direction = random.choice(directions_with_stairs_nearby)
                print(f"🎯 Moving toward stairs: {chosen_direction.value}")
            else:
                chosen_direction = random.choice(available_moves)
                print(f"🧭 Moving: {chosen_direction.value}")
            
            # Actually move using the move_player method
            success = game.move_player(chosen_direction)
            if not success:
                print(f"❌ Could not move {chosen_direction.value}")
        else:
            print("❌ No available moves!")
            break
            
        print()
        
        # Process any monster AI after movement
        game.process_monster_ai()
        
        # Check if we've moved to a new floor (this happens when stepping on stairs)
        new_floor = game.player.position[2]
        if new_floor > 0:
            print(f"🏆 SUCCESS! Reached floor {new_floor}!")
            print(f"Final position: {game.player.position}")
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
    find_stairs_game()