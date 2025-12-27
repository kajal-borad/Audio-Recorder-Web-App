# Final Server Fix Instructions

Your server is correctly reading the `cookies.txt` file (as seen in the logs: `[INFO] Cookies file found...`), but YouTube is still rejecting the connection. This is because:
1.  **Missing Dependencies**: Your logs show `WARNING: No supported JavaScript runtime could be found`. `yt-dlp` REQUIRES a JavaScript engine to correctly decode YouTube video signatures. Without it, requests are flagged as suspicious.
2.  **Datacenter IP**: DigitalOcean IPs are known "bot" IPs.

## Step 1: Install Node.js (Critical Fix)
You must install Node.js on your server so `yt-dlp` can execute necessary scripts. Run these commands on your server terminal:

```bash
# Update package list
sudo apt update

# Install Node.js and NPM
sudo apt install -y nodejs npm

# Verify installation
node -v
```

## Step 2: Use the Correct Port
You asked which port to run in the browser.
Since you are running Gunicorn on port **8000** (`-b 0.0.0.0:8000`), you must access your site at:

**http://167.99.95.129:8000/**

## Step 3: Refresh Info
After installing Node.js, restart your server app:
```bash
sudo systemctl restart gunicorn
# OR if running manually
kill <pid>
gunicorn -w 4 -b 0.0.0.0:8000 audio_recorder_file:app
```

## Step 4: If it STILL fails (Advanced)
If you still get "Sign in to confirm you’re not a bot" after installing Node.js, it means your `cookies.txt` is either:
*   **Expired**: Export them again from a fresh "Incognito" window where you just logged in.
*   **IP-Locked**: YouTube sometimes invalidates cookies used on a different IP (your home IP vs server IP). 
    *   *Solution*: Try to use a browser extension that exports cookies in Netscape format specifically, or try using an "Authentication" specific plugin for yt-dlp if available, but usually, a fresh cookie export + Node.js fixes 90% of cases.

### Why does OGMP3.com work?
Private downloading sites like that pay for **Residential Proxies**. They route their traffic through home internet connections so YouTube thinks they are normal users. Your DigitalOcean server is a known commercial cloud server, which YouTube blocks more aggressively.
