---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.py"
  - "**/*.go"
---

# Reuse the Existing Entry Point First

Before creating a new launcher, harness, test scaffold, or
service entry point to validate a feature, first check
whether an existing production entry point and a working
launch/verify setup already exist. Building a parallel
scaffold that duplicates something already runnable costs
time twice — once to build it, and again when the work has to
be redone against the real entry point.

## The Failure Mode

A validation asked for "launch the service, call the handler
from outside, confirm the result." A standalone lightweight
launcher was built for it — while the real service binary
already had a complete local launch setup (seeded config,
reachable middleware, a working interpreter) sitting unused.
The scaffold was thrown away and the validation redone
against the real binary. The trigger was a prediction that
the real entry point "couldn't run locally", made without
trying it.

## The Rule

1. **Look before you build.** Before writing a new entry
   point or harness, search for an existing production entry
   point (a `main`, a CLI command, an HTTP route, a public
   API) and for a completed launch/verify setup — prior goal
   or run docs, local config files, seeded middleware, a
   previously validated environment. A project's own reuse
   map (e.g. a goal's `reference.md`) is the code-reuse
   analogue; this rule extends that discipline to operational
   reuse.

2. **Try the real thing first.** If you suspect the existing
   entry point cannot run, that is a prediction — test it
   (see `exercise-before-concluding.md`) before concluding a
   new scaffold is needed.

3. **Justify a parallel scaffold explicitly.** Building a new
   launcher/harness is justified only after confirming reuse
   is impossible or genuinely more expensive, and the reason
   must be stated in the handoff. A throwaway scaffold left
   undocumented reads to the next reader as the intended
   entry point.

## Why This Matters

Parallel entry points diverge from the real one over time,
and a validation run against a bespoke harness proves less
than the same run against the production entry point — it can
pass while the real path is broken. Reusing the real entry
point is both cheaper and a stronger signal.

## Related Rules

- `exercise-before-concluding.md` — try the existing entry
  point before predicting it won't work.
- `claim-verification.md` — a "can't reuse it" claim is an
  infeasibility claim and needs the same evidence bar.
