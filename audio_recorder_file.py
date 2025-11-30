
from flask import Flask, render_template, request, send_file, flash, redirect
import os
import uuid
from yt_dlp import YoutubeDL
import glob
import re


app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.secret_key = "abc123"


# Safe download folder path
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "downloads")
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Function to sanitize filenames
def sanitize_filename(name):
    # Remove invalid characters for filesystem
    return re.sub(r'[\\/*?:"<>|]', "", name)



# Home 
@app.route("/")
def home():
    return render_template("audio_recorder_file.html")

# Contact routes
@app.route("/contact")
def contact():
    return render_template("contact_us.html")


@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("youtube_url")
    format_type = request.form.get("format_type")

    # FIX: convert "64k" → "64"
    quality = request.form.get("quality", "128k").replace("k", "")
    print("quality========",quality)
    if not url:
        flash("Please enter a YouTube URL.")
        return redirect("/")

    try:
        info = YoutubeDL({"quiet": True}).extract_info(url, download=False)
        video_title = info.get("title", "Unknown_Title")
        clean_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', video_title).replace(" ", "_")
    except:
        flash("Invalid YouTube URL.")
        return redirect("/")

    filename = f"{clean_title}.{format_type.lower()}"
    output_template = os.path.join(DOWNLOAD_FOLDER, f"{clean_title}.%(ext)s")

    # MP3 DOWNLOAD
    if format_type.lower() == "mp3":
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': output_template,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,   # FORCE BITRATE
                },
                {
                    'key': 'FFmpegMetadata'
                }
            ]
        }

    else:
        ydl_opts = {
            'format': 'bestvideo+bestaudio',
            'outtmpl': output_template,
        }

    # DOWNLOAD
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # FINAL FILE PATH
    final_file = os.path.join(DOWNLOAD_FOLDER, filename)

    # RENAME automatically
    files = glob.glob(os.path.join(DOWNLOAD_FOLDER, clean_title + ".*"))
    if files:
        os.rename(files[0], final_file)

    return send_file(final_file, as_attachment=True)


@app.route("/get_info", methods=["POST"])
def get_info():
    url = request.form.get("youtube_url")

    try:
        info = YoutubeDL({"quiet": True}).extract_info(url, download=False)

        audio_formats = [
            f for f in info["formats"]
            if f.get("acodec") != "none" and f.get("abr")
        ]

        bitrates = sorted({ int(f["abr"]) for f in audio_formats })

        return {"bitrates": bitrates}
    except:
        return {"bitrates": []}


# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)


