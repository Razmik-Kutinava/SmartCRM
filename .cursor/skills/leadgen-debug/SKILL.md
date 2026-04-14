---
name: leadgen-debug
description: Debugs SmartCRM lead generation pipeline failures end-to-end across backend routes, providers, analyzers, DB models, and frontend flows. Use when the user mentions leadgen errors, empty or low-quality leads, provider failures, pipeline regressions, flaky tests, or asks to investigate and fix lead generation behavior.
---

# Leadgen Debug

## Purpose

Use this skill to quickly diagnose and fix lead generation issues in SmartCRM with a repeatable workflow.

## When To Apply

Apply this skill when requests mention:

- `leadgen`
- pipeline bugs or regressions
- failed provider calls (`apollo`, `builtwith`, `checko`, `newsapi`, `buster`)
- empty enrichment fields
- wrong lead scoring or analyzer output
- backend route failures for lead generation
- frontend leadgen page not showing expected results

## Debug Workflow

Copy this checklist and track progress:

```md
Leadgen Debug Progress
- [ ] Reproduce issue and capture exact symptom
- [ ] Map failing path (UI/API -> route -> pipeline -> provider/analyzer -> DB)
- [ ] Add focused logs/assertions at failing boundary
- [ ] Implement minimal safe fix
- [ ] Run targeted tests and smoke checks
- [ ] Document root cause and prevention
```

### 1) Reproduce Exactly

- Capture the failing endpoint, payload, and expected vs actual output.
- If the issue starts in UI, trace the request to the matching backend route.
- Prefer deterministic repro with fixed sample input.

### 2) Trace The Execution Path

- Identify entrypoint route and pipeline function.
- Follow data through:
  - route validation
  - provider module calls
  - analyzer transforms
  - persistence model/session writes
  - response serialization
- Stop at first boundary where data becomes invalid or empty.

### 3) Validate Provider Boundaries

- For each external provider call:
  - validate auth/key env variables are present
  - verify timeout/error handling
  - guard against schema drift (missing/renamed fields)
- Normalize provider payloads before downstream analyzer logic.

### 4) Validate Analyzer And Scoring Logic

- Check assumptions about nullable fields and numeric ranges.
- Add defensive defaults only where domain-safe.
- Keep scoring rules explicit and testable.

### 5) Validate Persistence And Model Mapping

- Confirm mapped fields match DB model names and types.
- Ensure writes happen in the expected transaction/session.
- Validate dedupe keys and unique constraints behavior.

### 6) Fix Minimally, Then Verify

- Implement the smallest change that restores correctness.
- Avoid broad refactors during incident-style debugging.
- Run targeted tests first, then adjacent smoke tests.

## Output Format

When reporting results, use:

```md
## Leadgen debug result

### Symptom
- <what failed>

### Root cause
- <precise technical cause>

### Fix
- <what changed and why>

### Verification
- <tests/checks run and outcomes>

### Follow-ups
- <optional hardening or monitoring tasks>
```

## Guardrails

- Prefer existing project patterns over new abstractions.
- Do not silently swallow provider/analyzer errors; convert them to actionable logs.
- Keep logs structured and free of secrets.
- If multiple fixes are possible, choose the one with lowest regression risk.

## Additional Resources

- For concrete checks and reusable commands, see [reference.md](reference.md).
