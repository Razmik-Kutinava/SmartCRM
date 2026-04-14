---
name: prompt-eval
description: Evaluates LLM prompts for quality, reliability, and task fit using a repeatable rubric. Use when the user asks to assess a prompt, compare prompt variants, improve prompt quality, reduce hallucinations, tune instructions, or design prompt tests.
---

# Prompt Eval

## Purpose

Use this skill to evaluate and improve prompts with a consistent, evidence-based process.

## When To Apply

Apply this skill when requests mention:

- prompt evaluation or prompt review
- prompt quality issues
- hallucinations or weak model adherence
- comparing two or more prompt variants
- prompt tuning or optimization
- creating prompt test cases

## Evaluation Workflow

Copy this checklist and track progress:

```md
Prompt Eval Progress
- [ ] Confirm task goal and success criteria
- [ ] Identify model, context window, and constraints
- [ ] Score prompt with rubric
- [ ] Propose minimal, high-impact prompt edits
- [ ] Define test set and expected outcomes
- [ ] Re-score revised prompt and report delta
```

### 1) Define Target Behavior

- Capture the exact job the prompt must perform.
- Write measurable success criteria before editing.
- Note constraints: latency, token budget, output format, safety.

### 2) Analyze Prompt Structure

- Check role, objective, boundaries, and output schema clarity.
- Identify ambiguity, conflicting instructions, or missing context.
- Verify examples (if present) are representative and concise.

### 3) Score With Rubric

Use 1-5 scoring for each dimension:

- task clarity
- context completeness
- instruction hierarchy
- output format specificity
- robustness to edge cases
- safety and policy alignment

### 4) Improve With Minimal Changes

- Keep intent unchanged unless user asks for strategy shift.
- Prefer targeted edits over full rewrites.
- Add explicit guardrails only when they solve observed failure modes.

### 5) Build A Small Test Set

- Include happy path, edge case, and adversarial-style input.
- Define expected output traits (not only exact wording).
- Use the same rubric to compare baseline vs revised prompt.

## Output Format

When reporting results, use:

````md
## Prompt evaluation result

### Goal
- [what the prompt should achieve]

### Rubric scores (1-5)
- Task clarity: <score>
- Context completeness: <score>
- Instruction hierarchy: <score>
- Output format specificity: <score>
- Robustness: <score>
- Safety alignment: <score>

### Key issues
- [top weaknesses with concrete evidence]

### Revised prompt
```text
[improved prompt]
```

### Test plan
- Input 1: [case] -> Expected: [traits]
- Input 2: [case] -> Expected: [traits]

### Expected improvement
- [what should improve and why]
````

## Guardrails

- Do not claim quality improvements without test criteria.
- Avoid over-constraining prompts that need creativity.
- Keep revisions model-agnostic unless user specifies a model family.
- Flag missing business constraints instead of inventing them.

## Additional Resources

- For scoring anchors and rewrite patterns, see [reference.md](reference.md).
