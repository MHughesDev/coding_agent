# SPEC.md — Local Queue Agent Supervisor

## 1. Purpose

This project is a local Python application that automates queue-driven coding work across one or more repositories that share the same queue contract.

The system is started manually by the developer from a shell or PowerShell command. Once started, it continuously performs ordered repo sweeps and launches a single coding harness execution when actionable queue work is found.

The design goal is simplicity, determinism, and architectural separation.

---

## 2. Core design goals

1. Use the developer's **existing local repo checkouts directly**
2. Avoid separate worktrees
3. Support one repo or many repos
4. Process queue items automatically
5. Run only **one active queue item at a time**
6. Keep the **coding harness logic isolated in `harness/`**
7. Keep scheduler/orchestration logic outside the harness
8. Sleep only after a **fully empty pass**
9. Make the harness logic easily replaceable later

---

## 3. System overview

The system consists of two main layers:

### 3.1 Orchestration layer
Responsible for:
- CLI input
- repo list management
- repo scanning
- queue discovery
- scheduling
- pass-level sleep logic
- lock lifecycle
- logging
- result routing

### 3.2 Harness layer
Responsible for:
- loading required repo and queue context
- selecting relevant files for the run
- interacting with the model provider
- planning
- execution
- validation
- structured run result output

The harness must be isolated in its own top-level folder:

- `harness/`

This isolation is a hard requirement.

---

## 4. Runtime model

## 4.1 Startup
The developer launches the application with:
- a single repo root path, or
- an ordered list of repo root paths

The application stores the repo list in the exact order provided.

## 4.2 Full pass
A **full pass** means visiting every configured repo once in order.

Example:

`repoA -> repoB -> repoC`

For each repo visit:
1. verify repo is valid
2. locate root-level `queue/`
3. locate `queue/queue.csv`
4. determine whether there is an actionable queue item
5. if none, record this repo as empty for the current pass
6. if one exists, process **one queue item only** for that repo visit

## 4.3 Pass completion rule
After the full pass finishes:

- if **all repos were empty**, the application sleeps for the configured sleep interval (default: 60 seconds)
- if **at least one repo had actionable work**, the application starts the next full pass immediately

This same rule applies when only one repo is configured.

---

## 5. Concurrency model

The system is intentionally single-runner.

### 5.1 Hard rules
- only one active queue item at a time
- only one active harness execution at a time
- no parallel repo processing
- no worker pools
- no background distributed coordination

### 5.2 Enforcement
The supervisor process is the primary enforcement boundary.

Internal runtime state must track:
- whether the system is idle or running
- active repo path
- active queue id
- active start time

---

## 6. Repo contract assumptions

The system assumes each target repo follows a shared queue layout.

Minimum expected files:
- `queue/queue.csv`
- `queue/QUEUE_INSTRUCTIONS.md`
- `queue/QUEUE_AGENT_PROMPT.md`
- `README.md`
- `docs/README.MD`
- `docs/AGENTS.MD`

The queue item contract is expected to be expressed in `queue.csv` with fields such as:
- id
- summary
- dependencies
- related_files
- notes

The exact queue schema may evolve, but the selector must be built to support the shared template queue model.

---

## 7. Queue processing behavior

## 7.1 Selection
The queue selector identifies the next actionable queue item for a repo.

Initial expected behavior:
- inspect `queue/queue.csv`
- determine the next open actionable item
- optionally validate dependencies if dependency handling is implemented

## 7.2 Processing scope
For each repo visit, process **at most one queue item**.

This is intentional and preserves fairness across multiple repos.

## 7.3 Local repo usage
The system operates directly against the developer's local repo checkout.

It must not create a separate worktree.

The runner may:
- create or switch to a branch in the same local repo
- read and write files in that same checkout
- update queue artifacts associated with the currently processed item

The user may append new rows to `queue.csv` while the application is running.

---

## 8. Lock model

## 8.1 Primary lock
The primary lock is the supervisor's own single-process runtime state.

## 8.2 Visible lock file
A repo-local visible lock file should be used:

- `queue/queue.lock`

Purpose:
- visibility
- crash recovery
- debugging

Recommended contents:
- repo path
- queue id
- started time
- status

The visible lock file is secondary to the supervisor's in-process state.

---

## 9. Required project structure

Recommended structure:

```text
project-root/
  README.MD
  AGENTS.md
  SPEC.md

  app/
    __init__.py
    main.py
    cli.py
    supervisor.py
    scheduler.py
    repo_scanner.py
    queue_selector.py
    locks.py
    state.py
    config.py
    logging_setup.py

  harness/
    __init__.py
    runner.py
    context_loader.py
    model_client.py
    planner.py
    executor.py
    validator.py
    result_types.py
    prompts/

  tests/
```

### Structural rule
Any logic specific to the coding harness must stay under `harness/`.

Changes to scheduling, scanning, and orchestration should not require editing harness internals, and changes to harness logic should not require rewriting the scheduler.

---

## 10. Module responsibilities

## 10.1 `app/main.py`
Application entry point.

Responsibilities:
- initialize config
- parse CLI
- start supervisor loop

## 10.2 `app/cli.py`
CLI contract.

Responsibilities:
- accept single repo or ordered repo list
- accept optional sleep interval
- accept optional run mode flags such as one-pass or dry-run

## 10.3 `app/supervisor.py`
Top-level runtime control.

Responsibilities:
- maintain idle/running state
- coordinate full passes
- invoke repo scanner and harness runner
- apply pass completion sleep rule

## 10.4 `app/scheduler.py`
Pass scheduling logic.

Responsibilities:
- ordered repo iteration
- full-pass bookkeeping
- empty-pass detection

## 10.5 `app/repo_scanner.py`
Repo discovery and queue path detection.

Responsibilities:
- validate repo root
- locate `queue/`
- locate `queue/queue.csv`
- return structured repo scan result

## 10.6 `app/queue_selector.py`
Queue item selection.

Responsibilities:
- read `queue.csv`
- identify next actionable item
- return structured queue item object

## 10.7 `app/locks.py`
Visible lock-file lifecycle.

Responsibilities:
- create lock file
- clear lock file
- inspect stale lock file state

## 10.8 `harness/runner.py`
Harness entry point.

Responsibilities:
- receive repo + queue item
- orchestrate context loading, planning, execution, and validation
- return structured run result

## 10.9 `harness/context_loader.py`
Context construction.

Responsibilities:
- read required repo docs
- read queue docs
- read queue item contract
- read related files
- optionally expand with adjacent files

## 10.10 `harness/model_client.py`
Model provider integration.

Responsibilities:
- call OpenAI-compatible endpoint
- encapsulate model request/response behavior
- isolate provider logic from scheduler

## 10.11 `harness/planner.py`
Planning phase.

Responsibilities:
- create structured plan
- identify likely files to change
- define validation targets

## 10.12 `harness/executor.py`
Execution phase.

Responsibilities:
- apply model-directed changes
- perform file edits
- manage execution steps

## 10.13 `harness/validator.py`
Validation phase.

Responsibilities:
- run repo validations
- collect command results
- report structured validation outcome

---

## 11. LLM integration

The harness must target an **OpenAI-compatible API interface**.

Configuration should include:
- `MODEL_BASE_URL`
- `MODEL_API_KEY`
- `MODEL_NAME`

Recommended default assumption:
- local OpenAI-compatible endpoint such as Ollama or similar

The scheduler must not depend directly on provider-specific semantics.

All provider-specific behavior must live inside `harness/model_client.py`.

---

## 12. Logging requirements

The application must log:

### 12.1 Global scheduler log
Include:
- startup
- pass start/end
- repo scan decisions
- whether pass was empty
- sleep / immediate rerun decisions

### 12.2 Per-run log
Include:
- repo
- queue id
- start time
- end time
- result
- validation status
- error or blocked reason if applicable

---

## 13. Result model

The harness should return a structured result enum / object, such as:
- success
- blocked
- failed
- skipped

Each result should include enough context for the supervisor to log and continue.

---

## 14. Failure handling

## 14.1 Missing repo artifacts
If repo or queue artifacts are missing:
- log
- treat repo as empty/unactionable for that pass

## 14.2 Harness failure
If harness run fails:
- log failure
- clear visible lock
- continue full-pass behavior

## 14.3 Crash recovery
On startup:
- inspect existing `queue/queue.lock`
- warn or clear if stale
- continue safely

---

## 15. Testing requirements

Minimum required tests:

1. repo rotation order is preserved
2. one full pass across multiple repos works correctly
3. sleep only occurs after a fully empty pass
4. immediate rerun occurs after any non-empty pass
5. only one active harness run is allowed
6. missing queue folder / queue file is handled safely
7. visible lock lifecycle behaves correctly

---

## 16. Explicit non-goals for MVP

The first implementation should **not** include:
- distributed multi-worker execution
- databases
- background services
- cross-machine coordination
- multiple active runs
- advanced queue orchestration
- repo worktrees
- heavy framework adoption

The MVP should stay simple and local.

---

## 17. Recommended implementation philosophy

- prioritize deterministic behavior
- prefer simplicity over cleverness
- isolate harness-specific logic in `harness/`
- keep orchestration logic clean and testable
- design for future harness replacement without rewriting the scheduler

