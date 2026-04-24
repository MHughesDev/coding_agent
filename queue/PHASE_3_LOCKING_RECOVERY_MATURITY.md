# Phase 3 — Locking & Recovery Maturity

Parent roadmap: `queue/PLAN.md`.

## Why this phase exists

The lock file currently provides visibility, but robust operations require stale-lock detection and consistent recovery behavior after abrupt termination.

## Primary outcome

`queue.lock` becomes a reliable operational artifact for diagnosing active work and safely recovering from crashes.

## In-scope workstreams

1. **Stale lock policy**
   - Define lock freshness rules (timestamps, optional heartbeat, age thresholds).
   - Define stale-lock classification (definitely stale vs uncertain).
   - Define operator and automated cleanup rules.

2. **Lock metadata model**
   - Enrich lock payload with process/session identifiers and pass/run context.
   - Define mandatory vs optional lock fields.
   - Define compatibility behavior for legacy/minimal lock files.

3. **Recovery semantics**
   - Define startup behavior when lock exists.
   - Reconcile lock state with queue state transitions.
   - Define safe continuation, retry, or quarantine actions.

4. **Operational diagnostics**
   - Define lock inspection output for troubleshooting.
   - Define failure message taxonomy around lock conflicts/recovery.

## Out of scope

- Harness execution policy changes.
- Broader observability/reporting platform work.

## Deliverables

- Lock lifecycle specification (create/update/clear/recover).
- Stale-lock decision matrix.
- Restart and recovery runbook.
- Tests for stale-lock scenarios and lock/queue reconciliation.

## Dependencies

- Phase 2 transition persistence and crash-consistency behavior.

## Risks and mitigations

- **Risk:** False stale detection interrupts valid work.
  - **Mitigation:** conservative thresholds + explicit uncertain state.
- **Risk:** Lock and queue state drift.
  - **Mitigation:** deterministic reconciliation precedence and audit logs.

## Exit criteria

- Existing lock files at startup are handled deterministically.
- Recovery decisions are observable, documented, and test-covered.
- Lock lifecycle does not violate single-active-run constraints.

## Handoff to next phase

Phase 4 can now assume robust run lifecycle boundaries and reliable restart behavior.
