# Deployment Fix Instructions

It appears your DigitalOcean server IP is blocked by YouTube, which is causing the "Sign in to confirm you’re not a bot" error. This is common for data center IPs.

I have updated your `audio_recorder_file.py` to properly use a `cookies.txt` file for authentication.

## 1. Get Valid Cookies
The current `cookies.txt` in your project seems to be an auto-generated one that doesn't contain authentication credentials. You need to export cookies from your actual browser where you are logged into YouTube.

1. Install a browser extension like **"Get cookies.txt LOCALLY"** (available for Chrome/Firefox).
2. Go to [YouTube.com](https://www.youtube.com) and ensure you are **logged in**.
3. Use the extension to **export cookies** as a file named `cookies.txt`.
   - *Note: Ensure the content looks like Netscape format (lines starting with `.youtube.com` and containing `TRUE`/`FALSE`).*

## 2. Upload Config
1. **Replace** the local `cookies.txt` file with the one you just exported.
2. Push the updated code (including the new `audio_recorder_file.py`) to your server.
3. **Important**: Since `cookies.txt` contains sensitive session data, be careful if you are pushing to a public Git repository. If using Git, you might want to upload `cookies.txt` manually to the server using `scp` or `sftp` instead of committing it.
   
   **Manual Upload Example:**
   ```bash
   scp path/to/cookies.txt root@167.99.95.129:~/Audio-Recorder-Web-App/
   ```

## 3. Server Dependencies
Ensure **FFmpeg** is installed on your server, as it is required for converting to MP3.
```bash
sudo apt update
sudo apt install ffmpeg
```

## 4. Restart Server
After updating the code and cookies file, restart your Gunicorn service to apply changes.
```bash
sudo systemctl restart gunicorn
# OR if running manually
kill <gunicorn_pid>
gunicorn -w 4 -b 0.0.0.0:8000 audio_recorder_file:app
```
