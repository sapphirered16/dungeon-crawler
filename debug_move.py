#!/usr/bin/env python3
"""Debug script to test movement functionality."""

import sys
import os
# Add the parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.new_game_engine import SeededGameEngine
from src.classes.base import Direction

# Create a game with a specific seed
game = SeededGameEngine(seed=12345)

print(f"Initial player position: {game.player.position}")
print(f"Current room type: {game.current_room.room_type}")
print(f"Current room bounds: ({game.current_room.x}, {game.current_room.y}) to ({game.current_room.x + game.current_room.width - 1}, {game.current_room.y + game.current_room.height - 1})")

# Check what happens when we try to move south
# Simulate the movement calculation
old_pos = game.player.position
print(f"Old position: {old_pos}")

new_x, new_y, new_z = old_pos
print(f"Parsed coordinates: x={new_x}, y={new_y}, z={new_z}")

# Try moving south
new_y += 1
new_pos = (new_x, new_y, new_z)
print(f"New position after moving south: {new_pos}")

# Check cell type at new position
cell_type = game.dungeon.get_cell_type_at_position(new_pos)
print(f"Cell type at new position: {cell_type}")

# Check if there's a room at the new position
new_room = game.dungeon.get_room_at_position(new_pos)
print(f"Room at new position: {new_room}")

print("\nTesting movement...")
result = game.move_player(Direction.SOUTH)
print(f"Movement result: {result}")