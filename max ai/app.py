"""
Max AI — backend proxy
=======================
A minimal Flask server that does two things:

1. Serves max_ai.html as the web app's frontend.
2. Proxies /api/chat, /api/image and /api/tts to Google's Gemini API using a
   server-side API key (GEMINI_API_KEY), so the key never has to be typed
   into the browser or shipped in client-side JavaScript.

This is optional. The frontend also works completely standalone (client
calls Gemini directly using a key entered in Settings) — running this
backend and turning on "Use secure backend proxy" in Settings is only
needed if you want the key to live on a server instead of in the browser.

Run locally:
    pip install -r requirements.txt
    export GEMINI_API_KEY="your-key-here"
    python app.py

Then open http://localhost:5000
"""

import logging
import os
import time
from pathlib import Path

import requests
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
REQUEST_TIMEOUT_SECONDS = 60

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

# ---------------------------------------------------------------------------
# Logging — every request and error gets a timestamp in logs/app.log
# ---------------------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("max_ai")


def call_gemini(model: str, payload: dict):
    """Forward a payload to Google's Gemini generateContent endpoint."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set on the server. "
            "Set it as an environment variable before starting app.py."
        )
    url = f"{GEMINI_BASE_URL}/{model}:generateContent?key={GEMINI_API_KEY}"
    response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    return response


def call_ollama(model: str, payload: dict):
    """Forward a chat request to the local Ollama server."""
    if not model:
        raise ValueError("An Ollama model is required.")
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError("Ollama payload must include a non-empty messages list.")
    ollama_payload = {"model": model, "messages": messages, "stream": False}
    if "temperature" in payload:
        ollama_payload["options"] = {"temperature": payload["temperature"]}
    return requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=ollama_payload, timeout=REQUEST_TIMEOUT_SECONDS)


def proxy_request(default_model: str):
    """Shared handler for the three /api/* proxy routes."""
    try:
        body = request.get_json(force=True, silent=False)
        if not body or "payload" not in body:
            return jsonify(error={"message": "Request body must include a 'payload' field."}), 400

        model = body.get("model") or default_model
        payload = body["payload"]

        upstream = call_gemini(model, payload)

        # Pass through Gemini's own JSON body and status code as-is so the
        # frontend's existing error handling (response.ok checks) keeps working.
        return (upstream.text, upstream.status_code, {"Content-Type": "application/json"})

    except RuntimeError as e:
        logger.error("Configuration error: %s", e)
        return jsonify(error={"message": str(e)}), 500
    except requests.exceptions.Timeout:
        logger.error("Upstream Gemini request timed out")
        return jsonify(error={"message": "The AI service timed out. Please try again."}), 504
    except requests.exceptions.RequestException as e:
        logger.error("Upstream request failed: %s", e)
        return jsonify(error={"message": "Could not reach the AI service (bad gateway)."}), 502
    except Exception as e:  # noqa: BLE001 - top-level safety net, always return JSON
        logger.exception("Unexpected error in proxy_request")
        return jsonify(error={"message": f"Unexpected server error: {e}"}), 500


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR), "max_ai.html")


@app.route("/health")
def health():
    return jsonify(
        status="ok",
        time=time.time(),
        gemini_key_configured=bool(GEMINI_API_KEY),
        openai_key_configured=bool(OPENAI_API_KEY),
        anthropic_key_configured=bool(ANTHROPIC_API_KEY),
        ollama_url=OLLAMA_BASE_URL,
    )


@app.route("/api/ollama/tags")
def ollama_tags():
    try:
        upstream = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return (upstream.text, upstream.status_code, {"Content-Type": "application/json"})
    except requests.exceptions.Timeout:
        return jsonify(error={"message": "Ollama did not respond within 5 seconds."}), 504
    except requests.exceptions.RequestException:
        return jsonify(error={"message": "Ollama is not running. Start it with `ollama serve`."}), 503


@app.route("/api/ollama/chat", methods=["POST"])
def api_ollama_chat():
    try:
        body = request.get_json(force=True, silent=False)
        if not body or "payload" not in body:
            return jsonify(error={"message": "Request body must include a 'payload' field."}), 400
        upstream = call_ollama(body.get("model", ""), body["payload"])
        return (upstream.text, upstream.status_code, {"Content-Type": "application/json"})
    except ValueError as e:
        return jsonify(error={"message": str(e)}), 400
    except requests.exceptions.Timeout:
        return jsonify(error={"message": "Ollama timed out. Check that the model is available."}), 504
    except requests.exceptions.RequestException:
        return jsonify(error={"message": "Ollama is not running. Start it with `ollama serve`."}), 503
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error in api_ollama_chat")
        return jsonify(error={"message": f"Unexpected server error: {e}"}), 500


@app.route("/api/chat", methods=["POST"])
def api_chat():
    return proxy_request(default_model="gemini-3-flash-preview")


@app.route("/api/image", methods=["POST"])
def api_image():
    return proxy_request(default_model="gemini-3.1-flash-image")


@app.route("/api/tts", methods=["POST"])
def api_tts():
    return proxy_request(default_model="gemini-2.5-flash-preview-tts")


@app.route("/api/video", methods=["POST"])
def api_video():
    """Kick off a Veo video-generation job. Returns Google's long-running
    operation object (contains 'name'), which the frontend then polls."""
    return proxy_request(default_model="veo-3.1-generate-preview")


@app.route("/api/video/poll", methods=["POST"])
def api_video_poll():
    """Check the status of a previously started Veo operation."""
    try:
        body = request.get_json(force=True, silent=False)
        if not body or "operationName" not in body:
            return jsonify(error={"message": "Request body must include 'operationName'."}), 400
        if not GEMINI_API_KEY:
            return jsonify(error={"message": "GEMINI_API_KEY is not set on the server."}), 500

        op_name = str(body["operationName"]).lstrip("/")
        url = f"https://generativelanguage.googleapis.com/v1beta/{op_name}?key={GEMINI_API_KEY}"
        upstream = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        return (upstream.text, upstream.status_code, {"Content-Type": "application/json"})
    except requests.exceptions.Timeout:
        logger.error("Video status check timed out")
        return jsonify(error={"message": "Video status check timed out. Please try again."}), 504
    except requests.exceptions.RequestException as e:
        logger.error("Video poll upstream request failed: %s", e)
        return jsonify(error={"message": "Could not reach the AI service (bad gateway)."}), 502
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error in api_video_poll")
        return jsonify(error={"message": f"Unexpected server error: {e}"}), 500


@app.route("/api/video/fetch", methods=["POST"])
def api_video_fetch():
    """Stream a finished video's bytes back through the server, so the API
    key never has to be attached to a URL the browser calls directly."""
    try:
        body = request.get_json(force=True, silent=False)
        if not body or "fileUri" not in body:
            return jsonify(error={"message": "Request body must include 'fileUri'."}), 400
        if not GEMINI_API_KEY:
            return jsonify(error={"message": "GEMINI_API_KEY is not set on the server."}), 500

        file_uri = body["fileUri"]
        sep = "&" if "?" in file_uri else "?"
        upstream = requests.get(f"{file_uri}{sep}key={GEMINI_API_KEY}", timeout=REQUEST_TIMEOUT_SECONDS)
        content_type = upstream.headers.get("Content-Type", "video/mp4")
        return (upstream.content, upstream.status_code, {"Content-Type": content_type})
    except requests.exceptions.Timeout:
        logger.error("Video download timed out")
        return jsonify(error={"message": "Video download timed out. Please try again."}), 504
    except requests.exceptions.RequestException as e:
        logger.error("Video fetch upstream request failed: %s", e)
        return jsonify(error={"message": "Could not download the generated video (bad gateway)."}), 502
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error in api_video_fetch")
        return jsonify(error={"message": f"Unexpected server error: {e}"}), 500


@app.route("/api/openai", methods=["POST"])
def api_openai():
    """Proxy to OpenAI's Chat Completions API using a server-side key."""
    try:
        body = request.get_json(force=True, silent=False)
        if not body or "payload" not in body:
            return jsonify(error={"message": "Request body must include a 'payload' field."}), 400
        if not OPENAI_API_KEY:
            return jsonify(error={"message": "OPENAI_API_KEY is not set on the server. Set it as an environment variable before starting app.py."}), 500

        upstream = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=body["payload"],
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return (upstream.text, upstream.status_code, {"Content-Type": "application/json"})
    except requests.exceptions.Timeout:
        return jsonify(error={"message": "OpenAI request timed out."}), 504
    except requests.exceptions.RequestException as e:
        logger.error("OpenAI upstream request failed: %s", e)
        return jsonify(error={"message": "Could not reach OpenAI (bad gateway)."}), 502
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error in api_openai")
        return jsonify(error={"message": f"Unexpected server error: {e}"}), 500


@app.route("/api/anthropic", methods=["POST"])
def api_anthropic():
    """Proxy to Anthropic's Messages API using a server-side key."""
    try:
        body = request.get_json(force=True, silent=False)
        if not body or "payload" not in body:
            return jsonify(error={"message": "Request body must include a 'payload' field."}), 400
        if not ANTHROPIC_API_KEY:
            return jsonify(error={"message": "ANTHROPIC_API_KEY is not set on the server. Set it as an environment variable before starting app.py."}), 500

        upstream = requests.post(
            "https://api.anthropic.com/v1/messages",
            json=body["payload"],
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return (upstream.text, upstream.status_code, {"Content-Type": "application/json"})
    except requests.exceptions.Timeout:
        return jsonify(error={"message": "Anthropic request timed out."}), 504
    except requests.exceptions.RequestException as e:
        logger.error("Anthropic upstream request failed: %s", e)
        return jsonify(error={"message": "Could not reach Anthropic (bad gateway)."}), 502
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error in api_anthropic")
        return jsonify(error={"message": f"Unexpected server error: {e}"}), 500


# ---------------------------------------------------------------------------
# Error handlers — always return JSON, never a bare stack trace
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(_e):
    return jsonify(error={"message": "Route not found."}), 404


@app.errorhandler(405)
def method_not_allowed(_e):
    return jsonify(error={"message": "Method not allowed on this route."}), 405


@app.errorhandler(500)
def server_error(e):
    logger.exception("Unhandled server error: %s", e)
    return jsonify(error={"message": "Internal server error."}), 500


if __name__ == "__main__":
    if not GEMINI_API_KEY:
        logger.warning(
            "GEMINI_API_KEY is not set. The app will still serve the frontend, "
            "but /api/* routes will return an error until the key is configured. "
            "The frontend can still work in standalone mode (client-side key) instead."
        )
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
