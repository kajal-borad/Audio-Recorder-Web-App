import threading

# ... (rest of imports)

# Helper function for async email
def send_async_email(name, email, description, lead_id):
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
        msg['From'] = "kajalborad45@gmail.com"
        msg['To'] = "kajalborad.devintelle@gmail.com"
        msg['Reply-To'] = email

        # Set a short timeout so the thread doesn't hang forever
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.starttls()
            server.login("kajalborad45@gmail.com", "hekritbogafxrdte")
            server.send_message(msg)
            logger.info(f"Email sent for lead #{lead_id}")

    except Exception as e:
        logger.error(f"Email sending failed: {e}")

@app.route("/contact_submit", methods=["POST"])
def contact_submit():
    name = request.form.get("name")
    email = request.form.get("email")
    description = request.form.get("description")

    lead_id = None

    try:
        # Create a fresh connection for every request
        conn = psycopg2.connect(
            host="localhost",
            database="test_db",
            user="kajalborad",   
            password="kajalborad@1912"             
        )
        cursor = conn.cursor()

        # INSERT into database
        cursor.execute(
            "INSERT INTO lead (name, email, description) VALUES (%s, %s, %s) RETURNING id",
            (name, email, description)
        )
        lead_id = cursor.fetchone()[0]
        conn.commit()
        
        # Clean up
        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Database Error: {e}")
        return f"Database Error: {e}", 500

    # SEND EMAIL IN BACKGROUND THREAD
    if lead_id:
        threading.Thread(target=send_async_email, args=(name, email, description, lead_id)).start()

    return render_template("thankyou_template.html")

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# -----------------------------
# AGGRESSIVE FIX: JavaScript Runtime
# -----------------------------
# yt-dlp REQUIRES 'node' in the path. On Debian/Ubuntu, it is often 'nodejs'.
# Since this script runs as root, we will creates a global symlink if missing.
try:
    node_path = shutil.which("node")
    nodejs_path = shutil.which("nodejs")
    
    # If 'node' is missing but 'nodejs' is found, FORCE LINK IT
    if not node_path and nodejs_path:
        logger.info(f"'node' command not found, but '{nodejs_path}' exists. Creating global symlink...")
        try:
            # Force create symlink /usr/bin/node -> /usr/bin/nodejs
            subprocess.run(["ln", "-sf", nodejs_path, "/usr/bin/node"], check=True)
            logger.info("[SUCCESS] Created /usr/bin/node symlink.")
        except Exception as e:
            logger.error(f"Failed to create symlink: {e}")

    # Double check status for logs
    check_node = shutil.which("node")
    if check_node:
        try:
            version = subprocess.getoutput("node -v")
            logger.info(f"Node.js is active: {check_node} ({version})")
        except:
            logger.info(f"Node.js found at {check_node}, but version check failed.")
    else:
        logger.warning("CRITICAL: Node.js is NOT found. YouTube downloads will fail.")

except Exception as e:
    logger.error(f"Node.js fix error: {e}")


app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.secret_key = "abc123"



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
    req_id = request.args.get("req_id")
    if not req_id:
        return {"percent": 0, "status": "waiting"}
    
    progress_file = os.path.join(DOWNLOAD_FOLDER, f"{req_id}.progress")
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r") as f:
                data = f.read().strip().split("|")
                if len(data) >= 2:
                    return {"percent": int(data[0]), "status": data[1]}
                return {"percent": int(data[0]), "status": "processing"}
        except:
            pass
    return {"percent": 0, "status": "starting"} or {"percent": 0}


@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("youtube_url")
    format_type = request.form.get("format_type")
    req_id = request.form.get("req_id", str(uuid.uuid4()))
    
    quality = request.form.get("quality", "128k").replace("k", "")
    

    if not url:
        flash("Please enter a YouTube URL.")
        return redirect("/")

    # Progress Hook function (File-based for Gunicorn compatibility)
    def progress_hook(d):
        progress_file = os.path.join(DOWNLOAD_FOLDER, f"{req_id}.progress")
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                if total:
                    percent = int(downloaded / total * 100)
                    with open(progress_file, "w") as f:
                        f.write(f"{percent}|Downloading")
            except:
                pass
        elif d['status'] == 'finished':
            with open(progress_file, "w") as f:
                f.write("100|Converting")

    # Let yt-dlp handle User-Agent dynamically to reduce bot flags
    # We also specify a cache directory to avoid stale temp files
    common_opts = {
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': True,
        'quiet': False,     
        'verbose': True,    
        'retries': 10,      
        'fragment_retries': 10,
        'cache_dir': '/tmp/yt_dlp_cache',
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
        
        # Clear cache before extraction to fix 'No JS' warnings
        with YoutubeDL(opts_info) as ydl:
            ydl.cache.remove()
            info = ydl.extract_info(url, download=False)
        
        # ERROR FIX: Check if info is None before accessing
        if not info:
             raise Exception("YoutubeDL returned no info (None).")

        video_title = info.get("title", "Unknown_Title")
        clean_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', video_title).replace(" ", "_") 
        # Clean title further to prevent path issues
        clean_title = sanitize_filename(clean_title)

    except Exception as e:
        logger.error(f"Extract info failed: {e}")
        flash("Server blocked by YouTube. Try updating cookies.txt.")
        return redirect("/")

    filename = f"{clean_title}.{format_type.lower()}"
    output_template = os.path.join(DOWNLOAD_FOLDER, f"{clean_title}.%(ext)s")
    
    ydl_opts = {
        'outtmpl': output_template,
        'progress_hooks': [progress_hook],
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
        # Even if it errors, we check if file exists (ignoreerrors=True might have saved it)
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
        # Clean up progress file
        progress_file = os.path.join(DOWNLOAD_FOLDER, f"{req_id}.progress")
        if os.path.exists(progress_file):
            os.remove(progress_file)
            
        return send_file(final_file, as_attachment=True, download_name=f"{clean_title}.{format_type.lower()}")
    else:
        logger.error("Final file not found after download attempt.")
        flash("Download failed. YouTube blocked the server request.")
        return redirect("/")
    


# Admin Email
ADMIN_EMAIL = "kajalborad45@gmail.com"

@app.route("/contact_submit", methods=["POST"])
def contact_submit():
    name = request.form.get("name")
    email = request.form.get("email")
    description = request.form.get("description")

    lead_id = None

    try:
        # Create a fresh connection for every request to avoid "InFailedSqlTransaction"
        conn = psycopg2.connect(
            host="localhost",
            database="test_db",
            user="kajalborad",   
            password="kajalborad@1912"             
        )
        cursor = conn.cursor()

        # INSERT into database
        cursor.execute(
            "INSERT INTO lead (name, email, description) VALUES (%s, %s, %s) RETURNING id",
            (name, email, description)
        )
        lead_id = cursor.fetchone()[0]
        conn.commit()
        
        # Clean up
        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Database Error: {e}")
        return f"Database Error: {e}", 500

    # SEND EMAIL IN BACKGROUND THREAD
    if lead_id:
        threading.Thread(target=send_async_email, args=(name, email, description, lead_id)).start()

    return render_template("thankyou_template.html")


@app.route("/get_info", methods=["POST"])
def get_info():
    url = request.form.get("youtube_url")

    try:
        # Attempt to use mobile clients to bypass 'Bot' detection for metadata
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ydl_opts_info = {
            "quiet": True,
            "http_headers": {'User-Agent': user_agent},
            "extractor_args": {'youtube': {'player_client': ['android', 'ios']}}
        }
        
        if os.path.exists(COOKIES_FILE):
             ydl_opts_info['cookies'] = COOKIES_FILE
             
        info = YoutubeDL(ydl_opts_info).extract_info(url, download=False)
        
        # ERROR FIX: Check None
        if not info:
            return {"bitrates": []}

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
        logger.info(f"Extracted bitrates: {bitrates}")

        return {"bitrates": bitrates}

    except Exception as e:
        logger.error(f"get_info ERROR: {e}")
        # User requested dynamic ONLY. If it fails, we return empty list.
        # This means if the server is blocked, the dropdown will NOT populate.
        return {"bitrates": []}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
