"""
Queue Runner for Aider
======================
Reads tasks from queue/queue.csv, executes each through a fresh Aider
subprocess, archives completed rows, and polls for new work.

Usage:
    python queue_runner.py                          # Run in current directory
    python queue_runner.py --repo C:\path\to\repo   # Target a specific repo
    python queue_runner.py --once                   # Process queue once, then exit
    python queue_runner.py --dry-run                # Show what would run, don't execute
"""

import csv
import io
import os
import shutil
import subprocess
import sys
import time
import argparse
import signal
import logging
from datetime import datetime
from pathlib import Path

import config

# ──────────────────────────────────────────────
# GLOBALS
# ──────────────────────────────────────────────
SHUTDOWN_REQUESTED = False

CSV_COLUMNS = [
    "id", "batch", "phase", "category", "summary",
    "agent_instructions", "constraints", "dependencies",
    "related_files", "notes", "created_date",
]

ARCHIVE_COLUMNS = CSV_COLUMNS + ["completed_date", "exit_code", "duration_seconds"]


def setup_signal_handlers():
    """Graceful shutdown on Ctrl+C or SIGTERM."""
    def handler(signum, frame):
        global SHUTDOWN_REQUESTED
        SHUTDOWN_REQUESTED = True
        logging.info("Shutdown requested. Finishing current task...")

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def setup_logging(log_dir: Path):
    """Configure logging to console and a daily rotating log file."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"runner_{datetime.now().strftime('%Y-%m-%d')}.log"

    handlers = [logging.FileHandler(log_file, encoding="utf-8")]
    if config.LOG_TO_CONSOLE:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt=config.LOG_DATE_FORMAT,
        handlers=handlers,
    )


# ──────────────────────────────────────────────
# OLLAMA MANAGEMENT
# ──────────────────────────────────────────────
def is_ollama_running() -> bool:
    """Check if Ollama is responding on its API port."""
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{config.OLLAMA_BASE_URL}/api/tags",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=config.OLLAMA_HEALTH_TIMEOUT):
            return True
    except Exception:
        return False


def ensure_ollama():
    """Start Ollama if it's not already running."""
    if is_ollama_running():
        logging.info("Ollama is running.")
        return True

    logging.info("Ollama not detected. Attempting to start...")

    # Try starting ollama serve in background
    try:
        if sys.platform == "win32":
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except FileNotFoundError:
        logging.error("'ollama' not found in PATH. Install Ollama first.")
        return False

    # Wait for it to come up
    logging.info(f"Waiting {config.OLLAMA_STARTUP_WAIT}s for Ollama to start...")
    for i in range(config.OLLAMA_STARTUP_WAIT):
        time.sleep(1)
        if is_ollama_running():
            logging.info(f"Ollama started after {i + 1}s.")
            return True

    logging.error("Ollama failed to start within timeout.")
    return False


# ──────────────────────────────────────────────
# CSV OPERATIONS
# ──────────────────────────────────────────────
def read_queue(queue_path: Path) -> list[dict]:
    """Read queue.csv and return list of row dicts."""
    if not queue_path.exists():
        logging.error(f"Queue file not found: {queue_path}")
        return []

    try:
        with open(queue_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        return rows
    except Exception as e:
        logging.error(f"Failed to read queue: {e}")
        return []


def get_pending_tasks(rows: list[dict]) -> list[dict]:
    """Return all rows above the sentinel."""
    pending = []
    for row in rows:
        if row.get("id", "").strip().upper() == config.SENTINEL_ID:
            break
        pending.append(row)
    return pending


def archive_task(task: dict, queue_path: Path, archive_path: Path,
                 exit_code: int, duration: float):
    """Remove task from queue.csv and append to queue_archived.csv."""
    task_id = task["id"]

    # --- Remove from queue.csv ---
    rows = read_queue(queue_path)
    remaining = [r for r in rows if r.get("id", "").strip() != task_id]

    with open(queue_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in remaining:
            # Only write the standard columns
            filtered = {k: row.get(k, "") for k in CSV_COLUMNS}
            writer.writerow(filtered)

    # --- Append to archive ---
    archive_exists = archive_path.exists() and archive_path.stat().st_size > 0

    archive_row = {k: task.get(k, "") for k in CSV_COLUMNS}
    archive_row["completed_date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    archive_row["exit_code"] = str(exit_code)
    archive_row["duration_seconds"] = str(int(duration))

    with open(archive_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ARCHIVE_COLUMNS)
        if not archive_exists:
            writer.writeheader()
        writer.writerow(archive_row)

    logging.info(f"Task [{task_id}] archived (exit_code={exit_code}, "
                 f"duration={int(duration)}s)")


# ──────────────────────────────────────────────
# PROMPT BUILDING
# ──────────────────────────────────────────────
def build_prompt(task: dict) -> str:
    """Assemble a structured prompt from the task's CSV columns."""
    sections = []

    sections.append(f"# Task: {task.get('summary', 'No summary')}")
    sections.append("")

    if task.get("agent_instructions", "").strip():
        sections.append("## Instructions")
        sections.append(task["agent_instructions"].strip())
        sections.append("")

    if task.get("constraints", "").strip():
        sections.append("## Constraints")
        sections.append(task["constraints"].strip())
        sections.append("")

    if task.get("dependencies", "").strip():
        sections.append("## Dependencies")
        sections.append(task["dependencies"].strip())
        sections.append("")

    if task.get("notes", "").strip():
        sections.append("## Notes")
        sections.append(task["notes"].strip())
        sections.append("")

    sections.append("## Execution Rules")
    sections.append("- Make all changes requested above.")
    sections.append("- Do not modify files outside the scope of this task.")
    sections.append("- If a file does not exist and needs to be created, create it.")
    sections.append("- If you cannot complete the task, make as much progress as possible.")

    return "\n".join(sections)


def get_context_files(queue_dir: Path) -> list[Path]:
    """Gather all docs and skill files for --read context."""
    context_files = []

    docs_dir = queue_dir / config.DOCS_DIR
    skills_dir = queue_dir / config.SKILLS_DIR

    for d in [docs_dir, skills_dir]:
        if d.exists():
            for f in sorted(d.rglob("*")):
                if f.is_file() and f.suffix in (".md", ".txt", ".yaml", ".yml", ".json"):
                    context_files.append(f)

    return context_files


def get_related_files(task: dict, repo_root: Path) -> list[Path]:
    """Parse the related_files column into a list of file paths."""
    raw = task.get("related_files", "").strip()
    if not raw:
        return []

    files = []
    # Support both semicolons and commas as separators
    separators = ";" if ";" in raw else ","
    for part in raw.split(separators):
        part = part.strip()
        if not part:
            continue
        p = repo_root / part
        if p.exists():
            files.append(p)
        else:
            logging.warning(f"Related file not found: {p}")
    return files


# ──────────────────────────────────────────────
# AIDER EXECUTION
# ──────────────────────────────────────────────
def run_aider(task: dict, repo_root: Path, queue_dir: Path,
              dry_run: bool = False) -> tuple[int, str, float]:
    """
    Execute a single Aider session for one task.
    Returns (exit_code, output, duration_seconds).
    """
    task_id = task["id"]
    tmp_dir = queue_dir / config.TMP_DIR
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Write prompt to temp file
    prompt_text = build_prompt(task)
    prompt_file = tmp_dir / f"prompt_{task_id}_{int(time.time())}.md"
    prompt_file.write_text(prompt_text, encoding="utf-8")

    # Build command
    cmd = [
        "aider",
        "--model", config.AIDER_MODEL,
        "--message-file", str(prompt_file),
    ]

    # Add extra flags from config
    cmd.extend(config.AIDER_EXTRA_FLAGS)

    # Add related files as editable files
    related = get_related_files(task, repo_root)
    for f in related:
        cmd.extend(["--file", str(f)])

    # Add context files as read-only
    context_files = get_context_files(queue_dir)
    for f in context_files:
        cmd.extend(["--read", str(f)])

    # Log what we're about to do
    logging.info(f"{'[DRY RUN] ' if dry_run else ''}Task [{task_id}]: {task.get('summary', '')}")
    logging.info(f"  Prompt file: {prompt_file}")
    logging.info(f"  Related files: {[str(f) for f in related]}")
    logging.info(f"  Context files: {len(context_files)} loaded")
    logging.info(f"  Command: {' '.join(cmd)}")

    if dry_run:
        # Clean up temp file
        prompt_file.unlink(missing_ok=True)
        return 0, "[dry run - no execution]", 0.0

    # Execute
    env = os.environ.copy()
    env["OLLAMA_API_BASE"] = config.OLLAMA_BASE_URL

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour max per task
        )
        duration = time.time() - start_time
        output = result.stdout + "\n" + result.stderr
        exit_code = result.returncode

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        output = "TIMEOUT: Task exceeded 1 hour limit."
        exit_code = -1
        logging.error(f"Task [{task_id}] timed out after {int(duration)}s")

    except Exception as e:
        duration = time.time() - start_time
        output = f"EXCEPTION: {str(e)}"
        exit_code = -2
        logging.error(f"Task [{task_id}] failed with exception: {e}")

    # Write task-specific log
    log_dir = queue_dir / config.LOGS_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    task_log = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}_{task_id}.log"

    log_content = [
        f"Task ID: {task_id}",
        f"Summary: {task.get('summary', '')}",
        f"Started: {datetime.fromtimestamp(start_time).strftime(config.LOG_DATE_FORMAT)}",
        f"Duration: {int(duration)}s",
        f"Exit Code: {exit_code}",
        f"",
        f"{'='*60}",
        f"PROMPT:",
        f"{'='*60}",
        prompt_text,
        f"",
        f"{'='*60}",
        f"AIDER OUTPUT:",
        f"{'='*60}",
        output,
    ]
    task_log.write_text("\n".join(log_content), encoding="utf-8")

    # Clean up temp prompt file
    prompt_file.unlink(missing_ok=True)

    return exit_code, output, duration


# ──────────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────────
def process_queue(repo_root: Path, once: bool = False, dry_run: bool = False):
    """Main processing loop."""
    queue_dir = repo_root / config.QUEUE_DIR
    queue_path = queue_dir / config.QUEUE_CSV
    archive_path = queue_dir / config.ARCHIVE_CSV

    # Validate queue exists
    if not queue_path.exists():
        logging.error(f"Queue file not found: {queue_path}")
        logging.error("Run this script from your repo root, or use --repo <path>")
        sys.exit(1)

    logging.info(f"Queue Runner started")
    logging.info(f"  Repo: {repo_root}")
    logging.info(f"  Queue: {queue_path}")
    logging.info(f"  Model: {config.AIDER_MODEL}")
    logging.info(f"  Mode: {'once' if once else 'continuous'} | "
                 f"{'dry-run' if dry_run else 'live'}")
    logging.info("")

    while not SHUTDOWN_REQUESTED:
        # Check Ollama before each task
        if not dry_run and not ensure_ollama():
            logging.error("Ollama unavailable. Retrying in 60s...")
            time.sleep(config.POLL_INTERVAL_SECONDS)
            continue

        # Read queue
        rows = read_queue(queue_path)
        if not rows:
            logging.error("Queue file is empty or unreadable.")
            if once:
                break
            time.sleep(config.POLL_INTERVAL_SECONDS)
            continue

        # Get pending tasks
        pending = get_pending_tasks(rows)

        if not pending:
            logging.info(f"Queue empty. Polling in {config.POLL_INTERVAL_SECONDS}s...")
            if once:
                logging.info("--once flag set. Exiting.")
                break
            time.sleep(config.POLL_INTERVAL_SECONDS)
            continue

        # Take the first task
        task = pending[0]
        task_id = task.get("id", "UNKNOWN")

        logging.info(f"{'='*60}")
        logging.info(f"Processing task [{task_id}]: {task.get('summary', '')}")
        logging.info(f"Queue depth: {len(pending)} task(s) remaining")
        logging.info(f"{'='*60}")

        # Execute
        exit_code, output, duration = run_aider(task, repo_root, queue_dir, dry_run)

        # Archive
        if not dry_run:
            archive_task(task, queue_path, archive_path, exit_code, duration)
        else:
            logging.info(f"[DRY RUN] Would archive task [{task_id}]")

        # Log result
        status = "COMPLETED" if exit_code == 0 else f"FAILED (exit={exit_code})"
        logging.info(f"Task [{task_id}] {status} in {int(duration)}s")
        logging.info("")

        if SHUTDOWN_REQUESTED:
            break

    logging.info("Queue Runner stopped.")


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Queue Runner for Aider — process coding tasks sequentially",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=".",
        help="Path to the git repository (default: current directory)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process all pending tasks then exit (no polling)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would run without executing Aider",
    )

    args = parser.parse_args()
    repo_root = Path(args.repo).resolve()

    if not (repo_root / ".git").exists():
        logging.warning(f"No .git directory found in {repo_root}. "
                        f"Aider requires a git repo.")

    # Setup
    queue_dir = repo_root / config.QUEUE_DIR
    setup_logging(queue_dir / config.LOGS_DIR)
    setup_signal_handlers()

    # Run
    process_queue(repo_root, once=args.once, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
