#!/bin/bash

# 1. Force kill anything on Port 80
echo "Freeing Port 80..."
fuser -k 80/tcp 2>/dev/null || true
lsof -t -i:80 | xargs kill -9 2>/dev/null || true
service apache2 stop 2>/dev/null
service nginx stop 2>/dev/null

# 2. Kill old Gunicorn
pkill gunicorn

# 3. Allow a few seconds for cleanup
sleep 2

# 4. Start Gunicorn on Port 80
echo "Starting server on http://167.99.95.129/ (Port 80)"
gunicorn -w 4 -b 0.0.0.0:80 --timeout 120 audio_recorder_file:app
