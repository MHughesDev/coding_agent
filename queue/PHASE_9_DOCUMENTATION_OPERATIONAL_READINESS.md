# Phase 9 — Documentation & Operational Readiness

Parent roadmap: `queue/PLAN.md`.

## Why this phase exists

Sustainable operation requires clear documentation, operator workflows, and release readiness criteria aligned with implemented behavior.

## Primary outcome

The project is understandable, operable, and maintainable without relying on tribal knowledge.

## In-scope workstreams

1. **Specification and behavior alignment**
   - Update README/SPEC to reflect implemented queue lifecycle and recovery policies.
   - Ensure architecture boundaries are documented with examples.
   - Ensure configuration and observability docs match runtime behavior.

2. **Operator runbooks**
   - Define startup, shutdown, and recovery playbooks.
   - Define stale-lock and interrupted-run procedures.
   - Define troubleshooting guide by failure class.

3. **Contribution standards**
   - Define change-checklist for scheduler vs harness modifications.
   - Define testing expectations by change type.
   - Define documentation update requirements for behavioral changes.

4. **Release readiness framework**
   - Define MVP exit criteria and production-readiness gates.
   - Define risk acceptance and rollback expectations.
   - Define post-release monitoring/feedback loop.

## Out of scope

- Major new functional capabilities beyond roadmap scope.

## Deliverables

- Updated docs set (README, SPEC, AGENTS-adjacent guidance where applicable).
- Operator runbook and troubleshooting guide.
- Release-readiness checklist with measurable acceptance criteria.

## Dependencies

- Phases 1–8 completed or stabilized sufficiently for documentation accuracy.

## Risks and mitigations

- **Risk:** Documentation drifts from real behavior.
  - **Mitigation:** documentation-as-gate for behavior-changing merges.
- **Risk:** Operational procedures remain implicit.
  - **Mitigation:** explicit runbooks with scenario-based validation.

## Exit criteria

- New operator can run, monitor, and recover the system using docs alone.
- Contributors can identify correct module boundaries for changes.
- Readiness criteria are objective and auditable.

## Handoff / ongoing posture

This phase transitions the roadmap from build-out to steady-state maintenance with clear operational ownership.
