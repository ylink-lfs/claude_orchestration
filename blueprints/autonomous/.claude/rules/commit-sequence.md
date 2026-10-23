# Commit Sequence

The lead's post-approval commit sequence has three failure
surfaces that quality signals do not reveal: a SHA that went
stale between messages, a file that was never staged, and an
approval that arrived out of order. Each of these has shipped
in production with a clean build and a green test suite.

This rule holds the mechanics. The step order is in
`CLAUDE.md` under After Reviewer Approval.

## The SHA Comes From the Approval, Read Fresh

Use the baseline SHA from the **reviewer's approval
message**. Before running any git command, re-read the
current tip with `git log` or `git rev-parse HEAD`.

**Never reuse a SHA you verified earlier yourself.** A lead
told a reviewer "I independently confirmed `<sha>` is the
current WIP tip." That was true when said and stale by the
time it was used — the developer had committed again during
review. Your own earlier verification expires exactly like
anyone else's message does. See `safe-git.md` on anchor
freshness.

## Staging: Untracked Files Are Silently Dropped

After the reset, stage **each file from the reviewer's
verified list explicitly by path**. Never `git add .` or
`git add -A`.

Then confirm new files actually landed:

```
git show --summary HEAD | grep "create mode"
git diff --name-status <baseline-sha> HEAD | grep '^A'
```

**Use `--summary`, not `--stat`.** `git show --stat` does not
emit `create mode` lines at all, so the grep returns nothing
whether or not a file was created — a false negative that
silently defeats this check. Verified on git: for a commit
that demonstrably added a file, `--stat | grep "create mode"`
exits 1 and `--summary | grep "create mode"` prints the path.
The `--name-status` line is the independent confirmation; `A`
entries are the added files.

Untracked files are the trap. A task had ten changed files,
two of them new and untracked — and those two held the
task's two core tests. Staging only the modified files drops
them, and **the omission is invisible**: the files are still
on disk, so the build still compiles and the tests still
pass. The loss only surfaces later, as tests that vanished.

## Final Check

This must be empty — it confirms the commit matches what was
approved:

```
git diff <approved-sha> HEAD --stat
```

## Approvals Received During a Hold

If you asked the reviewer to hold approvals, an approval
that arrives afterward may have been **sent before your hold
reached it**. Ask the reviewer which, and do not run the
commit sequence until you know. A production session
executed a commit from an approval that predated its own
hold.

## Optional Suggestions Have a Gate Cost

When you offer the implementor an optional suggestion —
a nice-to-have comment, a small clarification — state the
gate consequence in the same message: **"if you take this
and it touches a production file, the output gate must be
re-run."**

Without that, the suggestion reads as free. A lead offered a
Low-severity comment addition, the developer added it, the
edit touched a production file, and it reopened an
already-closed output gate. The implementor should get to
decide whether the suggestion is worth that; it cannot decide
what it was not told.

## Skill-Output Commits

You make all commits — code commits (after reviewer
approval) and skill infrastructure outputs. For skill
outputs, **commit files that a skill's `SKILL.md` explicitly
names as outputs — immediately after the skill completes.**

The skill procedure determines what is written; you execute
it mechanically. This is not a general permission to commit
files you write based on your own judgment — that is
implementation work and must go through the
developer-reviewer pipeline.

**The test:** if you removed the skill invocation, would
this file still need to exist? If yes, it is project work
that belongs in the pipeline. If no, it is skill
infrastructure that you commit directly.

This covers `/project-init` outputs — the project
`CLAUDE.md`, `Cargo.toml` lint config, TypeScript
strictness config, and code intelligence plugin entries in
`.claude/settings.json`. Those are tracked project files.

It does **not** cover anything written into the plans
directory. `/ensure-ai-dirs` writes the format guide,
review checklist, `completed/CLAUDE.md`, and the
finished-plan moves into `completed/` there, and that
directory is normally gitignored — there is nothing to
commit. Plan status changes are local edits for the same
reason.

Skill outputs always land in a window with no teammates
alive, since skills run before any teammate is spawned for a
task — see Commit Timing.

## Commit Timing

With teammates alive, the only commits you make are the
post-approval task commit sequence (steps 2–5 of After
Reviewer Approval). Those are bounded by the squash reset
at step 2 and use the reviewer's handoff data as input.
Every other lead commit — skill outputs and user-directed
ad-hoc changes (doc tweaks, convention updates, small
fixes) — happens only in a team-down window.

**Team-down windows** — no teammate is alive:
- Before the first spawn (initial planning, skill runs,
  user clarifications).
- After the final shutdown at plan completion or
  abandonment.

Cycling between tasks is **not** a team-down window. Step 6
of After Reviewer Approval spawns the next task's instances
before shutting down the current one, precisely so that no
such gap exists — a lead that stops there has no teammate
left to generate the idle notification that would restart
it. Work that needs a team-down window waits for plan
completion.

**When the user requests a lead-side change while a team is
active**, note it and commit it in the next team-down
window. Do not commit ad-hoc changes while a team is up,
even if the change is small and the files do not overlap
with the developer's WIP.

**Why.** The post-approval squash runs
`git reset <baseline-sha>`, which wipes every commit
between the task's baseline and HEAD. An ad-hoc commit made
while a team is active lands in that range and is lost at
squash time. A production incident committed two
user-directed doc changes on top of the developer's WIP;
the commits were stranded between baseline and WIP and
required an emergency history reorder (stash + reset +
cherry-pick ×3 + pop) while the developer was actively
editing — the developer's uncommitted work was at risk
because the doc commits happened to not touch the WIP
files, not because the sequence was safe. The safe rule is
not "commit carefully during a task" — it is "do not commit
at all until the team is down."

## Conventional Commits

This blueprint uses conventional commit prefixes. The
reviewer composes the commit message for approved code and
you make the commit — commit type definitions live in the
reviewer's agent file. For skill-output commits, use `chore`
for infrastructure artifacts.

## Scope

This rule is for the lead — it is the only agent that runs
the post-approval commit sequence.
