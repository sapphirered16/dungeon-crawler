#!/bin/bash

# Terminal Dungeon Crawler - Main Play Script
# Usage: ./play.sh [seed] [command]
# Examples:
#   ./play.sh                  # Interactive play with random seed
#   ./play.sh 12345           # Interactive play with specific seed
#   ./play.sh stats           # Run single command with random seed
#   ./play.sh 12345 stats     # Run single command with specific seed
#   ./play.sh newgame         # Start new game with random seed
#   ./play.sh newgame 12345   # Start new game with specific seed

if [ $# -eq 0 ]; then
    # No arguments - interactive mode with random seed
    python3 -m src.main
elif [ $# -eq 1 ]; then
    # One argument - could be seed, command, or newgame
    arg="$1"
    if [[ "$arg" =~ ^[0-9]+$ ]]; then
        # It's a number - treat as seed for interactive mode
        python3 -m src.main --seed "$arg"
    elif [ "$arg" = "newgame" ]; then
        # It's the newgame command - start new game with random seed
        python3 -m src.main --newgame
    else
        # It's not a number - treat as command with random seed
        python3 -m src.main "$arg"
    fi
elif [ $# -eq 2 ]; then
    # Two arguments - could be newgame with seed, or seed with command
    first_arg="$1"
    second_arg="$2"
    
    if [ "$first_arg" = "newgame" ] && [[ "$second_arg" =~ ^[0-9]+$ ]]; then
        # newgame with specific seed: ./play.sh newgame 12345
        python3 -m src.main --newgame --seed "$second_arg"
    elif [[ "$first_arg" =~ ^[0-9]+$ ]] && [ "$second_arg" != "newgame" ]; then
        # seed with command: ./play.sh 12345 stats
        python3 -m src.main --seed "$first_arg" "$second_arg"
    else
        echo "Usage: ./play.sh [seed] [command] or ./play.sh newgame [seed]"
        echo "Examples:"
        echo "  ./play.sh 12345 stats    # Run single command with specific seed"
        echo "  ./play.sh newgame 12345  # Start new game with specific seed"
        exit 1
    fi
else
    echo "Usage: ./play.sh [seed] [command] or ./play.sh newgame [seed]"
    echo "Examples:"
    echo "  ./play.sh                    # Interactive play with random seed"
    echo "  ./play.sh 12345             # Interactive play with specific seed"
    echo "  ./play.sh stats             # Run single command with random seed"
    echo "  ./play.sh 12345 stats       # Run single command with specific seed"
    echo "  ./play.sh newgame           # Start new game with random seed"
    echo "  ./play.sh newgame 12345     # Start new game with specific seed"
    exit 1
fi