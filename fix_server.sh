#!/bin/bash

# 1. FIX NODE.JS (Specific for Debian/Ubuntu)
# The error "No supported JavaScript runtime" happens because yt-dlp looks for 'node'
# but sometimes only 'nodejs' is installed.
echo "--- Fixing Node.js ---"
if command -v nodejs &> /dev/null && ! command -v node &> /dev/null; then
    echo "Creating symlink for node..."
    ln -s $(which nodejs) /usr/bin/node
fi

# Verify it works
if command -v node &> /dev/null; then
    echo "✅ Node.js is active: $(node -v)"
else
    echo "❌ Node.js NOT found. Installing..."
    apt-get update
    apt-get install -y nodejs npm
fi

# 2. UPGRADE YT-DLP
# Must be latest to avoid bot detection
echo "--- Upgrading yt-dlp ---"
source venv/bin/activate
pip install --upgrade yt-dlp

# 3. RESTART GUNICORN WITH TIMEOUT
# The 'WORKER TIMEOUT' error means requests are taking >30s.
# We increase timeout to 120s for long downloads.
echo "--- Restarting Gunicorn ---"
echo "Stopping old processes..."
pkill gunicorn

echo "Starting Gunicorn with 120s timeout..."
# Run in background
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 audio_recorder_file:app --daemon

echo "✅ Server restarted on port 5000!"
echo "Check status with: ps aux | grep gunicorn"
