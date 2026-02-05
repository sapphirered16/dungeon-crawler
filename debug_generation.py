#!/usr/bin/env python3
"""Debug script to check dungeon generation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.classes.dungeon import SeededDungeon

def debug_dungeon_generation():
    print(".DEBUG DUNGEON GENERATION.")
    print("=" * 50)
    
    # Create a dungeon with a specific seed
    dungeon = SeededDungeon(seed=1337)
    
    # Get all floor numbers
    floors = set(pos[2] for pos in dungeon.room_states.keys())
    print(f"All floors: {sorted(floors)}")
    
    # Find starting position (should be (12, 12, 0))
    start_pos = (12, 12, 0)
    if start_pos in dungeon.room_states:
        start_room = dungeon.room_states[start_pos]
        print(f"\nStarting position {start_pos}:")
        print(f"  Room type: {start_room.room_type}")
        print(f"  Description: {start_room.description}")
        print(f"  Items: {[item.name for item in start_room.items]}")
    else:
        print(f"\nStarting position {start_pos} NOT FOUND!")
        # Find what's at z=0
        z0_rooms = [pos for pos in dungeon.room_states.keys() if pos[2] == 0]
        print(f"Rooms at z=0: {z0_rooms}")
        for pos in z0_rooms:
            room = dungeon.room_states[pos]
            print(f"  {pos}: type={room.room_type}, desc='{room.description}', items={[item.name for item in room.items]}")
    
    # Find lowest floor
    lowest_floor = min(floors) if floors else 0
    highest_floor = max(floors) if floors else 0
    print(f"\nLowest floor: {lowest_floor}")
    print(f"Highest floor: {highest_floor}")
    
    # Check lowest floor rooms
    lowest_floor_rooms = [pos for pos in dungeon.room_states.keys() if pos[2] == lowest_floor]
    print(f"\nRooms on lowest floor ({lowest_floor}):")
    for pos in lowest_floor_rooms[:5]:  # Show first 5
        room = dungeon.room_states[pos]
        print(f"  {pos}: type={room.room_type}, desc='{room.description[:50]}...', items={[item.name for item in room.items]}")
    
    # Check if any artifact items exist on non-lowest floors
    print(f"\nChecking for misplaced artifacts...")
    artifact_found = False
    for pos, room in dungeon.room_states.items():
        floor = pos[2]
        artifacts_here = [item for item in room.items if item.item_type.value == "artifact"]
        if artifacts_here and floor != lowest_floor:
            print(f"  ERROR: Artifacts found on floor {floor} (not lowest floor {lowest_floor}): {artifacts_here}")
            print(f"    At position {pos}: {room.room_type} - '{room.description}'")
            artifact_found = True
    
    if not artifact_found:
        print("  ✓ No artifacts found on non-lowest floors")
    
    # Check lowest floor for artifact
    lowest_floor_artifacts = []
    for pos in lowest_floor_rooms:
        room = dungeon.room_states[pos]
        artifacts_here = [item for item in room.items if item.item_type.value == "artifact"]
        if artifacts_here:
            lowest_floor_artifacts.extend([(pos, room.room_type, [a.name for a in artifacts_here]) for a in artifacts_here])
    
    if lowest_floor_artifacts:
        print(f"\n✓ Artifacts found on lowest floor ({lowest_floor}):")
        for pos, room_type, artifact_names in lowest_floor_artifacts:
            print(f"  {pos} ({room_type}): {artifact_names}")
    else:
        print(f"\n⚠️ No artifacts found on lowest floor ({lowest_floor})")
    
    # Also check the highest (deepest) floor
    highest_floor_rooms = [pos for pos in dungeon.room_states.keys() if pos[2] == highest_floor]
    highest_floor_artifacts = []
    for pos in highest_floor_rooms:
        room = dungeon.room_states[pos]
        artifacts_here = [item for item in room.items if item.item_type.value == "artifact"]
        if artifacts_here:
            highest_floor_artifacts.extend([(pos, room.room_type, [a.name for a in artifacts_here]) for a in artifacts_here])
    
    if highest_floor_artifacts:
        print(f"\n✓ Artifacts found on highest/deepest floor ({highest_floor}):")
        for pos, room_type, artifact_names in highest_floor_artifacts:
            print(f"  {pos} ({room_type}): {artifact_names}")
    else:
        print(f"\n⚠️ No artifacts found on highest/deepest floor ({highest_floor})")

if __name__ == "__main__":
    debug_dungeon_generation()