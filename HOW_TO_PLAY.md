# How to Play Terminal Dungeon Crawler

## Objective
Explore the multi-level dungeon, defeat increasingly difficult enemies, collect treasure, and find better equipment to progress deeper into the dungeon. Your ultimate goal is to find the Artifact of Power located at the bottom of the dungeon.

## Basic Gameplay
The game is turn-based and played through command-line arguments. Each action you take consumes one turn. The dungeon consists of multiple floors connected by staircases, with rooms and hallways forming branching pathways to explore.

## Commands
- `move <direction>` - Move in a direction (north, south, east, west, up, down)
- `attack <enemy_number>` - Attack an enemy in the current room (enemies are numbered)
- `take <item_number>` - Take an item from the current room (items are numbered)
- `equip <item_number>` - Equip an item from your inventory (items are numbered)
- `unequip <weapon|armor>` - Unequip weapon or armor
- `use <item_number>` - Use an item from your inventory (for keys, triggers, etc.)
- `drop <item_number>` - Drop an item from your inventory to the current room
- `look` - Look around the current room
- `inventory` - View your inventory
- `stats` - View your character stats
- `rest` - Rest to recover health
- `save` - Save the game
- `load` - Load a saved game

## Combat
Combat is turn-based. When you attack an enemy, you deal damage based on your attack stat minus the enemy's defense. Combat order is determined by initiative, which is based on your speed stat compared to the enemy's speed. If you have higher speed, you attack first; if the enemy has higher speed, it attacks first. If speeds are equal, combat order is randomized. The enemy then counterattacks if it survives your initial attack. Combat continues until either you or the enemy is defeated. Enemies become progressively stronger on deeper dungeon levels.

Some weapons and armor have special effects:
- Gruff weapons increase your damage output
- Shielding armor increases your defense
- Turbo weapons increase your initiative speed
- Light armor increases your movement speed

## Equipment
You can equip weapons and armor to increase your attack and defense stats. You can only have one weapon and one armor equipped at a time.

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
- Your ultimate goal is to reach the bottom floor and claim the Artifact of Power