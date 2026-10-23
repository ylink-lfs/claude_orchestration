# Claim Verification

When an agent reports that work is infeasible, blocked, or
requires major architectural changes, verify the claim
before accepting it. Unverified technical claims are the
most common source of premature plan closure in this
blueprint — four documented instances show the same
pattern: work framed as impossible turns out to be a
moderate change in the project's own codebase.

The same discipline applies to **positive** claims — "it
works", "it's tested", "it's verified" — and to your **own**
predictions, not only to infeasibility claims you receive
from another agent. A confident "done" backed by nothing
that ran is as unverified as a confident "can't be done".

## The Pattern

The implementor optimizes for scope reduction — fewer
things to implement means faster completion. This creates
a consistent bias: remaining work is framed as harder than
it is. Category labels like "needs X enhancement" or
"requires architectural changes" inflate perceived effort
without describing the actual work. These labels are
unfalsifiable without reading the code, so they pass
through review unchallenged.

## The Rule

### Require specifics, not categories

When reporting work as infeasible or requiring major
changes, the report must include:

- **Which file and function** would need to change
- **Whether the change is in the project's own codebase**
  or an external dependency — these are fundamentally
  different. A change in our own code is work to be
  scoped; a change in a dependency may be a genuine
  blocker.
- **Estimated scope** — approximate line count or
  complexity
- **What specifically is missing or insufficient** — not
  "the parser doesn't support X" but "the parser emits
  events A and B but the loader in `file.rs:fn_name()`
  doesn't consume event B"

A category label ("needs parser enhancements") without
these specifics is not sufficient justification for
closing or deferring work.

### Verify against the codebase

When you receive a claim that work is infeasible, read
the relevant source before accepting it. Check:

- Does the infrastructure the implementor says is missing
  actually not exist? Often it does — the implementor
  looked in the wrong place or at the wrong abstraction
  level.
- Is the change in an external dependency, or in the
  project's own code? The implementor may frame an
  internal change as if it requires upstream work.
- Is the scope as large as claimed? A "parser enhancement"
  might be a 10-line loader fix.

This verification takes minutes. Skipping it has
repeatedly allowed moderate tasks to be closed as
impossible.

### Distinguish N/A from blocked

- **Not applicable (N/A)** — the item does not apply to
  this project. Close it.
- **Blocked** — the item applies but cannot be completed
  now. Keep it open with a description of what unblocks
  it.

Do not use N/A for blocked items — N/A closes the item
permanently, while blocked preserves it for future work.
A plan with blocked items is not Completed; it stays
InProgress or gets follow-up tasks that address the
blocker.

### Verify test-failure categorization

When a handoff reports test failures as "expected" for a
later task, "pre-existing at baseline," or otherwise out
of scope for the current work, verify each failure
individually before accepting. Batch categorization is
the same scope-reduction bias as unverified infeasibility
claims — a set of failures is labeled "not in scope" and
moves through review unchallenged, even when one failure
has a different root cause that *is* in scope.

**For "expected failure" claims.** The claim must name
each failure and cite its specific root cause, mapped to
the expected category. "17 failures all map to Task 2"
is not sufficient — the claim must state, for each
failure, why its root cause matches Task 2's scope.
Reviewers read enough of each failure message to confirm
the mapping, not infer it from the aggregate count. A
failure whose root cause does not match the stated
category is a bug introduced by the current work, not
deferred work — treat it as a review finding, not a
known issue.

**For "pre-existing at baseline" claims.** The claim
must cite the baseline commit SHA and the exact test
command. Verifiers (reviewer at review time, lead at
spot-check) run that command at that SHA before
accepting the claim. Inferring "pre-existing" from
memory or from code reading is not verification — a
production incident had a reviewer mark a failure
pre-existing across three consecutive tasks without
running the test, and the claim was verifiably false at
the cited baseline. The failure was a bug introduced in
Task 1 that shipped to `main` because each subsequent
task carried the unverified claim forward.

### Positive claims and your own predictions need the same evidence

The bar above is usually described for a claim you *receive*
that something can't be done. It applies just as much to a
**positive** claim — "it works", "it's tested", "it's
verified" — and to a prediction *you* make before acting on
it ("this won't build", "the real entry point can't run
locally").

- A positive claim must be traceable to evidence that the
  path actually ran: which command, which test, and the
  observed output showing execution — the same specifics
  demanded of an infeasibility claim.
- **Existing evidence counts, and only the gap needs work.**
  If a prior run, a passing lane, or the current repo state
  already demonstrates the claim, cite that and move on. The
  requirement bites **only** when no execution evidence
  exists at all — a path claimed working that was skipped or
  never run. It does **not** ask you to re-verify claims or
  acceptance-criteria bullets the repo already satisfies;
  re-proving already-evidenced facts is wasted work, not
  diligence.
- Before acting on your *own* prediction that something is
  infeasible or too costly, take the cheapest disproving
  action first (see `exercise-before-concluding.md`). A
  workaround built on an untested prediction is the same
  error as accepting an unverified claim from someone else.

## Why This Matters

Each instance of unverified infeasibility compounds:
the plan closes, the work disappears from the queue,
and the underlying issue remains. Future sessions see a
Completed plan and move on — they don't know the work
was deferred. The gap is only discovered when a user
hits the missing functionality and asks why it wasn't
done.

## Related Rules

- `exercise-before-concluding.md` — the general form: run
  the path before you conclude anything about it.
- `integration-testing.md` — gated coverage must run once
  with the gate satisfied before "verified" holds.
