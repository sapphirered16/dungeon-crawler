#!/usr/bin/env python3
"""Test script to examine hallway creation."""

import sys
sys.path.insert(0, './src')

from src.classes.new_dungeon import SeededDungeon

# Create a dungeon with a specific seed
dungeon = SeededDungeon(seed=12345)

print("Room details:")
for i, room in enumerate(dungeon.rooms[:10]):  # First 10 rooms
    print(f"Room {i+1}: type={room.room_type}, pos=({room.x},{room.y}), size={room.width}x{room.height}, center={room.get_center()}")

print(f"\nTotal rooms: {len(dungeon.rooms)}")

print("\nChecking some hallway positions between rooms...")
# Check if there are hallways between some known rooms
floor_rooms = [room for room in dungeon.rooms if room.z == 0]
if len(floor_rooms) > 1:
    room1 = floor_rooms[0]  # entrance
    room2 = floor_rooms[1]  # next room
    
    print(f"Room 1 (entrance): {room1.room_type} at ({room1.x},{room1.y}) size {room1.width}x{room1.height}")
    print(f"Room 2: {room2.room_type} at ({room2.x},{room2.y}) size {room2.width}x{room2.height}")
    
    # Check positions between them for hallways
    center1 = room1.get_center()
    center2 = room2.get_center()
    print(f"Center 1: {center1}")
    print(f"Center 2: {center2}")
    
    # Check a few positions along the path
    for i in range(0, 5):  # Check 5 positions along the path
        ratio = i / 4.0 if i < 4 else 1.0  # 0.0, 0.25, 0.5, 0.75, 1.0
        x = int(center1[0] + (center2[0] - center1[0]) * ratio)
        y = int(center1[1] + (center2[1] - center1[1]) * ratio)
        z = center1[2]  # Same floor
        
        pos = (x, y, z)
        cell_type = dungeon.get_cell_type_at_position(pos)
        room_at_pos = dungeon.get_room_at_position(pos)
        
        print(f"  Pos ({x},{y}): cell_type={cell_type}, room={room_at_pos.room_type if room_at_pos else 'None'}")