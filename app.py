"""
Web UI for Nocturna, built with Flask.

Run with:
    python app.py
Then open http://127.0.0.1:5000 in your browser.

This runs entirely on your own machine -- it is NOT exposed to the internet.
The browser only renders the interface; listening and speaking both still
happen locally through speech_io (same microphone/speakers as main.py and
gui.py). No assistant logic is duplicated here -- this calls the exact same
speech_io.listen() and main.respond() functions.
"""

from flask import Flask, jsonify, render_template, request

import main as assistant
import reminders
import speech_io

app = Flask(__name__)

# Captures whatever speech_io.speak() says during one request, so the
# response can be sent back to the browser as text alongside being spoken
# out loud through your speakers as usual.
_last_spoken = []


def _capture_speech(text: str) -> None:
    _last_spoken.append(text)


speech_io.register_listener(_capture_speech)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/listen", methods=["POST"])
def api_listen():
    """Triggers the microphone, same as pressing nothing and just talking
    in the CLI version. Blocks until speech_io.listen() returns."""
    _last_spoken.clear()
    voice_data = speech_io.listen()
    if not voice_data:
        return jsonify({"you": None, "assistant": list(_last_spoken)})
    assistant.respond(voice_data)
    return jsonify({"you": voice_data, "assistant": list(_last_spoken)})


@app.route("/api/due_reminders")
def api_due_reminders():
    """Called once when the page loads to surface any reminders due today
    or overdue -- the browser equivalent of main.py's startup announcement."""
    due = reminders.get_due_reminders()
    messages = []
    for r in due:
        text = f"Reminder: {r['description']} (due {r['due_date']})"
        speech_io.speak(text)  # also spoken aloud, consistent with the rest of the assistant
        messages.append(text)
    return jsonify({"due": messages})


@app.route("/api/ask", methods=["POST"])
def api_ask():
    """Text fallback -- same pipeline as speech, skipping the microphone.
    Useful for demos where mic reliability isn't the point, or for quickly
    testing knowledge-base answers while you're tuning utg_knowledge.json."""
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip().lower()
    if not text:
        return jsonify({"you": None, "assistant": []})
    _last_spoken.clear()
    assistant.respond(text)
    return jsonify({"you": text, "assistant": list(_last_spoken)})


if __name__ == "__main__":
    # threaded=False on purpose: the microphone is a single shared resource,
    # so we don't want two /api/listen requests racing to open it at once.
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=False)
