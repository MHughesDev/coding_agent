"""
Queue Runner Configuration
Edit these values to match your local setup.
"""

from pathlib import Path

# ──────────────────────────────────────────────
# MODEL & AIDER
# ──────────────────────────────────────────────
AIDER_MODEL = "ollama_chat/qwen3.5:9b"
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OLLAMA_PROCESS_NAME = "ollama.exe"

# Extra flags passed to every aider invocation
AIDER_EXTRA_FLAGS = [
    "--yes",
    "--auto-commits",
    "--no-stream",
    "--no-show-model-warnings",
    "--no-gitignore",
]

# ──────────────────────────────────────────────
# QUEUE PATHS (relative to the repo root)
# ──────────────────────────────────────────────
QUEUE_DIR = "queue"
QUEUE_CSV = "queue.csv"
ARCHIVE_CSV = "queue_archived.csv"
DOCS_DIR = "docs"
SKILLS_DIR = "skills"
LOGS_DIR = "logs"
TMP_DIR = "tmp"

# ──────────────────────────────────────────────
# SENTINEL
# ──────────────────────────────────────────────
SENTINEL_ID = "END"

# ──────────────────────────────────────────────
# TIMING
# ──────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 60
OLLAMA_STARTUP_WAIT = 15
OLLAMA_HEALTH_TIMEOUT = 5

# ──────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────
LOG_TO_CONSOLE = True
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
