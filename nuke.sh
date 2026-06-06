#!/bin/bash
echo "Killing zombie servers..."
fuser -k 8000/tcp 2>/dev/null
pkill -9 -f "python main.py" 2>/dev/null
echo "Clearing cache..."
find . -name "*.pyc" -delete 2>/dev/null
echo "Starting fresh server..."
python main.py