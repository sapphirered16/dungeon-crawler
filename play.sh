#!/bin/bash
# Launcher script for Terminal Dungeon Crawler

cd "$(dirname "$0")"
python3 src/game_engine.py "$@"