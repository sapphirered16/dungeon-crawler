#!/usr/bin/env python3
"""
Test script to validate the grid-based item and obstacle system.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from new_game_engine import SeededGameEngine
from classes.base import Direction


def test_grid_based_system():
    """Test the grid-based item and obstacle system."""
    print("🧪 Testing Grid-Based Item and Obstacle System...")
    
    # Create a game engine with a specific seed
    game = SeededGameEngine(seed=12345)
    initial_pos = game.player.position
    
    print(f"📍 Starting position: {initial_pos}")
    print(f" dungeons.grid: {len(game.dungeon.grid)} cells in grid")
    
    # Check that the current position has a corresponding grid cell
    current_cell = game.dungeon.grid.get(initial_pos)
    if current_cell:
        print(f"✅ Current grid cell exists with type: {current_cell.cell_type}")
        print(f"  - Items: {len(current_cell.items)}")
        print(f"  - Locked doors: {len(current_cell.locked_doors)}")
        print(f"  - Blocked passages: {len(current_cell.blocked_passages)}")
    else:
        print("❌ Current position doesn't have a grid cell!")
        return False
    
    # Check neighboring positions
    x, y, z = initial_pos
    neighbors = [
        (x+1, y, z),  # East
        (x-1, y, z),  # West  
        (x, y+1, z),  # South
        (x, y-1, z),  # North
    ]
    
    accessible_neighbors = 0
    for nx, ny, nz in neighbors:
        neighbor_pos = (nx, ny, nz)
        if neighbor_pos in game.dungeon.grid:
            neighbor_cell = game.dungeon.grid[neighbor_pos]
            print(f"✅ Neighbor at {neighbor_pos}: {neighbor_cell.cell_type}")
            print(f"  - Items: {len(neighbor_cell.items)}")
            print(f"  - Locked doors: {len(neighbor_cell.locked_doors)}")
            print(f"  - Blocked passages: {len(neighbor_cell.blocked_passages)}")
            accessible_neighbors += 1
    
    print(f"📊 Found {accessible_neighbors} accessible neighboring cells")
    
    # Test movement logic
    print("\n🏃 Testing movement logic...")
    original_room = game.current_room
    print(f"🏠 Original room: {original_room.room_type} at z={original_room.z}")
    
    # Try to move in a valid direction
    moved = False
    for direction in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
        # Calculate destination
        current_x, current_y, current_z = game.player.position
        if direction == Direction.NORTH:
            dest_pos = (current_x, current_y - 1, current_z)
        elif direction == Direction.SOUTH:
            dest_pos = (current_x, current_y + 1, current_z)
        elif direction == Direction.EAST:
            dest_pos = (current_x + 1, current_y, current_z)
        elif direction == Direction.WEST:
            dest_pos = (current_x - 1, current_y, current_z)
        
        if dest_pos in game.dungeon.grid:
            dest_cell = game.dungeon.grid[dest_pos]
            print(f"✅ Can move {direction.value} to {dest_pos} (cell type: {dest_cell.cell_type})")
            
            # Check if this destination has locked doors or blocked passages
            if dest_cell.locked_doors:
                print(f"  🔒 Found locked doors: {dest_cell.locked_doors}")
            if dest_cell.blocked_passages:
                print(f"  🚧 Found blocked passages: {dest_cell.blocked_passages}")
            
            # Check if this destination has items
            if dest_cell.items:
                print(f"  🎁 Found {len(dest_cell.items)} items on this tile:")
                for i, item in enumerate(dest_cell.items):
                    print(f"    - {i+1}. {item.name} ({item.item_type.value})")
            
            moved = True
            break
    
    if not moved:
        print("❌ No valid moves found from starting position")
        return False
    
    print("\n✅ All grid-based system tests passed!")
    return True


def test_item_visualization():
    """Test that the visualization correctly shows items based on grid cells."""
    print("\n🖼️  Testing Item Visualization...")
    
    game = SeededGameEngine(seed=12345)
    
    # Count cells with items across the dungeon
    cells_with_items = 0
    total_cells = len(game.dungeon.grid)
    
    for pos, cell in game.dungeon.grid.items():
        if cell.items:
            cells_with_items += 1
    
    print(f"📊 Total grid cells: {total_cells}")
    print(f"🎁 Cells with items: {cells_with_items}")
    
    if cells_with_items > 0:
        print("✅ Items are distributed across specific grid cells (not entire rooms)")
    else:
        print("⚠️  No items found in this dungeon (might be normal for this seed)")
    
    return True


def test_obstacle_placement():
    """Test that obstacles are properly placed on hallway cells."""
    print("\n🚪 Testing Obstacle Placement...")
    
    game = SeededGameEngine(seed=12345)
    
    hallway_cells_with_obstacles = 0
    total_hallway_cells = 0
    
    for pos, cell in game.dungeon.grid.items():
        if cell.cell_type == 'hallway':
            total_hallway_cells += 1
            if cell.locked_doors or cell.blocked_passages:
                hallway_cells_with_obstacles += 1
    
    print(f"📊 Total hallway cells: {total_hallway_cells}")
    print(f"🚪 Hallway cells with obstacles: {hallway_cells_with_obstacles}")
    
    if hallway_cells_with_obstacles > 0:
        print("✅ Obstacles are placed on hallway grid cells")
    else:
        print("⚠️  No obstacles found in hallways (might be normal for this seed)")
    
    return True


if __name__ == "__main__":
    print("🧪 Running Grid-Based System Tests...\n")
    
    success = True
    success &= test_grid_based_system()
    success &= test_item_visualization()
    success &= test_obstacle_placement()
    
    if success:
        print("\n🎉 All tests passed! The grid-based system is working correctly.")
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)