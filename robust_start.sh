#!/bin/bash

# Stop existing processes
pkill gunicorn

# Start Gunicorn on PORT 80 (Standard Web Port)
# This removes the need for :5000 or :8000
echo "Starting server on http://167.99.95.129/ (Port 80)"
gunicorn -w 4 -b 0.0.0.0:80 --timeout 120 audio_recorder_file:app
