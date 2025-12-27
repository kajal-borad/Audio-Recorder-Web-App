#!/bin/bash

# Stop any running Gunicorn instances
pkill gunicorn

# Stop default web servers that might block port 80
# (Ignore errors if they aren't installed)
service apache2 stop 2>/dev/null
service nginx stop 2>/dev/null

# Start Gunicorn on Port 80 (Default HTTP port)
# This allows access via http://IP/ without :5000
gunicorn -w 4 -b 0.0.0.0:80 --timeout 120 audio_recorder_file:app
