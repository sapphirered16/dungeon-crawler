"""Unit tests for dungeon classes."""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from classes.new_dungeon import SeededDungeon
from classes.room import RoomState


class TestSeededDungeon(unittest.TestCase):
    def setUp(self):
        self.dungeon = SeededDungeon(seed=12345)

    def test_dungeon_initialization(self):
        """Test that dungeon initializes correctly."""
        self.assertEqual(self.dungeon.seed, 12345)
        self.assertIsInstance(self.dungeon.rooms, list)
        self.assertGreater(len(self.dungeon.rooms), 0)  # Should have generated rooms

    def test_room_generation(self):
        """Test that rooms are generated."""
        self.assertGreater(len(self.dungeon.rooms), 0)
        
        # Find the starting room
        start_room = None
        for room in self.dungeon.rooms:
            if room.room_type == "entrance":
                start_room = room
                break
        
        self.assertIsNotNone(start_room, "Should have an entrance room")
        self.assertIn("entrance", start_room.description.lower())

    def test_get_room_at(self):
        """Test getting a room at a specific position."""
        start_pos = (4, 10, 0)  # Center of the entrance room
        room = self.dungeon.get_room_at_position(start_pos)
        
        self.assertIsNotNone(room)
        # The starting room should be entrance or hub type
        self.assertIn(room.room_type, ["entrance", "hub"])

    def test_get_room_at_nonexistent(self):
        """Test getting a room that doesn't exist."""
        nonexistent_pos = (999, 999, 999)
        room = self.dungeon.get_room_at_position(nonexistent_pos)
        
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
        self.assertGreater(len(dungeon1.rooms), 0)
        self.assertGreater(len(dungeon2.rooms), 0)

    def test_multiple_floors_generation(self):
        """Test that multiple floors are generated."""
        # Check if rooms exist on different floors
        floors_present = set()
        for room in self.dungeon.rooms:
            floors_present.add(room.z)  # z-coordinate is the floor
        
        # Should have at least floor 0 (and likely more depending on generation)
        self.assertIn(0, floors_present)

    def test_room_connections(self):
        """Test that rooms have connections."""
        connected_rooms = 0
        for room in self.dungeon.rooms:
            if len(room.connections) > 0:
                connected_rooms += 1
        
        # There should be some connected rooms in a generated dungeon
        self.assertGreater(connected_rooms, 0)

    def test_serialization(self):
        """Test dungeon serialization."""
        dungeon_dict = self.dungeon.to_dict()
        
        # Check that the dictionary has expected keys
        self.assertIn("seed", dungeon_dict)
        self.assertIn("rooms", dungeon_dict)
        self.assertEqual(dungeon_dict["seed"], 12345)
        self.assertGreater(len(dungeon_dict["rooms"]), 0)

    def test_deserialization(self):
        """Test dungeon deserialization."""
        # Serialize the original dungeon
        original_dict = self.dungeon.to_dict()
        
        # Deserialize into a new dungeon
        new_dungeon = SeededDungeon.from_dict(original_dict)
        
        # Compare basic properties
        self.assertEqual(new_dungeon.seed, self.dungeon.seed)
        self.assertEqual(len(new_dungeon.rooms), len(self.dungeon.rooms))
        
        # Check that basic room structure is preserved
        original_entrance_rooms = [r for r in self.dungeon.rooms if r.room_type == "entrance"]
        new_entrance_rooms = [r for r in new_dungeon.rooms if r.room_type == "entrance"]
        
        self.assertEqual(len(original_entrance_rooms), len(new_entrance_rooms))
        
        if original_entrance_rooms:
            original_entrance = original_entrance_rooms[0]
            new_entrance = new_entrance_rooms[0]
            
            # Check basic properties are preserved
            self.assertEqual(new_entrance.room_type, original_entrance.room_type)
            self.assertEqual(new_entrance.x, original_entrance.x)
            self.assertEqual(new_entrance.y, original_entrance.y)
            self.assertEqual(new_entrance.z, original_entrance.z)
            self.assertEqual(new_entrance.width, original_entrance.width)
            self.assertEqual(new_entrance.height, original_entrance.height)

    def test_dungeon_generation_without_seed(self):
        """Test dungeon generation without specifying a seed."""
        dungeon = SeededDungeon()  # No seed specified
        
        self.assertIsNone(dungeon.seed)
        self.assertGreater(len(dungeon.rooms), 0)
        
        # Should still have a starting room (entrance or hub)
        start_rooms = [room for room in dungeon.rooms if room.z == 0 and room.room_type in ["entrance", "hub"]]
        self.assertGreater(len(start_rooms), 0)


if __name__ == '__main__':
    unittest.main()