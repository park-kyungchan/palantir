#!/bin/bash
# Kill previous instances
pkill -f "uvicorn"
pkill -f "vite"

# Start Backend (Port 8000)
echo "Starting Backend on 8000..."
cd /home/palantir/math/backend
source .venv/bin/activate
nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
disown $!
echo "Backend launched."

# Start Frontend (Port 3000)
echo "Starting Frontend on 3000..."
cd /home/palantir/math/frontend
nohup ./node_modules/.bin/vite --host 0.0.0.0 --port 3000 > ../frontend.log 2>&1 &
disown $!
echo "Frontend launched."

# Wait for startup
echo "Waiting for services to stabilize..."
sleep 10

# Verify
curl -I http://127.0.0.1:8000/health
curl -I http://127.0.0.1:3000