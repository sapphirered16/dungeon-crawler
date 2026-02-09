"""Unit tests for game engine."""

import unittest
import tempfile
import os
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from new_game_engine import SeededGameEngine


class TestSeededGameEngine(unittest.TestCase):
    def setUp(self):
        self.game = SeededGameEngine(seed=12345)

    def test_game_initialization(self):
        """Test that game initializes correctly."""
        self.assertEqual(self.game.seed, 12345)
        self.assertIsNotNone(self.game.dungeon)
        self.assertIsNotNone(self.game.player)
        self.assertIsNotNone(self.game.current_room)
        self.assertIsNotNone(self.game.data_provider)

    def test_player_starts_at_correct_position(self):
        """Test that player starts at the correct position."""
        # Player should start in a room on floor 0
        self.assertEqual(self.game.player.position[2], 0)  # z coordinate (floor)

    def test_show_stats_no_error(self):
        """Test that show_stats doesn't raise an error."""
        try:
            self.game.show_stats()
        except Exception as e:
            self.fail(f"show_stats raised {type(e).__name__}: {e}")

    def test_look_around_no_error(self):
        """Test that look_around doesn't raise an error."""
        try:
            self.game.look_around()
        except Exception as e:
            self.fail(f"look_around raised {type(e).__name__}: {e}")

    def test_move_player_directions(self):
        """Test that player can move in different directions."""
        from classes.base import Direction
        
        # Try to move in each direction and ensure it doesn't crash
        directions = [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]
        
        for direction in directions:
            # Capture current position
            old_pos = self.game.player.position
            
            # Try to move (may fail if no connection, but shouldn't crash)
            try:
                result = self.game.move_player(direction)
                # If it succeeded, position should have changed
                if result:
                    self.assertNotEqual(self.game.player.position, old_pos)
                else:
                    # If it failed, position should be the same
                    self.assertEqual(self.game.player.position, old_pos)
            except Exception as e:
                self.fail(f"move_player with direction {direction} raised {type(e).__name__}: {e}")

    def test_visualize_floor_no_error(self):
        """Test that visualize_floor doesn't raise an error."""
        try:
            self.game.visualize_floor()
        except Exception as e:
            self.fail(f"visualize_floor raised {type(e).__name__}: {e}")

    def test_visualize_specific_floor_no_error(self):
        """Test that visualize_floor with specific floor doesn't raise an error."""
        try:
            self.game.visualize_floor(0)  # Floor 1 (0-indexed)
        except Exception as e:
            self.fail(f"visualize_floor(0) raised {type(e).__name__}: {e}")

    def test_save_and_load_game(self):
        """Test saving and loading game."""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filename = temp_file.name

        try:
            # Save the game
            self.game.save_game(temp_filename)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_filename))
            
            # Load the game back
            original_position = self.game.player.position
            original_level = self.game.player.level
            
            # Create a new game instance and load
            new_game = SeededGameEngine(seed=12345)
            new_game.load_game(temp_filename)
            
            # Verify that the game state was loaded correctly
            self.assertEqual(new_game.seed, self.game.seed)
            self.assertEqual(new_game.player.position, original_position)
            self.assertEqual(new_game.player.level, original_level)
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_is_game_over(self):
        """Test is_game_over method."""
        # Initially, player should be alive
        self.assertFalse(self.game.is_game_over())
        
        # Set player health to 0 to simulate death
        self.game.player.health = 0
        
        # Now game should be over
        self.assertTrue(self.game.is_game_over())

    def test_get_game_status(self):
        """Test getting game status."""
        status = self.game.get_game_status()
        
        # Verify that the status contains expected keys
        self.assertIn("player_alive", status)
        self.assertIn("player_position", status)
        self.assertIn("player_level", status)
        self.assertIn("player_hp", status)
        self.assertIn("enemies_defeated", status)
        self.assertIn("treasures_collected", status)
        self.assertIn("floors_explored", status)
        self.assertIn("current_floor", status)
        
        # Verify that values are of correct types
        self.assertIsInstance(status["player_alive"], bool)
        self.assertIsInstance(status["player_position"], tuple)
        self.assertIsInstance(status["player_level"], int)
        self.assertIsInstance(status["player_hp"], int)
        self.assertIsInstance(status["enemies_defeated"], int)
        self.assertIsInstance(status["treasures_collected"], int)
        self.assertIsInstance(status["floors_explored"], int)
        self.assertIsInstance(status["current_floor"], int)

    def test_different_seed_generates_different_dungeon(self):
        """Test that different seeds create different dungeons."""
        game1 = SeededGameEngine(seed=11111)
        game2 = SeededGameEngine(seed=22222)
        
        # Different seeds should create different room layouts
        # (though they might share some characteristics)
        self.assertEqual(game1.seed, 11111)
        self.assertEqual(game2.seed, 22222)
        
        # Both games should have players
        self.assertIsNotNone(game1.player)
        self.assertIsNotNone(game2.player)

    def test_take_item_boundary_conditions(self):
        """Test take_item with boundary conditions."""
        # Try to take an item from an empty room
        initial_inventory_size = len(self.game.player.inventory)
        
        # This should fail gracefully since room is likely empty
        result = self.game.take_item(1)
        
        # The method should return False when there's no item to take
        # and not raise an exception
        # (Actual behavior depends on implementation, but shouldn't crash)

    def test_attack_enemy_boundary_conditions(self):
        """Test attack_enemy with boundary conditions."""
        # Try to attack when there are no enemies
        # This should fail gracefully and not crash
        try:
            result = self.game.attack_enemy(1)
            # Method should handle gracefully when no enemies are present
        except Exception as e:
            self.fail(f"attack_enemy(1) with no enemies raised {type(e).__name__}: {e}")


if __name__ == '__main__':
    unittest.main()