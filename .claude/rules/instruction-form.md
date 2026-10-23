# Choosing the Form of an Instruction

When a blueprint has a process failure, the reflex is to
write the correction into an agent's instructions. For one
class of correction that reliably does not work, and
repeating it wastes a revision cycle per attempt.

This rule is about **which form** a fix takes, not about
where the file lives. It complements
`reasoned-instructions.md` (when to add rationale) and
`behavior-preserving-cuts.md` (when to remove prose).

## The Evidence

A production program ran a controlled comparison across
twenty task cycles.

**Worked on the first try — requirements on the shape of an
artifact:**

- "A sign-off must state the SHA it covers." The output gate
  was signed three times in one task; every signature named
  its SHA, and the recurring argument about which tree a
  signature applied to did not recur.
- "Ask the implementor for the sign-off's own text; do not
  accept a paraphrase."
- "Check the delivery against the plan's required list, item
  by item — not only against the advisor's own list."

**Failed every time — judgments about when to act:**

- "Do not idle waiting for an advisor's reply." Written into
  the developer's instructions three separate times, moved
  to the top of the dispatch message on the third, and the
  developer stopped and waited in all three tasks.
- "A status query from the lead is an exception to the
  do-not-resend rule." The advisor stayed silent through
  three consecutive queries.

## Why the Second Class Fails

A requirement on an artifact is checkable: the field is
present or it is not, and the agent writing it can tell.

A judgment about timing has to beat the agent's local view
of the situation, and the local view is usually reasonable.
"I just sent a consult; waiting for the answer" is a
coherent next step at that moment. An instruction saying
otherwise loses to it.

## What to Do Instead

When the correction is about *when* something should happen,
convert it into one of these:

1. **A field on an artifact.** One more line in a sign-off,
   one more item in a handoff, one more recipient, one more
   parameter on a tool call. Set at production time, checkable
   at consumption time.
2. **An action hung on an event the harness generates.** Not
   "notice when X is wrong" but "when event E arrives, do D."
   A teammate going idle, a hook firing, a tool result
   returning — these arrive whether or not anyone remembered
   to look.
3. **Withdrawal of a competing authorization.** Sometimes the
   instruction is not missing; something else already
   licenses the behavior. Removing the license works where
   adding a prohibition does not — and it is easy to miss,
   because the prohibition and the license usually live in
   different files.

Option 3 is what the "do not idle" case actually needed. The
developer's own instructions listed "waiting for an advisor's
response" as a legitimate way to end a turn. Three dispatch
messages argued with a standing instruction, and the standing
instruction won.

## Before Writing Any Fix

Read what the blueprint currently says about the behavior.
An instruction that failed may have failed because another
file contradicted it — in which case the fix is in that
other file, and adding a third statement of the same rule
makes the contradiction harder to see rather than resolving
it.

## Scope

This applies when authoring or revising any blueprint file.
It is a rule for the blueprint's authors; it does not go
into a blueprint. The runtime equivalent for the lead —
acceptance criteria must be concrete and measurable — is
already enforced by `plan-format.md` and
`plan-review-checklist.md` through the `plan-reviewer` gate.
