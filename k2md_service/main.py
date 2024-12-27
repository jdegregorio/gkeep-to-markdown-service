import os
import logging
from flask import Flask, request, jsonify

from loguru import logger
from app.sync_manager import run_sync

app = Flask(__name__)

# Configure loguru to log to stdout so Cloud Run captures it
logger.remove()
logger.add(lambda msg: logging.info(msg), format="{message}", level="INFO")

@app.route("/")
def health_check():
    return "OK"

@app.route("/sync", methods=["GET", "POST"])
def sync():
    """
    Trigger the note sync & enrichment process.
    Called by Cloud Scheduler (GET) or manual triggers (POST).
    """
    logger.info("Sync endpoint called. Starting synchronization...")
    try:
        processed_count = run_sync()
        return jsonify({"status": "success", "processed_notes": processed_count}), 200
    except Exception as e:
        logger.exception("Exception occurred during sync:")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # For local dev:
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
