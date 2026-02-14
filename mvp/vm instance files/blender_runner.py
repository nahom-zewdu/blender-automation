# blender_runner.py
""" Flask server to receive rendering jobs, download assets from Google Drive, run Blender, and upload results to GCS. """

import os
import subprocess
import io
from flask import Flask, request, jsonify

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.cloud import storage


# ---------- CONFIG ----------
SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]

ASSET_DIR = "assets"
OUTPUT_DIR = "outputs"
BLENDER_SCRIPT = "scene_builder.py"
GCS_BUCKET_NAME = "blender-renders-output"

os.makedirs(ASSET_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------- GOOGLE DRIVE ----------
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=credentials)


def download_file(file_id, local_path):
    print("Downloading:", file_id)

    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(local_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"Progress: {int(status.progress() * 100)}%")

    if not os.path.exists(local_path) or os.path.getsize(local_path) < 1000:
        raise Exception("Download failed or file corrupted")

    print("Downloaded:", local_path)


# ---------- GCS ----------
gcs_client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
bucket = gcs_client.bucket(GCS_BUCKET_NAME)


def upload_to_gcs(local_file_path, remote_filename):
    if not os.path.exists(local_file_path):
        raise Exception("Render output missing")

    blob = bucket.blob(remote_filename)
    blob.upload_from_filename(local_file_path)
    blob.make_public()

    print("Uploaded:", blob.public_url)
    return blob.public_url


# ---------- FLASK ----------
app = Flask(__name__)


@app.route("/run-job", methods=["POST"])
def run_job():
    try:
        data = request.get_json()
        assets = data.get("assets", [])
        output_name = data.get("output_name", "render")

        if not assets:
            return jsonify({"error": "No assets provided"}), 400

        # -------- DOWNLOAD --------
        local_paths = []
        for asset in assets:
            filename = asset["name"]
            file_id = asset["id"]
            local_path = os.path.join(ASSET_DIR, filename)
            download_file(file_id, local_path)
            local_paths.append(local_path)

        # Convert list -> comma string (IMPORTANT)
        asset_arg = ",".join(local_paths)

        # -------- RUN BLENDER --------
        cmd = [
            "xvfb-run",
            "-s", "-screen 0 1024x768x24",
            "blender",
            "-b",
            "-noaudio",
            "-P", BLENDER_SCRIPT,
            "--",
            asset_arg,
            output_name + ".png"
        ]

        print("Running:", " ".join(cmd))
        subprocess.run(cmd, check=True)

        # -------- UPLOAD --------
        output_local_path = os.path.join(OUTPUT_DIR, output_name + ".png")
        public_url = upload_to_gcs(output_local_path, output_name + ".png")

        return jsonify({
            "status": "success",
            "gcs_url": public_url
        })

    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error",
            "message": "Blender execution failed",
            "details": str(e)
        }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)