#!/usr/bin/env python3
"""Check room spacing."""

import sys
sys.path.insert(0, './src')

from src.classes.new_dungeon import SeededDungeon

# Create a dungeon with a specific seed
dungeon = SeededDungeon(seed=12345)

rooms = sorted(dungeon.rooms, key=lambda r: (r.x, r.y))
print("Room positions and sizes:")
for i, room in enumerate(rooms[:10]):  # First 10 rooms
    print(f"Room {i+1}: type={room.room_type}, pos=({room.x},{room.y}), size={room.width}x{room.height}")
    print(f"  Covers x: {room.x} to {room.x + room.width - 1}, y: {room.y} to {room.y + room.height - 1}")
    
    # Check nearby positions for different cell types
    print(f"  Nearby cell types:")
    for dx in range(-3, room.width + 3):
        for dy in range(-3, room.height + 3):
            x, y = room.x + dx, room.y + dy
            if dx < 0 or dx >= room.width or dy < 0 or dy >= room.height:  # Outside room
                pos = (x, y, room.z)
                cell_type = dungeon.get_cell_type_at_position(pos)
                if cell_type != 'empty':  # Non-empty outside the room
                    print(f"    ({x},{y}): {cell_type}")
    print()