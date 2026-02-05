"""Comprehensive test for the new dungeon system."""

from src.classes.dungeon import SeededDungeon
from src.game_engine import SeededGameEngine
from src.classes.base import Direction


def test_comprehensive_dungeon_system():
    """Comprehensive test of the new room-based dungeon system."""
    print("🧪 Running comprehensive dungeon system tests...")
    
    # Test 1: Create dungeons with different seeds
    print("\n1. Testing dungeon creation with different seeds...")
    for seed in [1, 42, 123, 999]:
        dungeon = SeededDungeon(seed=seed)
        print(f"   Seed {seed}: {len(dungeon.room_states)} tiles, {len(dungeon.rooms_by_id)} rooms, {len(dungeon.hallways)} hallways")
    
    # Test 2: Verify room dimensions and placement
    print("\n2. Testing room dimensions and placement...")
    dungeon = SeededDungeon(seed=100)
    
    # Check that rooms don't overlap
    rooms = list(dungeon.rooms_by_id.values())
    overlaps = 0
    for i, room1 in enumerate(rooms):
        for room2 in rooms[i+1:]:
            if room1.floor == room2.floor and room1.rect.intersects(room2.rect):
                overlaps += 1
    
    print(f"   Total rooms: {len(rooms)}")
    print(f"   Rooms with overlaps: {overlaps}")
    if overlaps == 0:
        print("   ✅ No overlapping rooms detected")
    else:
        print(f"   ❌ Found {overlaps} overlapping rooms")
    
    # Test 3: Verify hallway connections
    print("\n3. Testing hallway connections...")
    hallways = dungeon.hallways
    print(f"   Total hallways: {len(hallways)}")
    
    # Check if hallways connect actual rooms
    connected_rooms = set()
    for hallway in hallways:
        start_pos = hallway.start_pos + (hallway.floor,)
        end_pos = hallway.end_pos + (hallway.floor,)
        
        # Check if start and end positions have rooms nearby
        start_has_room = any(
            room.contains(start_pos[0], start_pos[1]) and room.floor == hallway.floor
            for room in rooms
        )
        end_has_room = any(
            room.contains(end_pos[0], end_pos[1]) and room.floor == hallway.floor
            for room in rooms
        )
        
        if start_has_room and end_has_room:
            connected_rooms.add((start_pos, end_pos))
    
    print(f"   Valid hallway connections: {len(connected_rooms)}")
    
    # Test 4: Test game engine movement
    print("\n4. Testing game engine movement...")
    engine = SeededGameEngine(seed=200)
    
    initial_pos = engine.player.position
    print(f"   Initial position: {initial_pos}")
    
    # Try moving in all directions
    moves_attempted = 0
    moves_successful = 0
    for direction in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
        moves_attempted += 1
        old_pos = engine.player.position
        success = engine.move_player(direction)
        if success:
            moves_successful += 1
            print(f"   Moved {direction.value}: {old_pos} -> {engine.player.position}")
            # Move back to initial position for next test
            opposite_dir = {
                Direction.NORTH: Direction.SOUTH,
                Direction.SOUTH: Direction.NORTH,
                Direction.EAST: Direction.WEST,
                Direction.WEST: Direction.EAST
            }[direction]
            engine.move_player(opposite_dir)
        else:
            print(f"   Failed to move {direction.value}")
    
    print(f"   Moves successful: {moves_successful}/{moves_attempted}")
    
    # Test 5: Test room types and content
    print("\n5. Testing room types and content...")
    room_types = {}
    for pos, room_state in dungeon.room_states.items():
        room_type = room_state.room_type
        if room_type not in room_types:
            room_types[room_type] = 0
        room_types[room_type] += 1
    
    print(f"   Room types distribution: {dict(sorted(room_types.items(), key=lambda x: x[1], reverse=True))}")
    
    # Test 6: Test multi-floor connectivity
    print("\n6. Testing multi-floor connectivity...")
    floors = set()
    for pos in dungeon.room_states.keys():
        floors.add(pos[2])
    
    print(f"   Total floors: {sorted(floors)}")
    
    # Check for stairs
    stairs_up = sum(1 for room in dungeon.room_states.values() if room.has_stairs_up)
    stairs_down = sum(1 for room in dungeon.room_states.values() if room.has_stairs_down)
    print(f"   Stairs up: {stairs_up}, Stairs down: {stairs_down}")
    
    print("\n✅ All comprehensive tests completed!")


if __name__ == "__main__":
    test_comprehensive_dungeon_system()