# Prompt Eval Reference

## Rubric Anchors (1-5)

Use these anchors for consistent scoring:

- **1 - Poor**: major ambiguity, frequent failure likely
- **2 - Weak**: partially clear but unreliable across inputs
- **3 - Adequate**: works for common cases, fragile on edge cases
- **4 - Strong**: clear and reliable with minor gaps
- **5 - Excellent**: precise, robust, and easy to validate

## Common Failure Patterns

- Missing explicit goal or success criteria
- Conflicting instructions in different sections
- No output schema or formatting rules
- No boundary handling for unknown data
- Excessive verbosity that hides key constraints

## High-Impact Rewrite Patterns

### Pattern 1: Add explicit success criteria

Before:

```text
Write a summary of this customer call.
```

After:

```text
Summarize the customer call in 5 bullets:
1) primary issue
2) business impact
3) actions already taken
4) proposed next step
5) unresolved risks
Use factual language only; if data is missing, state "Not provided".
```

### Pattern 2: Resolve instruction hierarchy

Before:

```text
Be concise and detailed. Give all context but keep it very short.
```

After:

```text
Priority order:
1) correctness
2) required format
3) brevity
Return 120-180 words and include all mandatory fields.
```

### Pattern 3: Add edge-case behavior

Before:

```text
Classify the lead as hot, warm, or cold.
```

After:

```text
Classify as hot, warm, or cold.
If information is insufficient, return "unknown" and list missing fields.
```

## Lightweight Test Matrix

Use at least 3 cases:

1. **Happy path**: complete and clean input
2. **Edge case**: partial or noisy input
3. **Adversarial case**: contradictory instructions or missing context

Track:

- pass/fail against expected traits
- rubric delta before/after edits
- any new regressions introduced by the rewrite
