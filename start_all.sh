#!/bin/bash
cd /tmp/A2OwoFarmer || exit 1
TOKEN_FILE="$(dirname "$0")/tokens.txt"

if [ ! -f "$TOKEN_FILE" ]; then
    echo "Error: $TOKEN_FILE not found. Place your Discord token there."
    exit 1
fi

TOKEN=$(cat "$TOKEN_FILE" | head -1 | tr -d '[:space:]')
if [ -z "$TOKEN" ]; then
    echo "Error: Token file is empty."
    exit 1
fi

pkill -f "a2.py" 2>/dev/null
pkill -f "app.py" 2>/dev/null
sleep 1

python3 << 'PYEOF' &>/tmp/flask_dash.log &
import sys, os, logging
sys.path.insert(0, '/tmp/A2OwoFarmer')
os.chdir('/tmp/A2OwoFarmer')
from dashboard.app import app
logging.getLogger('werkzeug').setLevel(logging.ERROR)
app.run(host='0.0.0.0', port=6909, debug=False, threaded=True)
PYEOF

sleep 3

python3 a2.py "$TOKEN" &>/tmp/a2_output.log &

echo "All started"
