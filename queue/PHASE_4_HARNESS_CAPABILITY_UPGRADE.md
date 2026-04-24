# Phase 4 — Harness Capability Upgrade

Parent roadmap: `queue/PLAN.md`.

## Why this phase exists

The harness currently provides structure but limited execution depth. To realize autonomous queue processing, planning/execution/validation need practical capability while preserving isolation under `harness/`.

## Primary outcome

Upgrade harness internals so queue runs can produce meaningful code changes and verifiable outcomes without leaking orchestration concerns into harness modules.

## In-scope workstreams

1. **Context and planning quality**
   - Define context budget and prioritization policy.
   - Define structured plan format with step intent and acceptance signals.
   - Define failure modes when model output is malformed or incomplete.

2. **Execution boundaries**
   - Define allowed operation classes (edit/create/delete/test invocation policy).
   - Define filesystem safety scope (repo-local boundaries).
   - Define deterministic edit application/reporting contract.

3. **Validation routing**
   - Define repository-type-aware validation strategy.
   - Define validation result classification and confidence levels.
   - Define handoff format from harness validation to queue transition logic.

4. **Model interaction resilience**
   - Define timeout/retry/degradation strategy for model calls.
   - Define behavior when model endpoint is unavailable.
   - Define output normalization for stable downstream parsing.

## Out of scope

- Scheduler pass semantics changes.
- Repo rotation or fairness policy changes.

## Deliverables

- Harness capability spec with clear contracts between runner/planner/executor/validator.
- Validation outcome taxonomy.
- Expanded harness tests for model boundary and result-structure stability.

## Dependencies

- Phase 1 status semantics.
- Phase 2 transition outcomes (to consume harness results).

## Risks and mitigations

- **Risk:** Harness complexity bleeds into orchestration layer.
  - **Mitigation:** enforce strict interface contracts at `HarnessRunner` boundary.
- **Risk:** Non-deterministic model output destabilizes execution.
  - **Mitigation:** structured output expectations and defensive parsing.

## Exit criteria

- Harness produces structured, actionable execution results.
- Validation outcomes can drive queue status transitions deterministically.
- Architecture boundary (`app/` vs `harness/`) remains intact.

## Handoff to next phase

Phase 5 uses improved harness confidence to harden multi-repo runtime robustness.
