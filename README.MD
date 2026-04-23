# README.MD — Local Queue Agent Supervisor

## What this is

This project is a local Python application that automatically processes queue-driven coding work across one or more repositories that share the same queue contract.

It is designed to work with repos that follow the same queue structure as the user's template project.

The application:
- runs locally
- uses your existing local repo checkouts directly
- does **not** create separate worktrees
- scans repos in order
- processes queue items automatically
- only sleeps after a **fully empty pass**

---

## Core behavior

You start the app manually with one repo path or an ordered list of repo paths.

The application performs a **full pass** across the repo list:

`repoA -> repoB -> repoC -> ...`

For each repo:
- look for a root-level `queue/`
- look for `queue/queue.csv`
- if the queue has actionable work, process **one queue item**
- if not, skip it for the current pass

After the full pass:
- if **every repo was empty**, wait 60 seconds
- if **any repo had work**, immediately start the next full pass

This means the app continuously sweeps as long as work exists anywhere.

---

## Most important design rule

The coding-runner-specific logic is isolated in:

- `harness/`

This is intentional.

The goal is to make it easy to change or upgrade the coding harness later without rewriting the scheduler, repo scanning, or orchestration system.

---

## Recommended project layout

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

---

## Usage

### Single repo

```powershell
python -m app.main --repo "C:\\dev\\ego-app"
```

### Multiple repos

```powershell
python -m app.main --repos "C:\\dev\\ego-app" "C:\\dev\\mind-map" "C:\\dev\\template"
```

### Optional sleep override

```powershell
python -m app.main --repos "C:\\dev\\ego-app" "C:\\dev\\mind-map" --sleep-seconds 60
```

---

## Repo assumptions

Each target repo should contain:

- `README.md`
- `docs/README.MD`
- `docs/AGENTS.MD`
- `queue/`
- `queue/queue.csv`
- `queue/QUEUE_INSTRUCTIONS.md`
- `queue/QUEUE_AGENT_PROMPT.md`

The queue file is treated as the source of actionable work.

---

## Local repo usage

This system works directly in your local checkout.

That means:
- no separate worktrees
- no shadow clones
- no background distributed worker farm

The harness may create or switch to a branch in the same local repo, but it uses the repo you pointed it at.

---

## Locking

The scheduler is single-runner by design.

There is only one active queue item at a time.

For visibility, the application may also create:

- `queue/queue.lock`

This file is for visibility and crash recovery, while the real enforcement is the supervisor's single-process runtime state.

---

## Model configuration

The harness should use an OpenAI-compatible model endpoint.

Recommended environment variables:

- `MODEL_BASE_URL`
- `MODEL_API_KEY`
- `MODEL_NAME`

Example local usage may target Ollama or another OpenAI-compatible server.

Keep provider-specific behavior isolated inside `harness/model_client.py`.

---

## Development goals

The MVP should prioritize:
- correctness
- deterministic scheduling
- clean separation of concerns
- easy future modification of the harness logic

Avoid overengineering the first version.

---

## Testing priorities

At minimum, test:
- repo rotation order
- full-pass behavior
- empty-pass sleep rule
- immediate rerun after non-empty pass
- one-active-run-only behavior
- missing queue file handling
- lock lifecycle behavior

---

## Related docs

- `SPEC.md` — formal system specification
- `AGENTS.md` — instructions for agents modifying this repo

