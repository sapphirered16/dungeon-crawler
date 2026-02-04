# Game Design Document - Terminal Dungeon Crawler

## Overview
Terminal Dungeon Crawler is a nethack-inspired game that runs in the terminal. The game features turn-based exploration of a dungeon with combat, equipment, and progression systems. The ultimate goal is to find the Artifact of Power located at the bottom of the dungeon.

## Core Mechanics

### Movement
- Player can move in six directions: north, south, east, west, up, down
- Each movement is a discrete action
- The game maintains a coordinate system for the dungeon across multiple floors
- Stairs connect floors and allow vertical movement
- Structured dungeon layout with rooms and hallways instead of open grid

### Combat
- Turn-based combat system
- Player attacks enemy, then enemy counterattacks
- Damage calculated as attacker's attack minus defender's defense (minimum 1 damage)
- Player and enemies have health points
- Experience and leveling system
- Enemies become significantly stronger on deeper floors

### Equipment
- Weapon and armor systems
- Equipment provides attack and defense bonuses
- Player can equip/unequip items
- Limited inventory space (10 items maximum)

### Progression
- Multiple dungeon floors (5 floors total)
- Stairs connect floors and enable vertical movement
- Increasing difficulty as player descends
- Character advancement through experience
- Treasure collection
- Branching pathways encourage exploration on each floor
- Ultimate goal: Obtain the Artifact of Power from the deepest floor

### Scoring
- Points awarded for defeating enemies
- Points for collecting treasure
- Exploration bonuses for discovering new rooms and floors
- Distance traveled bonuses
- Major bonus for finding the Artifact of Power (win condition)

### Dungeon Generation
- Structured layout with rectangular rooms of varying sizes
- Hallways connecting rooms using L-shaped corridors
- Blocked areas preventing movement through walls
- Each floor has multiple branching pathways
- Ultimate Artifact of Power placed on the deepest floor

## Technical Implementation

### Game State
- Saved in JSON format
- Tracks player position, stats, inventory, dungeon layout
- Persistent between game sessions

### Command Interface
- Commands passed as arguments when executing the game binary
- Parser interprets commands and executes corresponding actions
- Error handling for invalid commands

### Display System
- Status display showing player stats and current room
- Shows adjacent room information to aid navigation
- Menu systems for inventory and character screens