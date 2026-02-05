#!/usr/bin/env python3
"""Check room connections."""

import sys
sys.path.insert(0, './src')

from src.classes.new_dungeon import SeededDungeon

# Create a dungeon with a specific seed
dungeon = SeededDungeon(seed=12345)

print("Room connections:")
for i, room in enumerate(dungeon.rooms[:10]):  # First 10 rooms
    if room.connections:
        print(f"Room {i+1} ({room.room_type} at {room.x},{room.y}):")
        for direction, pos in room.connections.items():
            print(f"  -> {direction}: {pos}")
    else:
        print(f"Room {i+1} ({room.room_type} at {room.x},{room.y}): No connections")

print("\nChecking if hallways exist between entrance and first few rooms...")

# Check specific positions for hallways
entrance_room = None
for room in dungeon.rooms:
    if room.room_type == "entrance":
        entrance_room = room
        break

if entrance_room:
    print(f"Entrance room center: {entrance_room.get_center()}")
    
    # Check nearby positions for hallways
    center_x, center_y, center_z = entrance_room.get_center()
    for dx in range(-5, 6):
        for dy in range(-5, 6):
            x, y = center_x + dx, center_y + dy
            pos = (x, y, center_z)
            cell_type = dungeon.get_cell_type_at_position(pos)
            if cell_type == 'hallway':
                print(f"Hallway found at ({x}, {y})")