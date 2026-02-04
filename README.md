# Terminal Dungeon Crawler

A nethack-inspired terminal-based dungeon crawler game with persistent state between executions.

## 🎮 Features

### 🏰 Enhanced Room-Based Dungeon Generation
- **Authentic Room Layouts**: Instead of single-tile rooms, the dungeon now features actual rectangular room areas (4x4 to 8x8 tiles) connected by narrow hallways
- **Strategic Floor Layout**: Each floor has specific required rooms - Floor 1 has the starting room and stairs down, upper floors have stairs up and down with appropriate room distributions
- **Thematic Variety**: Different room types including starting rooms, treasure rooms, monster rooms, trap rooms, NPC rooms, and staircase rooms
- **Floor-Specific Requirements**: Floor-specific room placement ensuring proper dungeon flow (staircase up only on floors > 0, staircase down only on non-last floors)
- **Seed-Based Generation**: Deterministic dungeon generation based on a seed value for efficient saving
- **Strategic Connections**: Rooms are connected via L-shaped hallways creating authentic dungeon feel

### ⚔️ Advanced Gameplay Elements
- **NPC Quest System**: Interact with NPCs who offer quests for rewards
- **Status Effects**: Weapons can inflict status effects like burn, poison, chill, shock, and stun
- **Locked Doors & Blocked Passages**: Puzzle elements requiring specific keys or items to proceed
- **Detailed Statistics**: Track score, enemies defeated, treasures collected, floors explored, rooms explored, and distance traveled

### 📋 Batch Command Processing
- Execute multiple commands in sequence: `python src/batch_processor.py "move north" "look" "stats"`
- Perfect for automated sequences and scripted gameplay
- Comprehensive documentation in [BATCH_COMMANDS.md](BATCH_COMMANDS.md)

### 💾 Efficient Save System
- **Seed-Based Saves**: Only save items and changes during gameplay, reducing save file size
- **Persistent Progress**: All game state preserved between sessions
- **Auto-Save**: Automatic saving after each action

### 🖼️ Dungeon Visualization Tool
- Visualize dungeon layouts based on seed: `python src/dungeon_visualizer.py <seed>`
- See room types and connections clearly displayed
- Helpful for debugging and planning

### 📍 Local Map Feature
- Show 5x5 map around player: `local` or `lm` command
- Provides immediate spatial awareness
- Shows nearby room types and points of interest

### 🤖 Intelligent Enemy AI
- Selective movement reporting: Only see enemy movements when in player's line of sight
- Enemies patrol and hunt intelligently
- Line-of-sight detection for realistic AI behavior

### 🔧 External Data System
- **Separation of Content and Code**: Game data stored in JSON files in the `data/` directory
- **Easy Customization**: Modify items, enemies, rooms, and NPCs without changing code
- **Expandable Content**: Add new game elements by editing JSON files

### Classic RPG Elements
- Turn-based exploration of a multi-level dungeon
- Combat system with various enemies that increase in difficulty as you descend
- Equipment system with weapons and armor
- Inventory management
- Persistent state through save/load functionality
- Scoring system based on enemies defeated, treasures collected, exploration, and other metrics
- Ultimate goal: Find the Artifact of Power at the bottom of the dungeon to win the game
- Multiple branching pathways encourage exploration before reaching the final goal
- Initiative system based on speed stat to determine combat order
- Strategic combat with tactical depth

## 🚀 Usage

### Basic Gameplay
```bash
# Start a new game or continue from save
python src/seeded_game_engine.py

# Execute individual commands
python src/seeded_game_engine.py move north
python src/seeded_game_engine.py attack 1
python src/seeded_game_engine.py take 1
python src/seeded_game_engine.py stats
```

### Batch Commands
```bash
# Execute multiple commands in sequence
python src/batch_processor.py "move north" "look" "take 1" "stats"
```

### Visualize Dungeon
```bash
# Visualize dungeon layout for a specific seed
python src/dungeon_visualizer.py 12345
python src/dungeon_visualizer.py 12345 0  # Visualize only floor 0
```

### Available Commands
- `move <direction>` - Move north, south, east, west, up, or down
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
- `quit` - Quit the game

## 📁 Directory Structure
```
dungeon-game/
├── src/
│   ├── seeded_game_engine.py     # Main game engine with seed-based generation
│   ├── batch_processor.py        # Batch command execution
│   ├── dungeon_visualizer.py     # Dungeon visualization tool
│   └── data_loader.py           # External data loading system
├── data/
│   ├── items.json               # Game items definition
│   ├── enemies.json             # Enemy definitions
│   ├── npcs.json               # NPC definitions
│   └── rooms.json              # Room templates
├── demo_improvements.py         # Demo script for new features
└── BATCH_COMMANDS.md           # Batch command documentation
```

## 🎯 Game Elements

### Room Types
- **Starting Room**: Safe starting area with basic equipment
- **Treasure Room**: Contains valuable items and equipment
- **Monster Room**: Hostile creatures to battle
- **Trap Room**: Dangerous areas with hazards
- **NPC Room**: Characters offering quests and rewards
- **Staircase Room**: Connections between dungeon levels
- **Hallway**: Narrow corridors connecting rooms
- **Artifact Room**: Contains the ultimate artifact on the deepest floor

### Items & Equipment
- **Weapons**: Swords, bows, staves with attack bonuses and status effects
- **Armor**: Protection with defense bonuses and health boosts
- **Consumables**: Potions and healing items
- **Keys**: Required to unlock doors
- **Triggers**: Special items to clear blocked passages

### Status Effects
- **Burn**: Deals damage over time
- **Poison**: Gradually reduces health
- **Chill**: Slows enemies
- **Shock**: Stuns enemies temporarily
- **Stun**: Paralyzes enemies briefly

## 🧩 Extensibility

The game is designed for easy expansion:
- Add new items to `data/items.json`
- Create new enemies in `data/enemies.json`
- Design custom room templates in `data/rooms.json`
- Add NPCs with quests in `data/npcs.json`
- Extend gameplay mechanics in the engine classes