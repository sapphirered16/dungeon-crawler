# Source Code Structure

The main source files for the dungeon crawler game.

## Core Modules

### main.py
Primary entry point for interactive gameplay. Handles game initialization and main loop. Now supports single command execution via command-line arguments.

### new_game_engine.py
Core game logic, player management, room states, and dungeon mechanics. Implements the new room-based layout system with proper room dimensions.

### command_processor.py
Processes player commands and interfaces with the game engine.

### data/
- `data_loader.py` - Manages loading game data from external JSON files
- `items.json` - Game items definition
- `enemies.json` - Enemy definitions  
- `npcs.json` - NPC definitions
- `rooms.json` - Room templates

### classes/
- `new_dungeon.py` - New dungeon system with proper room dimensions
- `base.py` - Base classes and enums
- `character.py` - Player and enemy character classes
- `item.py` - Item class and definitions
- `room.py` - Room class with dimensions
- `enemy.py` - Enemy AI and behavior
- `map_effects.py` - Environmental hazards and effects

### dungeon_visualizer.py
Provides visualization tools for dungeon layouts based on seeds.

## Entry Points

### Interactive Play
- `python -m src.main` - Start interactive game session
- `./play.sh` - Alternative interactive play script

### Single Command Execution
- `python -m src.main <command>` - Execute single command
- `./play.sh <command>` - Execute single command via script