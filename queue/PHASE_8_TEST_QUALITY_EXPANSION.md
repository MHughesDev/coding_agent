# Phase 8 — Test & Quality Expansion

Parent roadmap: `queue/PLAN.md`.

## Why this phase exists

The expanded behavior introduced in earlier phases requires deeper coverage to prevent regressions in deterministic scheduling and queue correctness.

## Primary outcome

A layered, high-confidence test strategy protects queue semantics, runtime recovery, and harness contract stability.

## In-scope workstreams

1. **Queue contract and transition coverage**
   - Extend tests for malformed CSV, duplicate IDs, dependency cycles, and blocked states.
   - Extend transition tests for all legal/illegal lifecycle moves.
   - Validate crash/restart reconciliation behavior.

2. **Supervisor integration simulations**
   - Model multi-repo pass sequences with mixed queue conditions.
   - Validate empty-pass sleep and immediate rerun invariants under stress.
   - Validate lock + queue consistency under injected failures.

3. **Harness boundary and provider tests**
   - Validate model call timeouts/errors and fallback behavior.
   - Validate structured result contracts across planner/executor/validator.
   - Validate prompt/context handling limits.

4. **Quality gates and regression policy**
   - Define minimum test categories required for merge.
   - Define deterministic test-run expectations for CI/local execution.

## Out of scope

- New product features not yet represented in roadmap phases.

## Deliverables

- Comprehensive test matrix mapped to roadmap invariants.
- Expanded automated suite across unit/integration boundary layers.
- Regression checklist integrated into development workflow.

## Dependencies

- Phases 1–7 behavior stabilization.

## Risks and mitigations

- **Risk:** Slow or flaky tests reduce trust.
  - **Mitigation:** deterministic fixtures, bounded integration scenarios, strict flake triage.
- **Risk:** Coverage gaps in cross-phase interactions.
  - **Mitigation:** matrix-based traceability from invariants to tests.

## Exit criteria

- Critical invariants are covered across queue, scheduler, lock, and harness boundaries.
- Regression risk is measurable and enforced by quality gates.
- Test suite remains deterministic and maintainable.

## Handoff to next phase

Phase 9 operationalizes this quality baseline into docs and readiness standards.
