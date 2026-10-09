"""
Central configuration for the Nocturna UTG assistant.

Secrets are read from environment variables rather than hard-coded, so the
project can be committed to version control (e.g. for your dissertation
appendix / GitHub repo) without leaking a live API key.

Before running, set:
    export OPENWEATHER_API_KEY="your_key_here"      # macOS/Linux
    setx OPENWEATHER_API_KEY "your_key_here"         # Windows

Or create a .env file and load it with python-dotenv if you prefer.
"""

import os

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

# Set this to a specific index (e.g. 19) if the OS default input device
# isn't the one you actually speak into -- common on machines with several
# audio devices (built-in mic, Bluetooth headset, etc.). Find the right
# number by running `python mic_test.py` (lists all devices) then
# `python mic_test.py <index>` to test each candidate. Leave as None to use
# whatever Windows/macOS/Linux considers the default.
MIC_DEVICE_INDEX = None

ASSISTANT_NAME = "Nocturna"
WAKE_GREETING = (
    "Hello, I'm Nocturna, your UTG student assistant. How can I help you today?"
)

# Which retrieval method the LIVE assistant (main.py / gui.py / app.py)
# uses: "keyword", "tfidf", or "embeddings". See retrieval_methods.py for
# what each one does. Run `python evaluate.py` first and set this to
# whichever one actually scored best on eval/test_set.json -- don't just
# assume the fanciest method wins; that's the whole point of evaluating.
RETRIEVAL_METHOD = "tfidf"

# Minimum similarity score (0-1) required before each method will answer a
# question rather than saying it doesn't know. Each method's scores aren't
# on a comparable scale (keyword overlap vs TF-IDF cosine vs embedding
# cosine behave differently), so each gets its own threshold rather than
# sharing one number.
#
# These starting values came from a small manual test (a handful of
# in-scope vs clearly-out-of-scope queries) -- NOT a proper validation set.
# `python evaluate.py` reports accuracy at these thresholds on your real
# test set; re-tune here based on those results and report the false
# accept/false reject trade-off in your results chapter.
RETRIEVAL_THRESHOLDS = {
    "keyword": 0.34,
    "tfidf": 0.45,
    "embeddings": 0.5,
}

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_DIR = os.path.join(_BASE_DIR, "notes")
LOG_PATH = os.path.join(_BASE_DIR, "logs", "interactions.csv")
KB_PATH = os.path.join(_BASE_DIR, "utg_knowledge.json")
