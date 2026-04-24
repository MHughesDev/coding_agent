# Phase 1 — Queue Contract Hardening

Parent roadmap: `queue/PLAN.md`.

## Why this phase exists

Before the supervisor can be trusted in long-running operation, queue parsing and actionability decisions must be deterministic, explicit, and resilient to imperfect queue data.

## Primary outcome

Establish an unambiguous queue contract so every subsequent phase can rely on stable input semantics.

## In-scope workstreams

1. **Schema contract**
   - Define required columns (e.g., `id`, `status`, `summary`) and optional columns (e.g., `depends_on`, `notes`, `related_files`).
   - Standardize allowed values and normalization rules (case, whitespace, separators).
   - Define forward-compatibility behavior for unknown columns.

2. **Validation behavior**
   - Introduce queue contract checks that classify findings as: fatal, warning, informational.
   - Provide operator-friendly error messages that identify row/column context.
   - Define startup and per-pass behavior when invalid data is encountered.

3. **Actionability semantics**
   - Canonicalize lifecycle statuses and map aliases to canonical states.
   - Define deterministic selection tie-breaks (row order vs timestamp vs priority fields).
   - Define behavior for missing IDs, duplicate IDs, and malformed dependency references.

4. **Dependency interpretation**
   - Normalize separators and formatting in dependency fields.
   - Define handling for unresolved dependencies and self-dependencies.
   - Define cycle-detection expectations and blocked-item categorization.

## Out of scope

- Changing queue item status in-place during runs.
- Stale lock recovery mechanics.
- Harness execution enhancements.

## Deliverables

- Queue contract specification addendum (or section update).
- Validation/reporting policy for queue ingestion.
- Deterministic actionability matrix (status + dependency conditions → decision).
- Expanded tests covering malformed and edge-case queue data.

## Dependencies

- None (foundational phase).

## Risks and mitigations

- **Risk:** Overly strict validation blocks work unnecessarily.
  - **Mitigation:** tiered validation severity and configurable strictness profile.
- **Risk:** Ambiguous tie-break logic causes non-determinism.
  - **Mitigation:** explicit single tie-break chain documented in contract.

## Exit criteria

- Queue parsing is deterministic for all supported status/dependency combinations.
- Invalid queue data produces clear, actionable diagnostics.
- Tests demonstrate stable behavior for malformed CSV and dependency edge cases.

## Handoff to next phase

Phase 2 assumes this phase has produced stable state semantics and trustworthy queue row interpretation.
