# Safe Git Operations

Before running any destructive git command on the working
tree, verify that uncommitted changes are protected.
Destructive operations permanently discard uncommitted
changes — hours of work that exists only in the working
tree is irrecoverable after a `git checkout --`,
`git reset --hard`, or `git clean`.

## The Rule

Before running `git checkout -- <file>`, `git reset
--hard`, `git clean -f`, or `git restore <file>`:

1. Run `git status` to check for uncommitted changes.
2. If the working tree is dirty, stash first:
   `git stash push -m "before <operation>"`. Do not make a
   WIP commit instead — every commit follows the Reviewer's
   approval of the reviewed task.
3. Only then run the destructive command.

## Why

A production incident lost ~2 hours of developer work
when `git checkout -- <file>` was used during debugging
to test whether specific files caused a regression. With
all modified files checked out, the entire working tree
was reset and no stash or WIP commit existed to recover
from.

## Anchor Freshness Is a Second Failure Surface

A correctly-formed command is not a safe command. Restoring
with `git checkout <SHA> -- <file>` obeys the rule above and
still destroys work if `<SHA>` is stale.

**Read the anchor on the spot** — `git rev-parse HEAD` —
immediately before restoring. **Never use a SHA that arrived
in a message**, including:

- an implementor's "final SHA" in a handoff
- a lead's "I verified this is the current tip"

Both expire during review. A reviewer followed the
no-bare-checkout rule exactly, restored against the SHA the
implementor's handoff named, and wiped 39 lines of new
integration tests from the working tree — the implementor had
committed again while the review was running. The work
survived only because it happened to be committed; uncommitted
it would have been gone.

Whoever submits for review keeps the working tree still until
the review returns. If you do change it, say so with the new
SHA — silence is what makes the reviewer's anchor stale.

## Mutation Happens in a Separate Worktree

When verifying a test by breaking the code it covers, never
edit the shared working tree. Check out the SHA under review
into a worktree outside the repository, break the code and run
the test there, then remove it:

```
wt=$(mktemp -d)
git worktree add --detach "$wt" <sha-under-review>
git worktree remove --force "$wt"
```

The shared tree belongs to the implementor, who may still be
editing it. A backup-and-restore there can write back a
version that matches no commit, and any file left there — a
backup, a probe test — can leak into the suite or the commit.
A separate worktree has nothing to restore, leaves nothing
behind in the shared tree, and stays pinned to the SHA under
review however the shared tree moves.

If the test needs untracked setup — installed dependencies,
env files — prepare it inside the worktree. Inconvenient setup
is not a reason to mutate the shared tree.

## Scope

This applies to any agent with Bash access.
