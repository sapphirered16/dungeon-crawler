#!/bin/bash

# Terminal Dungeon Crawler - Main Play Script
# Usage: ./play.sh [seed] [command]
# Examples:
#   ./play.sh                  # Interactive play with random seed
#   ./play.sh 12345           # Interactive play with specific seed
#   ./play.sh stats           # Run single command with random seed
#   ./play.sh 12345 stats     # Run single command with specific seed

if [ $# -eq 0 ]; then
    # No arguments - interactive mode with random seed
    python3 -m src.main
elif [ $# -eq 1 ]; then
    # One argument - could be seed or command
    arg="$1"
    if [[ "$arg" =~ ^[0-9]+$ ]]; then
        # It's a number - treat as seed for interactive mode
        python3 -m src.main --seed "$arg"
    else
        # It's not a number - treat as command with random seed
        python3 -m src.main "$arg"
    fi
elif [ $# -eq 2 ]; then
    # Two arguments - first is seed, second is command
    seed="$1"
    command="$2"
    if [[ "$seed" =~ ^[0-9]+$ ]]; then
        python3 -m src.main --seed "$seed" "$command"
    else
        echo "Usage: ./play.sh [seed] [command]"
        echo "Example: ./play.sh 12345 stats"
        exit 1
    fi
else
    echo "Usage: ./play.sh [seed] [command]"
    echo "Examples:"
    echo "  ./play.sh              # Interactive play with random seed"
    echo "  ./play.sh 12345        # Interactive play with specific seed"
    echo "  ./play.sh stats        # Run single command with random seed"
    echo "  ./play.sh 12345 stats  # Run single command with specific seed"
    exit 1
fi