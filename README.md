# Terminal Dungeon Crawler

A nethack-inspired terminal-based dungeon crawler game with persistent state between executions.

## 🎮 Features

### 🏰 Enhanced Room-Based Dungeon Generation
- **Authentic Room Layouts**: Instead of single-tile rooms, the dungeon now features actual rectangular room areas (2x2 to 8x8 tiles) connected by narrow hallways
- **Strategic Floor Layout**: Each floor has specific required rooms - Floor 1 has the starting room and stairs down, upper floors have stairs up and down with appropriate room distributions
- **Thematic Variety**: Different room types including starting rooms, treasure rooms, monster rooms, NPC rooms, and staircase rooms
- **Floor-Specific Requirements**: Floor-specific room placement ensuring proper dungeon flow (staircase up only on floors > 0, staircase down only on non-last floors)
- **Seed-Based Generation**: Deterministic dungeon generation based on a seed value for efficient saving
- **Strategic Connections**: Rooms are connected via L-shaped hallways creating authentic dungeon feel
- **Proper Room Dimensions**: Rooms now have actual dimensions (e.g., a library might be 3x5 tiles) instead of single tiles
- **Spaced Room Placement**: Rooms are placed with minimum spacing between them on a large grid (25x25)
- **Hallway Connections**: Rooms connect via hallways rather than directly touching, creating authentic dungeon feel

### ⚡ Map Effects System
- **Hidden Traps**: Environmental hazards that trigger when stepped on, causing damage
- **Wet Areas**: Environmental features that provide flavor text
- **Poisonous Areas**: Hazardous zones that cause damage and status effects
- **Icy Surfaces**: Areas that affect movement and speed
- **Dark Corners**: Environmental features affecting visibility
- **Slippery Floors**: Areas that cause movement issues
- **Loud Floors**: Areas that alert nearby creatures
- **Magnetic Fields**: Areas that affect metal objects
- **Scattered Throughout Floors**: Approximately 1 effect per 5 rooms
- **Not Visible on Main Map**: Preserves navigational clarity while adding environmental hazards
- **Environmental Descriptions**: Effects appear in room descriptions when present
- **Triggerable Effects**: Some effects activate when player steps on affected tiles

### ⚔️ Advanced Gameplay Elements
- **NPC Quest System**: Interact with NPCs who offer quests for rewards
- **Status Effects**: Weapons can inflict status effects like burn, poison, chill, shock, and stun
- **Locked Doors & Blocked Passages**: Puzzle elements requiring specific keys or items to proceed
- **Map Effects System**: Environmental hazards like traps, wet areas, poisonous zones, etc. scattered throughout dungeon floors that trigger when stepped on
- **Environmental Features**: Various environmental effects that appear in room descriptions
- **Detailed Statistics**: Track score, enemies defeated, treasures collected, floors explored, rooms explored, and distance traveled

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

### 🗺️ Item Location Indicators
- **Item Map Command**: Use `items` or `item` command to highlight locations with items
- **Visual Indicators**: '*' symbols on maps show rooms containing items
- **Enhanced Navigation**: Makes it easier to find backtracked items
- **Both Maps Supported**: Works on both full floor maps and local 5x5 maps

### 🪜 Stairs Location Command
- **Stairs Map Command**: Use `stairs`, `staircase`, or `levels` command to show locations of stairs on current floor
- **Distance Indicators**: Shows how close player is to nearby stairs
- **Enhanced Navigation**: Makes it easier to find staircases to progress through dungeon levels

### 🎨 Extended ASCII Map Characters
- **Enhanced Visual Appeal**: Replaced simple ASCII characters with distinctive Unicode symbols
- **Better Readability**: Uses symbols like □ (empty room), ■ (room with items), ∿ (hallway), ≈ (hallway with items), ♀ (player), ░ (unknown area), · (explored empty space)
- **Improved Map Clarity**: Each map element now has a visually distinct representation

### 🤖 Intelligent Enemy AI
- Selective movement reporting: Only see enemy movements when in player's line of sight
- Enemies patrol and hunt intelligently
- Line-of-sight detection for realistic AI behavior

### 🧭 Logical Progression System
- **Required Items Before Obstacles**: The dungeon generation ensures that required items appear before obstacles that need them
- **Solvable Puzzles**: Prevents unsolvable loops by placing keys and trigger items in earlier positions than locked doors and blocked passages
- **Strategic Exploration**: Players must explore strategically to find required items before encountering obstacles

### 🔧 External Data System
- **Separation of Content and Code**: Game data stored in JSON files in the `data/` directory
- **Easy Customization**: Modify items, enemies, rooms, and NPCs without changing code
- **Expandable Content**: Add new game elements by editing JSON files

### 📝 Single Command Execution
- **New Execution Method**: Run single commands with `python -m src.main <command>`
- **Script Integration**: Use `./play.sh <command>` for quick command execution
- **Example**: `./play.sh stats` or `./play.sh 12345 map`

### 📁 Logging System
- **Single Log File**: Uses `dungeon_log.txt` for all game events
- **Cleared on New Game**: Log file is cleared when a new game starts
- **Action Tracking**: All player actions are logged with timestamps and positions

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

### Interactive Gameplay (Recommended)
```bash
# Start a new game with interactive mode
python -m src.main

# Or use the play script
./play.sh

# Start with a specific seed
./play.sh 12345
```

### Single Command Execution
```bash
# Execute individual commands
python -m src.main stats
python -m src.main map
python -m src.main items
python -m src.main stairs
python -m src.main look
python -m src.main --seed 12345 stats
```

### Script Usage
```bash
# Execute single commands with the play script
./play.sh stats
./play.sh 12345 map
./play.sh items
./play.sh stairs
```

### Visualize Dungeon
```bash
# Visualize dungeon layout for a specific seed
python src/dungeon_visualizer.py 12345
python src/dungeon_visualizer.py 12345 0  # Visualize only floor 0
```

### Available Commands
- `stats` - View your character stats
- `look` - Look around the current room and show local map
- `map` - Show current floor map
- `items` or `item` - Show map with item location indicators
- `stairs`, `staircase`, or `levels` - Show locations of stairs on current floor
- `local` or `lm` - Show 5x5 local map around player
- `inventory` or `i` - View your inventory
- `go <direction>` or `move <direction>` - Move north, south, east, west, up, or down
- `attack <number>` - Attack enemy number in room
- `take <number>` - Take item number from room
- `equip <number>` - Equip item number from inventory
- `use <number>` - Use consumable item number from inventory
- `talk <number>` - Talk to NPC number in room
- `save` - Save the game
- `load` - Load a saved game
- `log` or `history` - View game log history
- `clear` - Clear save and log files
- `quit`, `q`, or `exit` - Quit the game
- `help`, `h`, or `?` - Show available commands and tips

## 📁 Directory Structure
```
dungeon-game/
├── src/
│   ├── main.py                 # Main entry point with single command support
│   ├── new_game_engine.py      # Main game engine with proper room-based layouts
│   ├── command_processor.py    # Command processing system
│   ├── dungeon_visualizer.py   # Dungeon visualization tool
│   └── data/
│       ├── data_loader.py      # External data loading system
│       ├── items.json          # Game items definition
│       ├── enemies.json        # Enemy definitions
│       ├── npcs.json           # NPC definitions
│       └── rooms.json          # Room templates
├── src/classes/
│   ├── new_dungeon.py          # New dungeon system with proper room dimensions
│   ├── base.py                 # Base classes and enums
│   ├── character.py            # Player and enemy character classes
│   ├── item.py                 # Item class and definitions
│   ├── room.py                 # Room class with dimensions
│   ├── enemy.py                # Enemy AI and behavior
│   ├── map_effects.py          # Environmental hazards and effects
│   └── ...
└── play.sh                     # Main play script with single command support
```

## 🎯 Game Elements

### Room Types
- **Starting Room**: Safe starting area with basic equipment
- **Treasure Room**: Contains valuable items and equipment
- **Monster Room**: Hostile creatures to battle
- **NPC Room**: Characters offering quests and rewards
- **Staircase Room**: Connections between dungeon levels
- **Hallway**: Narrow corridors connecting rooms
- **Artifact Room**: Contains the ultimate artifact on the deepest floor

### Items & Equipment
- **Weapons**: Swords, bows, staves with attack bonuses and status effects
- **Armor**: Protection with defense bonuses and health boosts
- **Consumables**: Potions and healing items with temporary buffs
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