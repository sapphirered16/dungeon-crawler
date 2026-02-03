#!/bin/bash
# Launcher script for Terminal Dungeon Crawler
# Usage: ./play.sh [command]
# Example: ./play.sh move north

cd "$(dirname "$0")"
python3 src/game_engine.py "$@"