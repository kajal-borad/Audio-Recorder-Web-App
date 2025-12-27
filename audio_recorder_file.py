from flask import Flask, render_template, request, send_file, flash, redirect, after_this_request
import uuid
from yt_dlp import YoutubeDL
import time
from apscheduler.schedulers.background import BackgroundScheduler   
import os, re, glob
import requests
import psycopg2
import smtplib
from email.mime.text import MIMEText


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

    try:
        info = YoutubeDL({"quiet": True}).extract_info(url, download=False)
        video_title = info.get("title", "Unknown_Title")
        clean_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', video_title).replace(" ", "_")
        thumbnail_url = info.get("thumbnail")  # get thumbnail URL

    except:
        flash("Invalid YouTube URL.")
        return redirect("/")

    filename = f"{clean_title}.{format_type.lower()}"
    output_template = os.path.join(DOWNLOAD_FOLDER, f"{clean_title}.%(ext)s")
    if format_type.lower() == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'writethumbnail': True,  
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                },
                {
                    'key': 'EmbedThumbnail'  # embed thumbnail into mp3
                },
                {
                    'key': 'FFmpegMetadata'
                }
            ],
            'postprocessor_args': {
                'FFmpegMetadata': ['-id3v2_version', '3']
            },
            'cookies': '/root/Audio-Recorder-Web-App/cookies.txt',  # <-- Add this line

        }
    else:
        ydl_opts = {
            'format': 'bestvideo+bestaudio',
            'outtmpl': output_template,
            'cookies': '/root/Audio-Recorder-Web-App/cookies.txt',  # <-- Add this line


        }


    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    final_file = os.path.join(DOWNLOAD_FOLDER, filename)    
    files = glob.glob(os.path.join(DOWNLOAD_FOLDER, clean_title + ".*"))
    if files:
        final_file = os.path.join(DOWNLOAD_FOLDER, filename)
        os.rename(files[0], final_file)
    else:
        final_file = None

    return send_file(final_file, as_attachment=True, download_name=f"{clean_title}.{format_type.lower()}")
    


conn = psycopg2.connect(
    host="localhost",
    database="test_db",
    user="darshangajera",   
    password=""             
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
        info = YoutubeDL({"quiet": True}).extract_info(url, download=False)

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
    app.run(host="0.0.0.0", port=8000, debug=True)
