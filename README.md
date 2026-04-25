# Queue Runner for Aider

A local automation system that processes coding tasks from a CSV queue through Aider, one at a time, with fresh context per task.

## Quick Start

```
1. Copy the queue/ folder into your repo
2. Edit queue/queue.csv with your tasks
3. Run: start.bat C:\path\to\your\repo --dry-run    (test first)
4. Run: start.bat C:\path\to\your\repo               (live)
```

## How It Works

1. Reads the first pending row from `queue/queue.csv`
2. Builds a prompt from the row's columns
3. Loads all files from `queue/docs/` and `queue/skills/` as read-only context
4. Spawns a fresh Aider subprocess (clean context window every time)
5. Waits for Aider to finish
6. Moves the completed row to `queue/queue_archived.csv`
7. Loops back to step 1
8. When the queue is empty, polls every 60 seconds for new tasks

## File Structure

```
your-repo/
├── queue/
│   ├── queue.csv              <- Pending tasks + sentinel row
│   ├── queue_archived.csv     <- Completed tasks with timestamps
│   ├── docs/                  <- Reference docs (read-only context)
│   ├── skills/                <- Skill files (read-only context)
│   ├── logs/                  <- Execution logs per task
│   └── tmp/                   <- Temp prompt files (auto-cleaned)
└── ...your code...
```

## Queue CSV Format

```csv
id,batch,phase,category,summary,agent_instructions,constraints,dependencies,related_files,notes,created_date
```

| Column              | Purpose                                           |
|---------------------|---------------------------------------------------|
| id                  | Unique task identifier (e.g., TASK-001)           |
| batch               | Group number for organizational use               |
| phase               | Phase/priority within a batch                     |
| category            | Task type (refactor, bugfix, feature, test, etc.) |
| summary             | One-line description of the task                  |
| agent_instructions  | Detailed instructions for the AI agent            |
| constraints         | Rules the agent must follow                       |
| dependencies        | IDs of tasks that should run first (informational)|
| related_files       | Semicolon-separated file paths to edit            |
| notes               | Additional context                                |
| created_date        | When the task was created                         |

### The Sentinel Row

The last row in queue.csv must always be:

```csv
END,0,0,sentinel,NO_MORE_TASKS,STOP,,,,,2026-01-01
```

This tells the runner the queue is empty. Never delete this row.

### related_files Format

Use semicolons to separate multiple files:

```
src/main.py;src/utils.py;tests/test_main.py
```

Paths are relative to the repo root.

## Commands

### Test without executing (see what would happen)

```
start.bat C:\Users\Mason\Desktop\coding_projects\coding_agent --dry-run
```

### Process all tasks then exit

```
start.bat C:\Users\Mason\Desktop\coding_projects\coding_agent --once
```

### Run continuously (polls for new tasks)

```
start.bat C:\Users\Mason\Desktop\coding_projects\coding_agent
```

### Run in background (no console window)

```
start_headless.bat C:\Users\Mason\Desktop\coding_projects\coding_agent
```

### Stop the runner

```
stop.bat
```

## Configuration

Edit `config.py` to change:

- **AIDER_MODEL** — which Ollama model to use
- **POLL_INTERVAL_SECONDS** — how often to check for new tasks (default: 60)
- **AIDER_EXTRA_FLAGS** — additional flags for every Aider call
- **OLLAMA_BASE_URL** — where Ollama is listening

## Logs

Each task creates a log file in `queue/logs/`:

```
queue/logs/2026-04-25_TASK-001.log
```

The daily runner log is:

```
queue/logs/runner_2026-04-25.log
```

## Adding Tasks While Running

You can add new rows to `queue.csv` while the runner is active.
Insert them above the sentinel row. The runner re-reads the file
before each task, so new tasks are picked up automatically.

## Error Handling

- If a task fails, it is still archived but with a non-zero exit_code
- If Ollama is not running, the runner starts it automatically
- If Ollama cannot start, the runner retries every 60 seconds
- Each task has a 1-hour timeout
- Ctrl+C gracefully stops after the current task finishes

## Tips

- Start with `--dry-run` to verify your queue before running live
- Keep `agent_instructions` detailed — the model is 7-9B, be explicit
- Put coding standards in `queue/skills/` so every task follows them
- Check `queue/logs/` after each run to review what the agent did
- Use `git log` to see all auto-committed changes
- Use `git revert <hash>` to undo any bad changes
