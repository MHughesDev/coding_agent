# Phase 6 — Observability & Operator UX

Parent roadmap: `queue/PLAN.md`.

## Why this phase exists

Operational trust depends on quickly understanding what the system is doing, what failed, and what to do next.

## Primary outcome

Operators gain clear, structured visibility into passes, queue item runs, outcomes, and recovery state.

## In-scope workstreams

1. **Structured event model**
   - Define event taxonomy (pass start/end, item selected, run completed, lock recovery, errors).
   - Define common fields (repo, queue_id, pass_id, durations, outcome, severity).
   - Define human-readable + machine-readable output modes.

2. **Run artifacts and traceability**
   - Define per-run artifact contents (summary, model boundary outcomes, validations, errors).
   - Define retention and cleanup policy for run artifacts.
   - Define correlation identifiers across logs, lock, queue transitions.

3. **Diagnostics UX**
   - Define status/diagnostics surface for current active state and recent failures.
   - Define operator-facing remediation hints for common failure classes.

4. **Failure communication standards**
   - Standardize concise and actionable error messaging.
   - Define escalation severity for warnings vs fatal conditions.

## Out of scope

- Deep policy changes to scheduling semantics.
- Queue contract semantics updates.

## Deliverables

- Observability schema and operator diagnostics guide.
- Run artifact structure definition.
- Tests validating critical event emission and diagnostic correctness.

## Dependencies

- Phase 5 runtime robustness and control points.
- Phase 3 lock recovery semantics.

## Risks and mitigations

- **Risk:** Logging noise reduces signal.
  - **Mitigation:** schema discipline and severity thresholds.
- **Risk:** Missing correlation across artifacts.
  - **Mitigation:** required run/pass identifiers across all surfaces.

## Exit criteria

- Operators can quickly determine active work, last outcomes, and remediation path.
- Critical events are consistently emitted in structured form.
- Run diagnostics support recovery workflows without code inspection.

## Handoff to next phase

Phase 7 builds configurability on top of these observable runtime behaviors.
