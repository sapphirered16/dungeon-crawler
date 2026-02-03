# Playing the Terminal Dungeon Crawler

## Starting the Game
To start a new game, simply run:
```
./play.sh
```

## Game Commands
Once in the game, you can enter the following commands:

### Movement
- `move north` - Move north
- `move south` - Move south
- `move east` - Move east
- `move west` - Move west

You can also use just the direction: `north`, `south`, `east`, `west`.

### Combat
- `attack <number>` - Attack an enemy by number (they appear numbered in the room)

### Items
- `take <number>` - Take an item by number from the current room
- `equip <number>` - Equip an item from your inventory

### Information
- `look` - Look around the current room
- `inventory` - View your inventory
- `stats` - View your character stats

### Survival
- `rest` - Rest to recover health

### Game Management
- `save` - Save your current game
- `load` - Load a saved game
- `help` - Show the help menu
- `quit` or `exit` - Exit the game

## Game Elements

### Character Stats
- **Level**: Your character's level, increases with experience
- **HP**: Your health points; if this reaches 0, you die
- **Attack**: Your offensive capability
- **Defense**: Reduces damage taken from enemies
- **EXP**: Experience points needed to level up
- **Gold**: Currency collected from defeated enemies
- **Score**: Points accumulated through various activities
- **Enemies Defeated**: Total number of enemies you've defeated
- **Treasures Collected**: Total number of treasures you've collected
- **Floors Explored**: Number of unique dungeon floors you've visited
- **Rooms Explored**: Number of unique rooms you've entered
- **Distance Traveled**: Total number of moves you've made

### Equipment
- **Weapons**: Increase your attack power
- **Armor**: Increase your defense and sometimes health
- **Consumables**: Items that provide temporary benefits

### Enemies
Different enemies have different stats and drop different rewards when defeated.

## Objective
Explore the dungeon, defeat enemies, collect better equipment, and venture deeper into the dungeon to face greater challenges and richer rewards.