# Leadgen Debug Reference

## Fast Triage Commands

Run from repository root.

```bash
# backend tests focused on leadgen
pytest backend/tests/test_leadgen.py -q

# run only leadgen-related tests
pytest backend/tests -k leadgen -q

# find leadgen route and pipeline usage
rg "leadgen|pipeline|apollo|builtwith|checko|newsapi|buster" backend
```

## High-Value Checks

1. Route contract
   - Request body schema matches frontend payload.
   - Response schema is stable for UI consumers.
2. Provider contract
   - Missing keys, rate limits, and non-200 responses are handled.
   - Provider fields are normalized before analyzer use.
3. Analyzer behavior
   - Handles partial data and nulls.
   - Scoring logic does not assume unavailable inputs.
4. Persistence
   - Model fields align with transformed payload keys.
   - Transaction/session boundaries are explicit.
5. Regression safety
   - Add or update targeted test for the bug scenario.

## Typical Root Causes In Leadgen Pipelines

- Provider schema drift (field renamed/removed)
- Silent fallback to empty lists on provider errors
- Analyzer assuming non-null enrichment fields
- Score calculation not clamping invalid values
- Route-level validation mismatch with frontend payload
- Duplicate handling incorrectly dropping valid new leads

## Minimal Fix Strategy

- Fix at the earliest failing boundary.
- Keep interfaces backward-compatible unless explicitly changing API contract.
- Add one regression test for the exact failure and one nearby edge case.
