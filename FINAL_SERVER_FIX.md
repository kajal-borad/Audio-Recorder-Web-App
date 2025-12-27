# Server Fix Instructions

The errors you are seeing (`Sign in to confirm you’re not a bot` and `No supported JavaScript runtime`) indicate two major issues on your DigitalOcean server:
1. **Missing JavaScript Runtime**: `yt-dlp` now requires a JavaScript engine (like Node.js) to decode YouTube's video signatures.
2. **Bot Detection**: YouTube knows your server IP is a data center. Even with cookies, if the environment isn't perfect (missing JS), it blocks you.

Follow these 3 steps to fix it permanently.

### Step 1: Install Node.js on Server
Run these commands in your server terminal to install Node.js. This removes the "No supported JavaScript runtime" warning and helps `yt-dlp` work correctly.

```bash
sudo apt-get update
sudo apt-get install -y nodejs npm
```
*Verify it is installed by running `node -v`.*

### Step 2: Update yt-dlp
Ensure you have the absolute latest version of `yt-dlp`, as YouTube changes their code daily.

```bash
pip install --upgrade yt-dlp
```

### Step 3: Refresh cookies.txt (CRITICAL)
Your current cookies are likely flagged or expired. You MUST generate fresh ones associated with a real Google account.

1. **On your local computer**, open Chrome/Firefox.
2. Install the extension **"Get cookies.txt LOCALLY"**.
3. Log in to [YouTube](https://www.youtube.com).
4. **Important**: Open a video to ensure the session is active.
5. Click the extension icon and "Export" the cookies.
6. Renames the file to `cookies.txt`.
7. Upload this NEW file to your server, replacing the old one in:
   `/root/Audio-Recorder-Web-App/cookies.txt`

   *You can copy the content of the new cookies.txt and paste it into the server file using `nano cookies.txt` if that is easier.*

### Step 4: Restart App
Kill the running process and start it again to load the new config.

```bash
# If running with gunicorn manually:
pkill gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 audio_recorder_file:app
```

**Why this fixes it:**
The "quality dropdown" failing to load is because the backend `/get_info` request fails when YouTube blocks the server. By installing Node.js and providing fresh cookies, the backend will successfully fetch the video data, and the dropdown will appear again.
