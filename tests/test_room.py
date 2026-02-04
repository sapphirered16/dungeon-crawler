"""Unit tests for room classes."""

import unittest
from src.classes.room import RoomState
from src.classes.item import Item
from src.classes.base import ItemType, Direction
from src.classes.character import Entity, NonPlayerCharacter


class TestRoomState(unittest.TestCase):
    def setUp(self):
        self.room = RoomState((10, 10, 0), "treasure")

    def test_room_initialization(self):
        """Test that room initializes correctly."""
        self.assertEqual(self.room.pos, (10, 10, 0))
        self.assertEqual(self.room.room_type, "treasure")
        self.assertEqual(self.room.items, [])
        self.assertEqual(self.room.entities, [])
        self.assertEqual(self.room.npcs, [])
        self.assertEqual(self.room.connections, {})
        self.assertFalse(self.room.has_stairs_up)
        self.assertFalse(self.room.has_stairs_down)
        self.assertIsNone(self.room.stairs_up_target)
        self.assertIsNone(self.room.stairs_down_target)
        self.assertEqual(self.room.locked_doors, {})
        self.assertEqual(self.room.blocked_passages, {})
        self.assertEqual(self.room.description, "An empty, quiet room.")
        self.assertEqual(self.room.theme, "generic")

    def test_add_item(self):
        """Test adding an item to the room."""
        item = Item("Test Item", ItemType.CONSUMABLE, 10)
        initial_count = len(self.room.items)
        
        self.room.add_item(item)
        
        self.assertEqual(len(self.room.items), initial_count + 1)
        self.assertIn(item, self.room.items)

    def test_add_entity(self):
        """Test adding an entity to the room."""
        entity = Entity("Test Entity", 50, 10, 5)
        initial_count = len(self.room.entities)
        
        self.room.add_entity(entity)
        
        self.assertEqual(len(self.room.entities), initial_count + 1)
        self.assertIn(entity, self.room.entities)

    def test_add_npc(self):
        """Test adding an NPC to the room."""
        npc = NonPlayerCharacter("Test NPC", 20, 5, 2)
        initial_entity_count = len(self.room.entities)
        initial_npc_count = len(self.room.npcs)
        
        self.room.add_npc(npc)
        
        self.assertEqual(len(self.room.entities), initial_entity_count + 1)
        self.assertEqual(len(self.room.npcs), initial_npc_count + 1)
        self.assertIn(npc, self.room.entities)
        self.assertIn(npc, self.room.npcs)

    def test_remove_entity(self):
        """Test removing an entity from the room."""
        entity = Entity("Test Entity", 50, 10, 5)
        self.room.add_entity(entity)
        
        initial_count = len(self.room.entities)
        self.room.remove_entity(entity)
        
        self.assertEqual(len(self.room.entities), initial_count - 1)
        self.assertNotIn(entity, self.room.entities)

    def test_get_living_entities(self):
        """Test getting living entities."""
        alive_entity = Entity("Alive Entity", 50, 10, 5)
        dead_entity = Entity("Dead Entity", 50, 10, 5)
        dead_entity.health = 0  # Kill the entity
        
        self.room.add_entity(alive_entity)
        self.room.add_entity(dead_entity)
        
        living_entities = self.room.get_living_entities()
        
        self.assertIn(alive_entity, living_entities)
        self.assertNotIn(dead_entity, living_entities)
        self.assertEqual(len(living_entities), 1)

    def test_connect_rooms(self):
        """Test connecting rooms."""
        # Manually set up connections
        self.room.connections[Direction.NORTH] = (10, 9, 0)
        self.room.connections[Direction.EAST] = (11, 10, 0)
        
        self.assertIn(Direction.NORTH, self.room.connections)
        self.assertIn(Direction.EAST, self.room.connections)
        self.assertEqual(self.room.connections[Direction.NORTH], (10, 9, 0))
        self.assertEqual(self.room.connections[Direction.EAST], (11, 10, 0))

    def test_locked_doors(self):
        """Test locked doors functionality."""
        self.room.locked_doors[Direction.WEST] = "Golden Key"
        
        self.assertIn(Direction.WEST, self.room.locked_doors)
        self.assertEqual(self.room.locked_doors[Direction.WEST], "Golden Key")

    def test_blocked_passages(self):
        """Test blocked passages functionality."""
        self.room.blocked_passages[Direction.SOUTH] = "Rune"
        
        self.assertIn(Direction.SOUTH, self.room.blocked_passages)
        self.assertEqual(self.room.blocked_passages[Direction.SOUTH], "Rune")

    def test_to_dict_and_from_dict(self):
        """Test serializing and deserializing room."""
        # Set up room with some state
        item = Item("Test Item", ItemType.CONSUMABLE, 10)
        entity = Entity("Test Entity", 50, 10, 5)
        entity.active_status_effects = {"burn": 2}
        npc = NonPlayerCharacter("Test NPC", 20, 5, 2)
        
        self.room.add_item(item)
        self.room.add_entity(entity)
        # Note: NPCs are also entities, so we don't add npc separately to entities
        
        self.room.connections[Direction.NORTH] = (10, 9, 0)
        self.room.has_stairs_up = True
        self.room.stairs_up_target = (10, 10, 1)
        self.room.locked_doors[Direction.WEST] = "Golden Key"
        self.room.blocked_passages[Direction.SOUTH] = "Rune"
        self.room.description = "A treasure room filled with gleaming objects."
        self.room.theme = "ancient"
        
        # Serialize and deserialize
        room_dict = self.room.to_dict()
        new_room = RoomState.from_dict(room_dict)
        
        # Check that properties are preserved
        self.assertEqual(new_room.pos, self.room.pos)
        self.assertEqual(new_room.room_type, self.room.room_type)
        self.assertEqual(len(new_room.items), len(self.room.items))
        self.assertEqual(new_room.items[0].name, "Test Item")
        self.assertEqual(len(new_room.entities), len(self.room.entities))
        self.assertEqual(new_room.entities[0].name, "Test Entity")
        self.assertEqual(new_room.entities[0].active_status_effects, {"burn": 2})
        self.assertEqual(len(new_room.connections), len(self.room.connections))
        self.assertIn(Direction.NORTH, new_room.connections)
        self.assertEqual(new_room.connections[Direction.NORTH], (10, 9, 0))
        self.assertTrue(new_room.has_stairs_up)
        self.assertEqual(new_room.stairs_up_target, (10, 10, 1))
        self.assertIn(Direction.WEST, new_room.locked_doors)
        self.assertEqual(new_room.locked_doors[Direction.WEST], "Golden Key")
        self.assertIn(Direction.SOUTH, new_room.blocked_passages)
        self.assertEqual(new_room.blocked_passages[Direction.SOUTH], "Rune")
        self.assertEqual(new_room.description, "A treasure room filled with gleaming objects.")
        self.assertEqual(new_room.theme, "ancient")

    def test_serialization_with_multiple_entities(self):
        """Test serialization with multiple entities."""
        # Add multiple entities to the room
        entity1 = Entity("Entity 1", 30, 8, 3)
        entity2 = Entity("Entity 2", 40, 12, 6)
        item1 = Item("Item 1", ItemType.WEAPON, 50)
        item2 = Item("Item 2", ItemType.ARMOR, 30)
        
        self.room.add_entity(entity1)
        self.room.add_entity(entity2)
        self.room.add_item(item1)
        self.room.add_item(item2)
        
        # Serialize and deserialize
        room_dict = self.room.to_dict()
        new_room = RoomState.from_dict(room_dict)
        
        # Check that all entities and items are preserved
        self.assertEqual(len(new_room.entities), 2)
        self.assertEqual(len(new_room.items), 2)
        entity_names = [e.name for e in new_room.entities]
        self.assertIn("Entity 1", entity_names)
        self.assertIn("Entity 2", entity_names)
        item_names = [i.name for i in new_room.items]
        self.assertIn("Item 1", item_names)
        self.assertIn("Item 2", item_names)


if __name__ == '__main__':
    unittest.main()