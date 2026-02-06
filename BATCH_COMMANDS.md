# Batch Command Processing

The dungeon crawler supports batch command processing for automated testing, allowing you to execute multiple commands in sequence.

**IMPORTANT**: Batch processing is intended for **testing and automation purposes only**. For actual gameplay, use the interactive mode:

```bash
# Recommended for gameplay
python -m src.main
# or
./play.sh
```

The batch processor does not maintain proper game state continuity and can cause unexpected behavior during actual gameplay.

## Usage

### Running Batch Commands (Testing Only)
```bash
python src/batch_processor.py "command1" "command2" "command3" ...
```

### Examples
```bash
# Automated testing
python src/batch_processor.py "move north" "move east" "look" "stats"

# Combat sequence testing
python src/batch_processor.py "move north" "attack 1" "take 1" "equip 1" "stats"

# Exploration testing
python src/batch_processor.py "move north" "move north" "move east" "move south" "look" "inventory"
```

## Supported Commands

- `move <direction>` - Move in a direction (north, south, east, west, up, down)
- `attack <number>` - Attack enemy number in room
- `take <number>` - Take item number from room
- `equip <number>` - Equip item number from inventory
- `use <number>` - Use consumable item number from inventory
- `talk <number>` - Talk to NPC number in room
- `look` - Look around the current room
- `inventory` or `i` - View your inventory
- `stats` - View your character stats
- `save` - Save the game
- `load` - Load a saved game

## Benefits

- **Automated Testing**: Test game mechanics with predefined command sequences
- **Debugging**: Quickly execute command sequences for development
- **Integration**: Easily integrate with other tools or scripts for testing

## Notes

- Commands are executed in sequence with minimal delay between them
- The game state is automatically saved after batch execution
- Invalid commands are reported but don't halt execution of remaining commands
- Use quotes around commands that contain spaces
- **Not recommended for actual gameplay** - use interactive mode instead