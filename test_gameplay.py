"""Quick test to verify the game still works normally."""

from src.game_engine import SeededGameEngine


def test_gameplay():
    """Test normal gameplay with the new dungeon system."""
    print("🎮 Testing normal gameplay...")
    
    # Create a game engine
    engine = SeededGameEngine(seed=12345)
    
    print(f"Starting position: {engine.player.position}")
    print(f"Current room: {engine.current_room_state.room_type}")
    
    # Show initial stats
    engine.show_stats()
    
    # Look around
    engine.look_around()
    
    # Try some movements
    print("\n--- Moving around ---")
    from src.classes.base import Direction
    
    # Move in a few directions to explore
    engine.move_player(Direction.EAST)
    engine.move_player(Direction.SOUTH)
    engine.move_player(Direction.WEST)
    engine.move_player(Direction.NORTH)
    
    # Show stats again
    print("\n--- Final stats ---")
    engine.show_stats()
    
    print("\n✅ Gameplay test completed successfully!")


if __name__ == "__main__":
    test_gameplay()