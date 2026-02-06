# Game Design Document - Terminal Dungeon Crawler

## Overview
Terminal Dungeon Crawler is a nethack-inspired game that runs in the terminal. The game features turn-based exploration of a dungeon with combat, equipment, and progression systems. The ultimate goal is to find the Artifact of Power located at the bottom of the dungeon.

## Core Mechanics

### Movement
- Player can move in six directions: north, south, east, west, up, down
- Each movement is a discrete action
- The game maintains a coordinate system for the dungeon across multiple floors
- Stairs connect floors and allow vertical movement
- Structured dungeon layout with dimensional rooms and hallways instead of single tiles
- Tile-by-tile movement through hallways for authentic exploration
- Movement validated against grid-based obstacles (locked doors, blocked passages)

### Combat
- Turn-based combat system
- Initiative system based on speed stat determines combat order
- If player has higher speed than enemy, player attacks first
- If enemy has higher speed, enemy attacks first
- If speeds are equal, combat order is randomized
- Damage calculated as attacker's attack minus defender's defense (minimum 1 damage)
- Player and enemies have health points
- Experience and leveling system
- Enemies become significantly stronger on deeper floors
- Special effects: Gruff weapons increase damage, Shielding armor increases defense
- Turbo weapons and Light armor increase initiative/speed
- Enemy AI that patrols and hunts player when in line of sight

### Equipment
- Weapon and armor systems
- Equipment provides attack and defense bonuses
- Player can equip items from inventory
- Consumable items provide temporary stat buffs
- Special items: keys for locked doors and triggers for blocked passages
- Special effects: Gruff weapons increase damage, Shielding armor increases defense
- Speed-enhancing items: Turbo weapons and Light armor increase initiative/speed
- Item stacking for consumable items (KEY, TRIGGER, CONSUMABLE)

### Progression
- Multiple dungeon floors (5 floors total)
- Stairs connect floors and enable vertical movement
- Increasing difficulty as player descends
- Character advancement through experience
- Treasure collection
- Branching pathways encourage exploration on each floor
- Ultimate goal: Obtain the Artifact of Power from the deepest floor
- Logical progression: Required items placed before obstacles that need them
- Solvable puzzles: Prevents unsolvable loops by placing keys and triggers before locked doors/blocked passages

### Scoring
- Points awarded for defeating enemies
- Points for collecting treasure
- Exploration bonuses for discovering new rooms and floors
- Distance traveled bonuses
- Major bonus for finding the Artifact of Power (win condition)

### Dungeon Generation
- Structured layout with rectangular rooms of varying sizes (2x2 to 8x8 tiles)
- Hallways connecting rooms using L-shaped corridors
- Grid-based layout with proper spacing between rooms
- Locked doors requiring specific keys to open
- Blocked passages requiring trigger items to activate
- Each floor has multiple branching pathways
- Ultimate Artifact of Power placed on the deepest floor
- Enemies generated with speed stats that scale with dungeon depth
- Special effect items (Gruff weapons, Shielding armor, Turbo items, etc.) scattered throughout dungeon
- Map effects system: Environmental hazards like traps, wet areas, poisonous zones scattered throughout floors
- Items and obstacles placed on specific grid cells rather than entire rooms
- Logical progression system: Required items placed before obstacles that need them

### Environmental Hazards
- Hidden traps that trigger when stepped on, causing damage
- Wet areas that provide flavor text
- Poisonous zones that cause damage and status effects
- Icy surfaces that affect movement and speed
- Dark corners that affect visibility
- Slippery floors that cause movement issues
- Loud floors that alert nearby creatures
- Magnetic fields that affect metal objects
- Effects scattered throughout floors (approximately 1 per 5 rooms)
- Not visible on main map to preserve navigational clarity

## Technical Implementation

### Game State
- Saved in JSON format
- Tracks player position, stats, inventory, dungeon layout
- Persistent between game sessions

### Command Interface
- Interactive mode: `python -m src.main` or `./play.sh`
- Single command execution: `python -m src.main <command>` or `./play.sh <command>`
- Parser interprets commands and executes corresponding actions
- Error handling for invalid commands

### Data System
- External JSON files for items, enemies, rooms, and NPCs
- Configurable values from definition files instead of hardcoded values
- Proper loot tables based on enemy definitions
- Temporary buff system for consumable items

### Display System
- Status display showing player stats and current room
- Shows adjacent room information to aid navigation
- Full floor maps with extended ASCII characters (♀, ■, □, ∿, ≈, ░, ·)
- Local 5x5 maps around player for immediate spatial awareness
- Item location indicators on maps to aid navigation
- Stairs location indicators to show where to progress between floors

### Logging System
- Single dungeon_log.txt file that clears on new game start
- All player actions logged with timestamps and positions