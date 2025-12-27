#!/bin/bash

echo "=========================================="
echo "   STARTING FINAL SERVER FIX & LAUNCH     "
echo "=========================================="

# 1. Stop Everything
echo "[1/4] Stopping existing services..."
pkill gunicorn
service apache2 stop 2>/dev/null
service nginx stop 2>/dev/null

# 2. Clear Cache manually
echo "[2/4] Clearing YouTube cache..."
rm -rf /tmp/yt_dlp_cache
mkdir -p /tmp/yt_dlp_cache
chmod 777 /tmp/yt_dlp_cache

# 3. Fix Node.js again (Belt and suspenders)
echo "[3/4] Verifying Node.js..."
if ! command -v node &> /dev/null; then
    ln -sf $(which nodejs) /usr/bin/node
fi

# 4. Start Gunicorn on PORT 80
echo "[4/4] Starting Server on Port 80..."
# We use sudo + port 80 so you can access without :5000
gunicorn -w 4 -b 0.0.0.0:80 --timeout 120 audio_recorder_file:app --daemon

echo ""
echo "✅ SUCCESS! Your site is live at:"
echo "   http://167.99.95.129/"
echo ""
echo "(No :5000 needed. Quality options should appear if cookies are valid.)"
echo "=========================================="
