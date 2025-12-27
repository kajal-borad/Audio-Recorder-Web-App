#!/bin/bash

# Stop any running Gunicorn instances
pkill gunicorn

# Start Gunicorn with a 2-minute (120s) timeout
# This prevents "[CRITICAL] WORKER TIMEOUT" errors when YouTube is slow.
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 audio_recorder_file:app
