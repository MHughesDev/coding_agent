# Phase 7 — Configuration & Provider Flexibility

Parent roadmap: `queue/PLAN.md`.

## Why this phase exists

As environments vary, behavior must be tunable without modifying code, while preserving deterministic defaults.

## Primary outcome

A coherent configuration model governs scheduler, queue policy, and model provider behavior with clear precedence and validation.

## In-scope workstreams

1. **Configuration surfaces and precedence**
   - Define config sources (CLI, env vars, config file) and precedence rules.
   - Define startup validation behavior and error reporting.
   - Define immutable-at-runtime vs runtime-adjustable settings.

2. **Provider abstraction maturity**
   - Define provider capability matrix for OpenAI-compatible endpoints.
   - Define timeout/retry/circuit-breaker style behavior.
   - Define authentication and endpoint compatibility requirements.

3. **Prompt and behavior configuration**
   - Define prompt profile/version selection policy.
   - Define safe overrides for harness behavior.
   - Define fallback strategy when provider settings are invalid/unreachable.

4. **Operational safety controls**
   - Define guardrails on dangerous/unsupported combinations.
   - Define diagnostics that expose effective config at startup.

## Out of scope

- New scheduler algorithms.
- Deep harness algorithm redesign.

## Deliverables

- Unified configuration contract and precedence matrix.
- Provider compatibility policy and failure behavior spec.
- Tests for config loading/validation and provider error boundaries.

## Dependencies

- Phase 4 harness contract.
- Phase 6 observability surfaces (for config diagnostics).

## Risks and mitigations

- **Risk:** Config sprawl introduces ambiguity.
  - **Mitigation:** strict precedence matrix and explicit effective-config output.
- **Risk:** Provider-specific drift leaks into scheduler logic.
  - **Mitigation:** keep provider details isolated to harness model client interfaces.

## Exit criteria

- Operators can configure behavior safely without code changes.
- Provider failures degrade predictably with actionable diagnostics.
- Effective configuration is transparent and test-covered.

## Handoff to next phase

Phase 8 expands test depth against the now broader policy/config surface.
