#!/usr/bin/env python3
"""Test dungeon generation with smaller grid size."""

import sys
sys.path.insert(0, './src')
from src.classes.new_dungeon import SeededDungeon

print("Testing dungeon generation with 15x15 grid...")

# Create a dungeon with a smaller grid
dungeon = SeededDungeon(seed=12345, grid_width=15, grid_height=15)

print(f"Dungeon created with {len(dungeon.rooms)} rooms")
print(f"Grid size: {dungeon.grid_width}x{dungeon.grid_height}")

# Check room positions
print("\nRoom positions:")
for i, room in enumerate(dungeon.rooms):
    print(f"  {i+1}. {room.room_type} at ({room.x}, {room.y}) size {room.width}x{room.height}")

# Check hallway count
hallway_count = sum(1 for cell in dungeon.grid.values() if cell.cell_type == 'hallway')
print(f"\nHallway cells: {hallway_count}")
print(f"Room cells: {sum(1 for cell in dungeon.grid.values() if cell.cell_type == 'room')}")

# Check if rooms can fit in a 15x15 grid
print(f"\nGrid coverage analysis:")
min_x = min(room.x for room in dungeon.rooms)
max_x = max(room.x + room.width - 1 for room in dungeon.rooms)
min_y = min(room.y for room in dungeon.rooms)
max_y = max(room.y + room.height - 1 for room in dungeon.rooms)

print(f"X range: {min_x} to {max_x} (span: {max_x - min_x + 1})")
print(f"Y range: {min_y} to {max_y} (span: {max_y - min_y + 1})")
print(f"Grid dimensions: {dungeon.grid_width}x{dungeon.grid_height}")

# Check if it's reasonable for 15x15
if max_x >= dungeon.grid_width or max_y >= dungeon.grid_height:
    print("WARNING: Some rooms extend beyond grid boundaries!")
else:
    print("All rooms fit within the grid.")