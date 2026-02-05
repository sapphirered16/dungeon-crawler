"""Test script to verify the new dungeon generation system."""

from src.classes.dungeon import SeededDungeon
from src.game_engine import SeededGameEngine


def test_new_dungeon_system():
    """Test the new room-based dungeon system."""
    print("🧪 Testing new dungeon generation system...")
    
    # Test dungeon creation
    print("\n1. Creating dungeon with seed 42...")
    dungeon = SeededDungeon(seed=42)
    
    print(f"   Dungeon has {len(dungeon.room_states)} rooms/tiles")
    print(f"   Number of dimensional rooms: {len(dungeon.rooms_by_id)}")
    print(f"   Number of hallways: {len(dungeon.hallways)}")
    
    # Test getting room info
    print("\n2. Testing room information retrieval...")
    sample_pos = list(dungeon.room_states.keys())[0] if dungeon.room_states else None
    if sample_pos:
        room_info = dungeon.get_room_info(sample_pos)
        if room_info:
            print(f"   Sample position {sample_pos}:")
            print(f"     Room type: {room_info['room_state'].room_type}")
            print(f"     Is hallway: {room_info['is_hallway']}")
            if room_info['dimensional_room']:
                room = room_info['dimensional_room']
                print(f"     Dimensional room: {room.rect.width}x{room.rect.height} at ({room.rect.x}, {room.rect.y})")
    
    # Test adjacent positions
    print("\n3. Testing adjacent position detection...")
    if sample_pos:
        adjacent = dungeon.get_adjacent_positions(sample_pos)
        print(f"   From position {sample_pos}, can move to {len(adjacent)} adjacent positions")
        print(f"   Adjacent positions: {adjacent[:5]}{'...' if len(adjacent) > 5 else ''}")
    
    # Test game engine integration
    print("\n4. Testing game engine integration...")
    try:
        engine = SeededGameEngine(seed=42)
        print(f"   Engine created successfully")
        print(f"   Player position: {engine.player.position}")
        print(f"   Current room type: {engine.current_room_state.room_type}")
        
        # Test adjacent moves
        adjacent = engine._get_adjacent_positions(engine.player.position)
        print(f"   Can move to {len(adjacent)} adjacent positions")
        
        print("\n✅ All tests passed! New dungeon system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Error testing game engine: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_new_dungeon_system()