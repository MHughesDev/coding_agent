# Queue Supervisor — Remaining Work Plan (High-Level)

This document maps what is still needed to take the current MVP toward a robust queue-driven local coding supervisor.

> Scope note: this is intentionally high-level planning, not implementation detail.

---

## Phase documents

Each phase has a dedicated planning file that expands scope, dependencies, risks, and exit criteria:

- [Phase 1 — Queue Contract Hardening](./PHASE_1_QUEUE_CONTRACT_HARDENING.md)
- [Phase 2 — Queue State Transitions & Persistence](./PHASE_2_QUEUE_STATE_TRANSITIONS_PERSISTENCE.md)
- [Phase 3 — Locking & Recovery Maturity](./PHASE_3_LOCKING_RECOVERY_MATURITY.md)
- [Phase 4 — Harness Capability Upgrade](./PHASE_4_HARNESS_CAPABILITY_UPGRADE.md)
- [Phase 5 — Repo & Runtime Robustness](./PHASE_5_REPO_RUNTIME_ROBUSTNESS.md)
- [Phase 6 — Observability & Operator UX](./PHASE_6_OBSERVABILITY_OPERATOR_UX.md)
- [Phase 7 — Configuration & Provider Flexibility](./PHASE_7_CONFIGURATION_PROVIDER_FLEXIBILITY.md)
- [Phase 8 — Test & Quality Expansion](./PHASE_8_TEST_QUALITY_EXPANSION.md)
- [Phase 9 — Documentation & Operational Readiness](./PHASE_9_DOCUMENTATION_OPERATIONAL_READINESS.md)

---

## Current baseline (what already exists)

- Deterministic single-process scheduler loop.
- Ordered full-pass scanning across repos.
- One queue item per repo visit.
- Empty-pass sleep / non-empty immediate rerun behavior.
- Basic queue selection (`open/todo/ready/queued`) with simple dependency checks.
- Visible `queue/queue.lock` lifecycle.
- Harness boundary (`harness/`) with context loading + OpenAI-compatible model client.
- Basic automated tests for core scheduler behaviors.

---

## Phase 1 — Queue Contract Hardening

Goal: ensure queue parsing/selection is resilient and predictable across real-world queue files.

### 1.1 Queue schema and validation
- Define required and optional queue columns explicitly.
- Add queue contract validation with clear errors/warnings.
- Add graceful handling for malformed CSV rows and mixed casing.

### 1.2 Actionability semantics
- Formalize status lifecycle (e.g., `open`, `in_progress`, `blocked`, `done`, `failed`).
- Define deterministic tie-break behavior when multiple items are eligible.
- Clarify behavior for missing IDs, duplicates, and invalid dependencies.

### 1.3 Dependency model
- Support richer dependency formats (comma/semicolon/whitespace robustly).
- Detect cycles and unresolved references.
- Standardize blocked-item reporting.

---

## Phase 2 — Queue State Transitions & Persistence

Goal: make queue progression visible and durable as work is executed.

### 2.1 Status updates during run lifecycle
- Mark selected item as `in_progress` when a run starts.
- Mark item to terminal state on completion (`done`/`failed`/`blocked`).
- Persist timestamps and run metadata in queue artifacts.

### 2.2 Atomicity and safety
- Prevent partial/corrupt writes to `queue.csv`.
- Define behavior for mid-run crashes and restart recovery.
- Ensure lock + queue status stay consistent under failure.

### 2.3 Idempotent resumption
- Define restart behavior for stale `in_progress` items.
- Add policy for retry attempts and backoff.

---

## Phase 3 — Locking & Recovery Maturity

Goal: improve observability and crash recovery around `queue.lock`.

### 3.1 Stale lock detection
- Detect stale lock based on timestamps / ownership metadata.
- Define cleanup policy for stale lock files.

### 3.2 Lock metadata enrichment
- Include pass ID, process ID, host/user, and heartbeat metadata.
- Add lock inspection diagnostics for operators.

### 3.3 Recovery workflows
- Define explicit restart procedures after abrupt termination.
- Ensure resumed runs cannot violate single-active-run guarantees.

---

## Phase 4 — Harness Capability Upgrade

Goal: move from skeleton/no-op harness behavior to practical autonomous execution.

### 4.1 Planning quality
- Improve prompt/context packaging for predictable planning.
- Add structured plan representation with explicit step statuses.

### 4.2 Execution behavior
- Replace no-op executor with real file-change workflow.
- Add boundaries/guardrails for allowed paths and operations.
- Add repo-aware change summaries.

### 4.3 Validation routing
- Route validation commands based on repo type (Python/JS/etc).
- Capture validation output and classify failures.
- Feed validation result back into queue status transitions.

---

## Phase 5 — Repo & Runtime Robustness

Goal: improve correctness and operability across multiple repositories.

### 5.1 Repo discovery hardening
- Tighten project-root checks and explicit repo readiness diagnostics.
- Handle missing docs/prompts as warnings with fallback policy.

### 5.2 Runtime controls
- Add run limits / max-pass options for controlled execution windows.
- Add graceful shutdown behavior while preserving queue integrity.

### 5.3 Fairness and starvation checks
- Verify long-running repo patterns do not starve other repos.
- Add telemetry to monitor per-repo throughput and wait time.

---

## Phase 6 — Observability & Operator UX

Goal: make runtime behavior easier to inspect and troubleshoot.

### 6.1 Structured logging
- Standardize log event schema (pass, repo, queue_id, duration, outcome).
- Emit machine-readable logs option (JSON lines).

### 6.2 Run artifacts
- Persist per-run summaries and transcripts in `queue/runs/`.
- Add human-readable failure reports with next actions.

### 6.3 Health and diagnostics
- Add lightweight status command/report for active state, last pass, and errors.

---

## Phase 7 — Configuration & Provider Flexibility

Goal: make behavior configurable without code edits.

### 7.1 Config model expansion
- Add config file support (while preserving env vars and CLI precedence).
- Validate config at startup with actionable feedback.

### 7.2 Model-provider abstraction maturity
- Expand provider options for OpenAI-compatible backends.
- Add timeout/retry policies and clear error classifications.

### 7.3 Prompt/config isolation
- Make prompt selection/versioning explicit and configurable.

---

## Phase 8 — Test & Quality Expansion

Goal: protect behavior through comprehensive automated coverage.

### 8.1 Queue parsing/state tests
- Malformed CSV cases, duplicate IDs, dependency failures, cycle cases.
- Queue status transition and recovery-path tests.

### 8.2 Supervisor integration tests
- Multi-repo long-pass simulation with mixed outcomes.
- Crash/restart and stale-lock behavior.

### 8.3 Harness boundary tests
- Model call error boundaries, context-size limits, and result contract stability.

---

## Phase 9 — Documentation & Operational Readiness

Goal: make adoption and maintenance straightforward.

### 9.1 Docs updates
- Update README/SPEC with exact queue lifecycle semantics.
- Add operator runbook (startup, recovery, troubleshooting).

### 9.2 Contribution guidance
- Clarify where orchestration changes vs harness changes belong.
- Add coding/testing checklist for queue-related changes.

### 9.3 Release readiness
- Define MVP exit criteria and production-readiness checklist.

---

## Cross-Phase Principles (must remain true)

- Keep orchestration concerns in `app/` and harness concerns in `harness/`.
- Preserve deterministic, single-process, one-active-run behavior.
- Continue using local repo checkouts directly (no worktrees).
- Keep behavior explicit, observable, and testable.
