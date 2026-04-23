# AGENTS.md — Instructions for agents working on this project

## Purpose

This repository contains a Python application that automatically processes queue-driven coding work across one or more local repositories.

The architecture intentionally separates the system into:
- orchestration logic
- harness logic

The most important architectural rule is that **harness-specific coding-runner logic must remain isolated under `harness/`**.

---

## Mandatory reads before making changes

Read these first:

1. `README.MD`
2. `SPEC.md`
3. this file (`AGENTS.md`)

Do not begin implementation changes before reading them.

---

## Non-negotiable architecture rule

The `harness/` folder exists so the coding harness can be modified later without forcing changes to the rest of the system.

That means:

- scheduler logic should not be implemented inside `harness/`
- repo scanning should not be implemented inside `harness/`
- queue rotation / sleep logic should not be implemented inside `harness/`
- lock lifecycle should not be implemented inside `harness/`

`harness/` should contain only logic directly related to:
- building run context
- interacting with the model
- planning
- execution
- validation
- structured run results

If you are changing scheduler or orchestration behavior, prefer editing code under `app/`.

If you are changing agent reasoning / context loading / model behavior, prefer editing code under `harness/`.

---

## Project intent

This application is intentionally:
- local
- single-process
- deterministic
- non-parallel
- easy to reason about

Do not turn the MVP into a distributed system.

Do not add unnecessary complexity.

---

## Scheduler rules to preserve

These are core requirements and should not be changed casually:

1. repos are visited in the exact order given by the user
2. a full pass means visiting every repo once
3. only one queue item is processed at a time
4. only one harness execution is active at a time
5. after a full pass:
   - if all repos were empty, sleep
   - if any repo had work, rerun immediately
6. the system uses the user's existing local repo checkout directly
7. no separate worktrees are created

---

## Code organization expectations

Preferred structure:

```text
app/
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
  runner.py
  context_loader.py
  model_client.py
  planner.py
  executor.py
  validator.py
  result_types.py
```

You may refine internals, but preserve the separation of concerns.

---

## Implementation preferences

- use Python type hints
- use dataclasses where helpful
- keep functions small and readable
- prefer standard library unless a dependency is justified
- isolate side effects
- keep scheduler logic testable
- keep harness logic swappable

---

## Logging expectations

Changes should preserve or improve:
- global scheduler logging
- per-run logging
- understandable failure messages
- clear repo / queue id traceability

---

## Testing expectations

When changing scheduler or orchestration logic, update or add tests for:
- repo rotation
- empty-pass sleep behavior
- immediate rerun after non-empty pass
- single active run enforcement
- lock lifecycle
- missing queue artifacts

When changing harness logic, update or add tests for:
- context assembly
- model call boundaries
- structured result behavior
- validation step routing

---

## Avoid these mistakes

Do not:
- mix harness logic into scheduler modules
- hide scheduling behavior inside the model client
- introduce parallel workers into the MVP
- add worktree management
- make the repo scanner dependent on LLM logic
- make the harness directly control the outer scheduling loop

---

## Preferred development mindset

Make the smallest clean change that preserves the architecture.

If a new feature seems to require touching both `app/` and `harness/`, first ask:
- is this truly a boundary concern, or
- am I violating the separation that this project is designed around?

Default to preserving the separation.
