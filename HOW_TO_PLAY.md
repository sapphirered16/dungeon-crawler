# How to Play Terminal Dungeon Crawler

## Objective
Explore the multi-level dungeon, defeat increasingly difficult enemies, collect treasure, and find better equipment to progress deeper into the dungeon. Your ultimate goal is to find the Artifact of Power located at the bottom of the dungeon.

## Basic Gameplay
The game is turn-based and played through command-line arguments. Each action you take consumes one turn. The dungeon consists of multiple floors connected by staircases, with rooms and hallways forming branching pathways to explore.

## Starting the Game
```bash
# Interactive mode with random seed
python -m src.main
# or
./play.sh

# Interactive mode with specific seed
python -m src.main --seed 12345
# or
./play.sh 12345

# Single command execution
python -m src.main stats
# or
./play.sh stats
```

## Commands
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

## Combat
Combat is turn-based. When you attack an enemy, you deal damage based on your attack stat minus the enemy's defense. Combat order is determined by initiative, which is based on your speed stat compared to the enemy's speed. If you have higher speed, you attack first; if the enemy has higher speed, it attacks first. If speeds are equal, combat order is randomized. The enemy then counterattacks if it survives your initial attack. Combat continues until either you or the enemy is defeated. Enemies become progressively stronger on deeper dungeon levels.

Some weapons and armor have special effects:
- Gruff weapons increase your damage output
- Shielding armor increases your defense
- Turbo weapons increase your initiative speed
- Light armor increases your movement speed

## Equipment
You can equip weapons and armor to increase your attack and defense stats. You can only have one weapon and one armor equipped at a time.

## Environmental Hazards
Watch out for environmental hazards that appear throughout the dungeon:
- Hidden traps that cause damage when stepped on
- Wet areas that provide flavor text
- Poisonous zones that cause damage and status effects
- Icy surfaces that affect movement
- Dark corners that affect visibility
- Slippery floors that cause movement issues
- Loud floors that alert nearby creatures
- Magnetic fields that affect metal objects

## Locked Doors & Blocked Passages
Some areas are blocked by locked doors or blocked passages that require specific keys or trigger items to pass through. These puzzle elements require strategic exploration to find the necessary items.

## Scoring
Your score increases based on:
- Enemies defeated
- Treasure collected
- Exploration (rooms and floors explored)
- Distance traveled
- Finding the ultimate Artifact of Power (major bonus!)

## Strategy Tips
- Explore thoroughly to find better equipment and treasure
- Defeat enemies to gain experience and improve your stats
- Each floor has multiple branching pathways - try different routes
- Deeper floors contain stronger enemies but also better rewards
- Look for items before encountering obstacles that require them
- Use the `items` command to locate areas with items
- Use the `stairs` command to find staircases to progress to other floors
- Your ultimate goal is to reach the bottom floor and claim the Artifact of Power