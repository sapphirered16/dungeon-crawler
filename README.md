# Terminal Dungeon Crawler

A nethack-inspired terminal-based dungeon crawler game with persistent state between executions.

## Features

- Turn-based exploration of a multi-level dungeon
- Combat system with various enemies that increase in difficulty as you descend
- Equipment system with weapons and armor
- Inventory management
- Persistent state through save/load functionality
- Scoring system based on enemies defeated, treasures collected, exploration, and other metrics
- Structured dungeon generation with rooms and hallways
- Ultimate goal: Find the Artifact of Power at the bottom of the dungeon to win the game
- Multiple branching pathways encourage exploration before reaching the final goal
- Special effects for weapons and armor (gruff weapons increase damage, shielding armor increases defense)
- Initiative system based on speed stat to determine combat order
- Strategic combat with tactical depth
- Locked doors and blocked passages that require special items to pass
- Item stacking for consumable items
- NPC quest system for additional challenges
- Themed dungeon environments (cavern, castle, forest, magical, etc.)
- Seed-based dungeon generation for efficient saves and deterministic behavior
- Visual dungeon mapping tool for debugging and analysis
- Improved dungeon generation with larger rooms connected by narrow hallways

## How to Play
- Run the game executable to start a new game
- Pass commands as arguments to perform actions (move, attack, use item, etc.)
- Explore the dungeon, defeat enemies, and find better equipment
- Descend through the floors to find the ultimate Artifact of Power

## Commands
- `move <direction>` - Move in a direction (north, south, east, west)
- `attack <enemy>` - Attack an enemy in the current room
- `take <item>` - Take an item from the current room
- `equip <item>` - Equip an item from your inventory
- `unequip <weapon|armor>` - Unequip weapon or armor
- `look` - Examine the current room
- `inventory` - View your inventory
- `stats` - View character stats
- `rest` - Rest to recover health
- `save` - Save the game
- `load` - Load a saved game

## Visualization Tool
A dungeon visualization tool is included to help debug and analyze dungeon layouts:

```bash
python src/dungeon_visualizer.py <seed> [floor]
```

Example: `python src/dungeon_visualizer.py 12345` to visualize all floors of dungeon with seed 12345
Example: `python src/dungeon_visualizer.py 12345 0` to visualize only floor 0 of dungeon with seed 12345