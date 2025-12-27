# Server Troubleshooting Guide

The logs indicate two specific problems causing your issue:

1.  **JavaScript Runtime Missing**: `yt-dlp` cannot find `node` to execute code, causing the warning: `No supported JavaScript runtime could be found`.
2.  **Bot Detection**: YouTube is blocking the request (`Sign in to confirm you’re not a bot`), which is likely worsened by #1.

Follow these steps in order to fix your server environment.

### 1. Fix the "No JavaScript Runtime" Error
Even if you installed `npm`, the system might not have the `node` command available in the right path, or it might be named `nodejs` instead of `node`.

Run these commands on your server:

```bash
# 1. Update package list
sudo apt-get update

# 2. Install Node.js explicitly
sudo apt-get install -y nodejs npm

# 3. CRITICAL: Check if 'node' command works
node -v

# 4. If 'node -v' says "command not found" but 'nodejs -v' works, create a link:
sudo ln -s /usr/bin/nodejs /usr/bin/node
```
*Why this helps:* `yt-dlp` often needs to execute JavaScript to decode YouTube video signatures. Without it, downloads fail more often.

### 2. Update `yt-dlp` (Crucial)
YouTube changes their blocking scripts daily. You must have the absolute latest version.

```bash
# Activate your virtual environment first
source venv/bin/activate

# Force upgrade
pip install --upgrade yt-dlp

# Verify version (should be 2024.xx.xx or later)
yt-dlp --version
```

### 3. Server-Grade Cookies Export
The "Sign in to confirm you’re not a bot" error means your `cookies.txt` is either expired or flagged.

1.  **Do not use an incognito window.** Use your main browser profile.
2.  **Play a YouTube video** for at least 10 seconds to establish a "watching" session.
3.  Export cookies using the **"Get cookies.txt LOCALLY"** extension.
4.  Open the file and verify it contains lines for `.youtube.com`.
5.  Upload it to your server at `/root/Audio-Recorder-Web-App/cookies.txt`.

### 4. Restart Gunicorn Service
Restarting the service is required to pick up the new `node` path and library updates.

```bash
sudo systemctl restart gunicorn
```

### Summary Check
After doing the above, check the logs again:
```bash
journalctl -u gunicorn -f
```
You should **NO LONGER** see `WARNING: No supported JavaScript runtime could be found`.
If that warning is gone, the quality dropdown and downloads should start working.
