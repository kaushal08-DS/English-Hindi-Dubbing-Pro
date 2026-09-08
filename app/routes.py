import json
import threading
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename


bp = Blueprint("main", __name__)
ALLOWED = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v"}

def job_file(job_id):
    return current_app.config["STORAGE"] / "jobs" / f"{job_id}.json"

def save_job(job):
    job_file(job["id"]).write_text(
        json.dumps(job, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def read_job(job_id):
    p = job_file(job_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

@bp.get("/")
def index():
    return render_template("index.html")

@bp.post("/api/jobs")
def create_job():
    video = request.files.get("video")
    if not video or not video.filename:
        return jsonify({"error": "Please select an English video."}), 400

    suffix = Path(video.filename).suffix.lower()
    if suffix not in ALLOWED:
        return jsonify({"error": f"Unsupported video format: {suffix}"}), 400

    job_id = uuid.uuid4().hex
    original_name = secure_filename(video.filename)
    upload_path = (
        current_app.config["STORAGE"]
        / "uploads"
        / f"{job_id}{suffix}"
    )
    video.save(upload_path)

    whisper_model = request.form.get("whisper_model") or current_app.config["WHISPER_MODEL"]
    min_speakers = int(request.form.get("min_speakers") or current_app.config["MIN_SPEAKERS"])
    max_speakers = int(request.form.get("max_speakers") or current_app.config["MAX_SPEAKERS"])

    if min_speakers < 1 or max_speakers < min_speakers:
        return jsonify({"error": "Invalid speaker range."}), 400

    job = {
        "id": job_id,
        "filename": original_name,
        "status": "queued",
        "progress": 0,
        "stage": "Queued",
        "message": "Waiting to start.",
        "output": None,
        "transcript": None,
        "speaker_map": None,
        "error": None,
        "whisper_model": whisper_model,
        "min_speakers": min_speakers,
        "max_speakers": max_speakers,
    }
    save_job(job)

    def start_job(app_obj, job_id, upload_path, whisper_model, min_speakers, max_speakers):
        from .services.dubbing import run_dubbing

        run_dubbing(
            app_obj,
            job_id,
            upload_path,
            whisper_model,
            min_speakers,
            max_speakers,
        )


    thread = threading.Thread(
        target=start_job,
        args=(
            app_obj,
            job_id,
            upload_path,
            whisper_model,
            min_speakers,
            max_speakers,
        ),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id}), 202

@bp.get("/api/jobs/<job_id>")
def job_status(job_id):
    job = read_job(job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    return jsonify(job)

@bp.get("/api/jobs/<job_id>/download")
def download(job_id):
    job = read_job(job_id)
    if not job or not job.get("output"):
        return jsonify({"error": "Output is not ready."}), 404

    path = Path(job["output"])
    if not path.exists():
        return jsonify({"error": "Output file is missing."}), 404

    return send_file(
        path,
        as_attachment=True,
        download_name=path.name,
        mimetype="video/mp4",
    )
