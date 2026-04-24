# Phase 5 — Repo & Runtime Robustness

Parent roadmap: `queue/PLAN.md`.

## Why this phase exists

As usage broadens across diverse local repos, startup checks, runtime controls, and fairness behavior must be explicit and resilient.

## Primary outcome

Supervisor behavior remains deterministic and safe under heterogeneous repo conditions and long-running operation.

## In-scope workstreams

1. **Repo readiness policy**
   - Define strict vs permissive repo validation modes.
   - Define required artifacts vs optional artifacts and fallback behavior.
   - Define skip/reporting semantics for partially compliant repos.

2. **Runtime control policies**
   - Define bounded run modes (max passes, max duration, maintenance windows).
   - Define graceful shutdown and drain behavior.
   - Define safe interruption points.

3. **Fairness and throughput**
   - Define measurable fairness criteria across ordered repos.
   - Detect and report starvation patterns.
   - Define balancing levers that preserve ordered pass guarantees.

4. **Error isolation**
   - Ensure one repo’s repeated failures do not destabilize global loop.
   - Define escalation behavior for chronic repo-level failure.

## Out of scope

- Detailed structured logging schema (Phase 6).
- Provider configuration expansion (Phase 7).

## Deliverables

- Repo readiness policy and runtime control spec.
- Fairness and starvation measurement policy.
- Integration tests for mixed repo states and long-running passes.

## Dependencies

- Phases 1–4 baseline semantics and harness outcomes.

## Risks and mitigations

- **Risk:** Hardening breaks current flexibility for imperfect repos.
  - **Mitigation:** configurable readiness profiles with clear defaults.
- **Risk:** Fairness enhancements accidentally violate ordered pass contract.
  - **Mitigation:** enforce invariant checks preserving repo order and one-item-per-visit.

## Exit criteria

- Runtime remains stable under mixed-validity repo sets.
- Long-running behavior is observable for fairness and throughput.
- Shutdown and bounded run controls are deterministic.

## Handoff to next phase

Phase 6 layers richer observability onto these robust runtime semantics.
