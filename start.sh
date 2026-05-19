#!/bin/bash
# Start the NOVA-7 app
PIDS=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}')
if [ -n "$PIDS" ]; then
    echo "Already running (PIDs: $(echo $PIDS | tr '\n' ' '))"
    exit 0
fi
PYTHON=$(command -v python3)
nohup "$PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8080 > /tmp/nova7.log 2>&1 &
sleep 2
PIDS=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}')
if [ -n "$PIDS" ]; then
    echo "Started (PIDs: $(echo $PIDS | tr '\n' ' '))"
else
    echo "Failed to start — check /tmp/nova7.log"
    exit 1
fi
