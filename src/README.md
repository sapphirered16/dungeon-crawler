# Source Code Structure

The main source files for the dungeon crawler game.

## Core Modules

### main.py
Primary entry point for interactive gameplay. Handles game initialization and main loop.

### game_engine.py
Core game logic, player management, room states, and dungeon mechanics.

### command_processor.py
Processes player commands and interfaces with the game engine.

### data_loader.py
Manages loading game data from external JSON files.

### dungeon_visualizer.py
Provides visualization tools for dungeon layouts based on seeds.

### batch_processor.py
Handles batch command execution for automated sequences (for testing/debugging).

## Entry Points

### Interactive Play
- `python -m src.main` - Start interactive game session
- `./play.sh` - Alternative interactive play script

### Batch Processing
- `python src/batch_processor.py` - Execute multiple commands (testing only)