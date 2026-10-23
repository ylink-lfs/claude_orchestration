---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.py"
  - "**/*.go"
---

# Exercise Before You Conclude

A claim about how the running system behaves — "tested",
"verified", "it works", "it can't boot", "that's
infeasible", "too costly" — must be backed by having run the
relevant path at least once. A statement you have not
exercised is a prediction, not an observation, and
predictions are where confident-sounding mistakes come from.

## The Failure Mode

Two mirror-image errors, one root cause. In one, a feature
was reported "integration verified" while the tests that
would have proven it had never run — they were gated behind
an unset environment variable and silently skipped, and the
green suite was read as proof. In the other, a redundant
launcher was built on the prediction that the real service
"can't boot locally" — a prediction that was simply wrong;
the real binary booted on the first try. One claimed working
without running it; the other claimed not-working without
trying it. Both substituted a mental model for an executed
path.

## The Rule

1. **Take the cheapest disproving action before you
   conclude.** Before reporting something done, blocked, or
   infeasible, run the smallest thing that would prove or
   disprove it — launch the real entry point, run the gated
   test, issue the real request. Conclude from what you
   observed, not from what you expected.

2. **Distinguish "I predict" from "I observed."** If you
   have not run the path, say so, and say what running it
   would take — do not phrase a prediction as a result.

3. **Existing evidence counts — do not re-run what is
   already green (anti-spinning).** The bar is that the path
   has been exercised at least once and the evidence is on
   record. If a prior run, a passing CI lane, or the current
   repo state already demonstrates it, cite that evidence and
   move on. This rule fires **only on the gap** — a claim for
   which no execution evidence exists at all, or coverage
   that was skipped. It never asks you to re-verify a bullet
   the repo already satisfies; that is wasted work, not
   diligence.

## Why This Matters

The expensive failures here are invisible from the diff: the
tests are green (because they skipped), the report reads
"verified", the workaround looks reasonable. Nothing flags
them except the discipline of having run the path. Exercising
the cheapest disproof once is far cheaper than shipping a
false "done" or building a workaround around a blocker that
was never real.

## Related Rules

- `claim-verification.md` — the same evidence bar applied to
  a specific claim; that rule extends it to positive claims
  and to your own predictions.
- `integration-testing.md` — gated tests must run once with
  the gate satisfied before the feature is called verified.
- `acceptance-criteria.md` — an unexpected skip of required
  coverage is a finding, not silent success.
- `reuse-first-entry-points.md` — the cheapest disproof is
  usually the existing entry point; try it before building a
  new one.
