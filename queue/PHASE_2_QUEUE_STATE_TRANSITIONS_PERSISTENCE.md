# Phase 2 — Queue State Transitions & Persistence

Parent roadmap: `queue/PLAN.md`.

## Why this phase exists

Selection logic without durable transitions leads to repeated selection and poor operator visibility. This phase turns queue processing into an auditable lifecycle.

## Primary outcome

Each run has explicit, persistent queue-state transitions that survive process boundaries and failure conditions.

## In-scope workstreams

1. **Lifecycle transition model**
   - Define legal transitions (e.g., `open -> in_progress -> done|failed|blocked`).
   - Define terminal state semantics and retry eligibility.
   - Define status ownership boundaries (scheduler vs harness outcomes).

2. **Persistence protocol**
   - Define when writes occur (run start, run end, failure handling).
   - Establish safe write strategy to avoid partial queue corruption.
   - Define metadata fields for observability (timestamps, run_id, last_error).

3. **Crash consistency**
   - Define behavior if process exits after lock write but before queue update.
   - Define reconciliation rules between lock state and queue state on restart.
   - Define replay/idempotency policy for interrupted transitions.

4. **Retry and resumption policy**
   - Define retry thresholds and escalation (e.g., repeated failures → blocked).
   - Define backoff and eligibility windows.
   - Define operator overrides for forced requeue.

## Out of scope

- Full stale-lock lifecycle implementation details.
- Provider-specific harness improvements.

## Deliverables

- Transition state machine and policy doc.
- Queue persistence consistency rules.
- Recovery decision table for interrupted runs.
- Tests for transition correctness and crash-resume behavior.

## Dependencies

- Phase 1 queue contract and status semantics.

## Risks and mitigations

- **Risk:** Mid-write failure corrupts queue file.
  - **Mitigation:** atomic write pattern and validation post-write.
- **Risk:** Ambiguous recovery creates duplicate processing.
  - **Mitigation:** deterministic reconciliation precedence rules.

## Exit criteria

- Queue item transitions are persistent and auditable.
- Interrupted runs are recoverable without violating single-item processing guarantees.
- Retry behavior is deterministic and documented.

## Handoff to next phase

Phase 3 builds lock recovery on top of these durable queue-state guarantees.
