#!/usr/bin/env python3
"""Check specific position."""

import sys
sys.path.insert(0, './src')

from src.classes.new_dungeon import SeededDungeon

# Create a dungeon with a specific seed
dungeon = SeededDungeon(seed=12345)

pos_to_check = (5, 10, 0)
cell_type = dungeon.get_cell_type_at_position(pos_to_check)
room_at_pos = dungeon.get_room_at_position(pos_to_check)

print(f"Position (5, 10, 0):")
print(f"  Cell type: {cell_type}")
print(f"  Room at position: {room_at_pos.room_type if room_at_pos else 'None'}")

# Check surrounding positions too
for dx, dy in [(0,-1), (0,1), (-1,0), (1,0)]:  # N, S, W, E
    adj_pos = (4+dx, 10+dy, 0)
    adj_cell_type = dungeon.get_cell_type_at_position(adj_pos)
    adj_room = dungeon.get_room_at_position(adj_pos)
    print(f"  Adjacent ({adj_pos}): cell_type={adj_cell_type}, room={adj_room.room_type if adj_room else 'None'}")