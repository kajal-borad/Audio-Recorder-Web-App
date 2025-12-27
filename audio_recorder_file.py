from flask import Flask, render_template, request, send_file, flash, redirect, after_this_request
import uuid
from yt_dlp import YoutubeDL
import time
from apscheduler.schedulers.background import BackgroundScheduler   
import os, re, glob, sys, shutil
import requests
import psycopg2
import smtplib
from email.mime.text import MIMEText
import logging

# -----------------------------
# AUTO-FIX: JavaScript Runtime
# -----------------------------
# yt-dlp needs 'node' specifically. If only 'nodejs' exists (common on Ubuntu),
# we locate it and create a temporary PATH entry so yt-dlp finds it.
try:
    if not shutil.which("node") and shutil.which("nodejs"):
        print("[INFO] 'node' command not found, but 'nodejs' exists. Patching PATH...")
        nodejs_path = shutil.which("nodejs")
        # Create a local bin folder to bridge the gap
        local_bin = os.path.join(os.path.dirname(__file__), "local_bin_fix")
        if not os.path.exists(local_bin):
            os.makedirs(local_bin)
        
        # Create symlink: local_bin/node -> /usr/bin/nodejs
        symlink_path = os.path.join(local_bin, "node")
        if not os.path.exists(symlink_path):
            os.symlink(nodejs_path, symlink_path)
            
        # Prepend to PATH for this process
        os.environ["PATH"] = local_bin + os.pathsep + os.environ["PATH"]
        print(f"[SUCCESS] Patched PATH with: {local_bin}")
        print(f"[CHECK] node version: {os.popen('node -v').read().strip()}")
except Exception as e:
    print(f"[WARNING] Failed to auto-patch Node.js: {e}")


app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.secret_key = "abc123"

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Download folder
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "downloads")
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

COOKIES_FILE = os.path.join(os.path.dirname(__file__), "cookies.txt")

# DEBUG: Check for cookies file immediately
if os.path.exists(COOKIES_FILE):
    logger.info(f"Cookies file found at: {COOKIES_FILE}")
else:
    logger.warning(f"Cookies file NOT found at: {COOKIES_FILE}. YouTube downloads will likely fail on server!")

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# -----------------------------
# CRON – delete old files
# -----------------------------

def delete_old_files():
    now = time.time()
    for file_name in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

        if os.path.isfile(file_path):
            age = now - os.path.getmtime(file_path)

            if age > 86400:
                try:
                    os.remove(file_path)
                    print("Deleted old file:", file_name)
                except Exception as e:
                    print("Delete error:", e)

# Scheduler run every 24 hours
scheduler = BackgroundScheduler()
scheduler.add_job(delete_old_files, "interval", hours=24)
scheduler.start()


# Home
@app.route("/")
def home():
    return render_template("audio_recorder_file.html")

# Contact
@app.route("/contact")
def contact():
    return render_template("contact_us.html")

progress_data = {"percent": 0}
        

@app.route("/progress")
def progress():
    return {"percent": progress_data.get("percent", 0)}


@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("youtube_url")
    format_type = request.form.get("format_type")

    quality = request.form.get("quality", "128k").replace("k", "")
    

    if not url:
        flash("Please enter a YouTube URL.")
        return redirect("/")

    # MODERN USER AGENT (Chrome 120 on Windows)
    # This helps reduce bot detection significantly compared to the old Chrome 91 string
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    common_opts = {
        'http_headers': {
            'User-Agent': user_agent,
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': True,
        'quiet': False,     # We want to see errors in logs
        'verbose': True,    # Helps debug specific YouTube blocks
        'retries': 10,      # Retry on 502/timeouts
        'fragment_retries': 10,
    }
    
    if os.path.exists(COOKIES_FILE):
        common_opts['cookies'] = COOKIES_FILE
        logger.info(f"Using cookies for extraction: {COOKIES_FILE}")
    else:
        logger.warning("No cookies found. Attempting without authentication.")

    try:
        # Pass cookies and headers here
        opts_info = {"quiet": True}
        opts_info.update(common_opts)
        
        # 'extract_info' with download=False is lighter, but still checks validity
        info = YoutubeDL(opts_info).extract_info(url, download=False)
        video_title = info.get("title", "Unknown_Title")
        clean_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', video_title).replace(" ", "_")
        thumbnail_url = info.get("thumbnail") 

    except Exception as e:
        logger.error(f"Extract info failed: {e}")
        flash("Invalid YouTube URL or server blocked. Check server logs.")
        return redirect("/")

    filename = f"{clean_title}.{format_type.lower()}"
    output_template = os.path.join(DOWNLOAD_FOLDER, f"{clean_title}.%(ext)s")
    
    ydl_opts = {
        'outtmpl': output_template,
    }
    ydl_opts.update(common_opts)

    if format_type.lower() == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'writethumbnail': True,  
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                },
                {
                    'key': 'EmbedThumbnail' 
                },
                {
                    'key': 'FFmpegMetadata'
                }
            ],
            'postprocessor_args': {
                'FFmpegMetadata': ['-id3v2_version', '3']
            },
        })
    else:
        ydl_opts.update({
            'format': 'bestvideo+bestaudio',
        })


    try:
        logger.info(f"Starting download for {url}...")
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logger.info("Download finished successfully.")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        # Even if it errors, check if file exists (sometimes ignoreerrors saves it)
        pass 

    final_file = os.path.join(DOWNLOAD_FOLDER, filename)    
    files = glob.glob(os.path.join(DOWNLOAD_FOLDER, clean_title + ".*"))
    if files:
        # Find the mp3 or mp4 properly
        for f in files:
            if f.endswith(f".{format_type.lower()}"):
                final_file = f
                break
    else:
        final_file = None

    if final_file and os.path.exists(final_file):
        return send_file(final_file, as_attachment=True, download_name=f"{clean_title}.{format_type.lower()}")
    else:
        logger.error("Final file not found after download attempt.")
        flash("Server blocked by YouTube. Please update cookies.txt using 'Get cookies.txt LOCALLY' extension.")
        return redirect("/")
    


conn = psycopg2.connect(
    host="localhost",
    database="test_db",
    user="kajalborad",   
    password="kajalborad@1912"             
)
cursor = conn.cursor()

# Admin Email
ADMIN_EMAIL = "kajalborad45@gmail.com"

@app.route("/contact_submit", methods=["POST"])
def contact_submit():
    name = request.form.get("name")
    email = request.form.get("email")
    description = request.form.get("description")

    # INSERT into database
    cursor.execute(
        "INSERT INTO lead (name, email, description) VALUES (%s, %s, %s) RETURNING id",
        (name, email, description)
    )
    lead_id = cursor.fetchone()[0]
    conn.commit()

    # SEND EMAIL TO ADMIN ON NEW LEAD
    try:
        msg_content = (
            f"New contact submission:\n\n"
            f"ID: {lead_id}\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Description: {description}"
        )

        msg = MIMEText(msg_content)
        msg['Subject'] = f"New Contact Lead #{lead_id}"
        msg['From'] = "kajalborad45@gmail.com"      # YOUR EMAIL
        msg['To'] = "kajalborad.devintelle@gmail.com"                     # ADMIN EMAIL
        msg['Reply-To'] = email                     # USER EMAIL

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("kajalborad45@gmail.com", "hekritbogafxrdte")
            server.send_message(msg)

    except Exception as e:
        print("Email sending failed:", e)

    return render_template("thankyou_template.html")


@app.route("/get_info", methods=["POST"])
def get_info():
    url = request.form.get("youtube_url")

    try:
        # Match user agent with download config
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ydl_opts_info = {
            "quiet": True,
            "http_headers": {'User-Agent': user_agent}
        }
        
        if os.path.exists(COOKIES_FILE):
             ydl_opts_info['cookies'] = COOKIES_FILE
             
        info = YoutubeDL(ydl_opts_info).extract_info(url, download=False)

        audio_formats = [
            f for f in info.get("formats", [])
            if f.get("acodec") not in [None, "none"]  
        ]

        bitrates = set()

        for f in audio_formats:
            if f.get("abr"):
                bitrates.add(int(f["abr"]))

            elif f.get("tbr"):
                bitrates.add(int(f["tbr"]))

            elif f.get("asr"):
                est = int(f["asr"] / 2 / 1000) * 10  
                if est > 0:
                    bitrates.add(est)

        bitrates = sorted(bitrates)
        print("Extracted bitrates:", bitrates)

        return {"bitrates": bitrates}

    except Exception as e:
        print("ERROR:", e)
        return {"bitrates": []}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
