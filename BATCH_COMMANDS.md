# Batch Command Processing

The dungeon crawler now supports batch command processing, allowing you to execute multiple commands in sequence.

## Usage

### Running Batch Commands
```bash
python src/batch_processor.py "command1" "command2" "command3" ...
```

### Examples
```bash
# Navigate and explore
python src/batch_processor.py "move north" "move east" "look" "stats"

# Combat sequence
python src/batch_processor.py "move north" "attack 1" "take 1" "equip 1" "stats"

# Exploration and mapping
python src/batch_processor.py "move north" "move north" "move east" "move south" "look" "inventory"
```

## Supported Commands

- `move <direction>` - Move in a direction (north, south, east, west, up, down)
- `attack <number>` - Attack enemy number in room
- `take <number>` - Take item number from room
- `equip <number>` - Equip item number from inventory
- `unequip <weapon|armor>` - Unequip weapon or armor
- `talk <number>` - Talk to NPC number in room
- `look` - Look around the current room
- `inventory` - View your inventory
- `stats` - View your character stats
- `rest` - Rest to recover health
- `save` - Save the game
- `load` - Load a saved game

## Benefits

- **Automated Testing**: Test game mechanics with predefined command sequences
- **Scripted Gameplay**: Create custom adventure sequences
- **Exploration Assistance**: Automate routine navigation tasks
- **Integration**: Easily integrate with other tools or scripts

## Notes

- Commands are executed in sequence with minimal delay between them
- The game state is automatically saved after batch execution
- Invalid commands are reported but don't halt execution of remaining commands
- Use quotes around commands that contain spaces