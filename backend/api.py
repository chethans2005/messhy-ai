"""
Flask web server — HTTP interface for the mesh generation pipeline.

Run with:
    python api.py

Then open http://localhost:5000 in your browser.
"""
import logging
import sys
import threading
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

# Ensure backend/ is importable when running api.py directly.
sys.path.insert(0, str(Path(__file__).parent))

from core.config import config
from core.device import DeviceManager
from core.utils import setup_logging
from main import run_pipeline

setup_logging(config.log_level)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app = Flask(__name__)

# job_id -> {"status": "running|done|error", "message": str, "output_path": str}
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = str(data.get("prompt", "")).strip()

    if not prompt:
        return jsonify({"error": "Prompt cannot be empty."}), 400
    if len(prompt) > 500:
        return jsonify({"error": "Prompt must be 500 characters or fewer."}), 400

    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {"status": "running", "message": "Initialising..."}

    thread = threading.Thread(target=_run_job, args=(job_id, prompt), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id}), 202


@app.route("/status/<job_id>")
def status(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found."}), 404
    return jsonify(job)


@app.route("/download/<job_id>")
def download(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found."}), 404
    if job["status"] != "done":
        return jsonify({"error": "Mesh not ready yet."}), 409

    output_path = Path(job["output_path"])
    return send_file(
        str(output_path),
        as_attachment=True,
        download_name=output_path.name,
        mimetype="model/gltf-binary",
    )


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

def _run_job(job_id: str, prompt: str) -> None:
    try:
        _update_job(job_id, message="Loading models onto GPU...")
        output_path = run_pipeline(prompt)
        _update_job(job_id, status="done", message="Mesh ready!", output_path=output_path)
        logger.info("Job %s complete → %s", job_id, output_path)
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _update_job(job_id, status="error", message=f"Generation failed: {exc}")


def _update_job(job_id: str, **kwargs) -> None:
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(kwargs)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    dm = DeviceManager()
    dm.log_info()
    logger.info("Server starting at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
