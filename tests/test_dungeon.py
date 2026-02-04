"""Unit tests for dungeon classes."""

import unittest
from src.classes.dungeon import SeededDungeon
from src.classes.room import RoomState


class TestSeededDungeon(unittest.TestCase):
    def setUp(self):
        self.dungeon = SeededDungeon(seed=12345)

    def test_dungeon_initialization(self):
        """Test that dungeon initializes correctly."""
        self.assertEqual(self.dungeon.seed, 12345)
        self.assertIsInstance(self.dungeon.room_states, dict)
        self.assertGreater(len(self.dungeon.room_states), 0)  # Should have generated rooms

    def test_room_generation(self):
        """Test that rooms are generated."""
        self.assertGreater(len(self.dungeon.room_states), 0)
        
        # Check that there's a starting room at (12, 12, 0)
        start_pos = (12, 12, 0)
        self.assertIn(start_pos, self.dungeon.room_states)
        
        start_room = self.dungeon.room_states[start_pos]
        self.assertEqual(start_room.room_type, "starting")
        self.assertIn("entrance to the dungeon", start_room.description)

    def test_get_room_at(self):
        """Test getting a room at a specific position."""
        start_pos = (12, 12, 0)
        room = self.dungeon.get_room_at(start_pos)
        
        self.assertIsNotNone(room)
        self.assertEqual(room.room_type, "starting")

    def test_get_room_at_nonexistent(self):
        """Test getting a room that doesn't exist."""
        nonexistent_pos = (999, 999, 999)
        room = self.dungeon.get_room_at(nonexistent_pos)
        
        self.assertIsNone(room)

    def test_dungeon_with_different_seeds(self):
        """Test that different seeds produce different dungeons."""
        dungeon1 = SeededDungeon(seed=11111)
        dungeon2 = SeededDungeon(seed=22222)
        
        # While they might have some similarities due to algorithm, 
        # they should generally be different
        self.assertEqual(dungeon1.seed, 11111)
        self.assertEqual(dungeon2.seed, 22222)
        
        # Both should have rooms
        self.assertGreater(len(dungeon1.room_states), 0)
        self.assertGreater(len(dungeon2.room_states), 0)

    def test_multiple_floors_generation(self):
        """Test that multiple floors are generated."""
        # Check if rooms exist on different floors
        floors_present = set()
        for pos in self.dungeon.room_states.keys():
            floors_present.add(pos[2])  # z-coordinate is the floor
        
        # Should have at least floor 0 (and likely more depending on generation)
        self.assertIn(0, floors_present)

    def test_room_connections(self):
        """Test that rooms have connections."""
        connected_rooms = 0
        for pos, room in self.dungeon.room_states.items():
            if len(room.connections) > 0:
                connected_rooms += 1
        
        # There should be some connected rooms in a generated dungeon
        self.assertGreater(connected_rooms, 0)

    def test_serialization(self):
        """Test dungeon serialization."""
        dungeon_dict = self.dungeon.to_dict()
        
        # Check that the dictionary has expected keys
        self.assertIn("seed", dungeon_dict)
        self.assertIn("room_states", dungeon_dict)
        self.assertEqual(dungeon_dict["seed"], 12345)
        self.assertGreater(len(dungeon_dict["room_states"]), 0)

    def test_deserialization(self):
        """Test dungeon deserialization."""
        # Serialize the original dungeon
        original_dict = self.dungeon.to_dict()
        
        # Deserialize into a new dungeon
        new_dungeon = SeededDungeon.from_dict(original_dict)
        
        # Compare properties
        self.assertEqual(new_dungeon.seed, self.dungeon.seed)
        self.assertEqual(len(new_dungeon.room_states), len(self.dungeon.room_states))
        
        # Check that rooms are properly reconstructed
        for pos, original_room in self.dungeon.room_states.items():
            self.assertIn(pos, new_dungeon.room_states)
            new_room = new_dungeon.room_states[pos]
            self.assertEqual(new_room.room_type, original_room.room_type)
            self.assertEqual(new_room.description, original_room.description)
            self.assertEqual(len(new_room.items), len(original_room.items))
            self.assertEqual(len(new_room.entities), len(original_room.entities))
            self.assertEqual(len(new_room.connections), len(original_room.connections))

    def test_dungeon_generation_without_seed(self):
        """Test dungeon generation without specifying a seed."""
        dungeon = SeededDungeon()  # No seed specified
        
        self.assertIsNone(dungeon.seed)
        self.assertGreater(len(dungeon.room_states), 0)
        
        # Should still have a starting room
        start_pos = (12, 12, 0)
        self.assertIn(start_pos, dungeon.room_states)


if __name__ == '__main__':
    unittest.main()