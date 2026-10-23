# Claude Orchestration Kit

A toolkit for building Claude Code multi-agent orchestration
setups. Provides design rules, audit skills, a test harness,
and conventions for creating blueprints — `.claude/`
configurations that turn a Claude Code session into a
coordinated multi-agent team. The three included blueprints
are products of this framework, not the whole project.

## Build and Test

This project runs in a Docker container. Install `uv` on
first use — it is required to run the test suite.

```sh
which uv || curl -LsSf https://astral.sh/uv/install.sh | sh
uv run pytest blueprints/workflow/tests/ -m static -v
uv run pytest blueprints/autonomous/tests/ -m static -v
uv run pytest blueprints/direct-review/tests/ -m static -v
```

## Components

| Path | Purpose |
|---|---|
| `/.claude/rules/` | Design rules for blueprint development (never copied) |
| `/.claude/skills/` | Audit skills: `/blueprint-audit`, `/cache-audit` (never copied) |
| `blueprints/workflow/` | Clarify-first blueprint — user chooses workflow |
| `blueprints/autonomous/` | Autonomous blueprint — plan queue + developer |
| `blueprints/direct-review/` | Advisor-first blueprint — lead implements on request, per-task user review |
| `devcontainer_templates/` | Devcontainer setup for sandboxed agent execution |
| `CONTRIBUTING.md` | How to develop and extend blueprints |

### workflow

Clarify-first: the lead clarifies the task, writes a plan
(reviewed by the plan-reviewer subagent and approved by
the user), then presents workflow options. The user
chooses: Direct-Review for simple tasks, Develop-Review
(Supervised or Autonomous) for complex ones, or TDD
User-in-the-Loop. 4 team agents (Developer, Test Engineer,
Security Engineer, Reviewer) plus the lead, with three
on-demand subagents launched during planning and TDD
entry: `design-advisor` (proposes design improvements and
preparatory refactors before every code-changing plan),
`plan-reviewer` (reviews draft plans before user
presentation), and `test-list` (converts an example
mapping into a minimum required test list). Workflows
defined as separate files — adding one requires no
changes to CLAUDE.md or agents.

### autonomous

Autonomous after clarification: the lead clarifies, writes
a plan, manages a plan queue. For each task, the lead
assesses risk and directs the developer to consult advisors
when warranted. The developer implements, the reviewer
approves, and the lead commits. 4 team agents (Developer,
Reviewer, Test Engineer, Security Engineer) plus the lead
and two subagents: `design-advisor` (proposes design
improvements and preparatory refactors before every
code-changing plan) and `plan-reviewer` (launched before
user plan presentation). Teammates are task-scoped and
replaced between task slices. Execution assumes no one is
watching: after plan approval the lead stops for the user
only to lower an acceptance target or to avoid damage,
while staying available for new requests.

### direct-review

Advisor first: the lead clarifies, weighs options, and
recommends without editing files. It implements only on an
explicit user request — plan (plan-reviewer + user
approval), then one task at a time: `risk-assessment.md`
selects Reviewer-only, Security-Hybrid (Security Engineer
pre/post sign-offs), or escalation to the user. The
Reviewer approves each task, the user reviews it, the lead
commits and starts the plan's next task. 2 team agents
(Reviewer, Security Engineer) plus the lead and two
subagents: `design-advisor` (proposes design improvements
and preparatory refactors for options and plans that
change code; adopted refactors get tests pinning the
behavior first) and `plan-reviewer`. No `workflows/`
directory.

### devcontainer_templates

Docker-based sandboxing for agent execution. Project-scoped
volume for Claude config, dual auth mode (`proxy`/`oauth`)
via `CLAUDE_AUTH` env var, base and audio variants.

## Language

Everything written to this repository is in English —
blueprint files, rules, skills, tests, docs, and commit
messages — regardless of the language the user chats in.
There are no exceptions: translate quoted non-English
material, such as user feedback or notes from a target
project, before it goes into a file or a commit message.
Chat replies may use the user's language.

## Conventions

<!-- Agents: add non-obvious project conventions discovered
during work — things a future agent would need to know to
avoid mistakes. One line each. Remove when no longer true. -->

- Two levels of `.claude/`: project-level (`/.claude/`) is tooling for this repo, never copied; blueprint-level (`blueprints/*/.claude/`) gets copied to target projects
- Use "lead" not "orchestrator" — Claude Code's native term for the session that manages the team
- Every directive in blueprint markdown files must include its rationale (see `reasoned-instructions.md` rule)
- Agent files define role and capability only — no named teammates, no workflow-specific coordination (see `agent-design.md` rule)
- Agent `name:` fields in frontmatter use lowercase hyphenated form: `developer`, `test-engineer`
- Use official terminology: "launch" subagents, "spawn" and "shut down" teammates, "message" within teams (see `terminology.md` rule)
- Rule files and CLAUDE.md files target under 200 lines — agent adherence degrades beyond that threshold
- Blueprint files are cached at prompt cache level 3 — no dynamic content (dates, counters, versions)
- Test suite uses pytest with `-m static` marker for structural verification

## Quota Cost of Transcript-Replay Experiments

Evaluating blueprint changes by replaying local
transcripts through headless `claude -p` calls drains
the subscription quota far faster than it looks: every
call is small, but a full-dataset run fans out to
hundreds of calls in parallel. One afternoon run of about
470 calls used roughly 13% of the weekly quota and nearly
filled the 5-hour window. In an earlier run, the 5-hour
limit hit mid-flight, and the aborted calls were billed
but their output was discarded.

Calibration from that run (API list price as reported by
`total_cost_usd`; about $85 ≈ 13% weekly, so about $6.5
per 1%):

| Call shape | Tokens per call | Cost per call | 1% weekly ≈ |
|---|---|---|---|
| Single-shot, no tools, ~15k input, Sonnet | ~15k cache write, ~1k out | $0.04–0.07 | 100–150 calls |
| Same, Opus | same | ~$0.16 | ~40 calls |
| Agentic replay (Read/Glob/Grep on a repo tree), ~25 turns, ~210k peak context, Sonnet | ~1.5M cache read, ~220k write, ~20k out | ~$1.4 | ~5 runs |
| Same, Opus | same | ~$2.8 | ~2–3 runs |

Agentic replays dominate because each turn re-reads the
whole accumulated context. Scale with
`calls × cost per call`, not with the size of the dataset.
Treat a run of about $85 as one full 5-hour window.

Before any full-scale run:

1. Pilot 4–8 samples and read `total_cost_usd` from
   each result.
2. Extrapolate to the planned call count. Every repeat,
   rater, and model arm multiplies it.
3. Show the user the estimate as a weekly-quota
   percentage, and get approval before launching.
4. Prefer a sample subset, Sonnet, or single-shot
   judging over stored reports, rather than replaying
   the full dataset.
5. Keep concurrency low enough that a 5-hour limit
   cannot abort calls that are already in flight.

The calibration ties to one account plan and the current
model prices. Re-derive it if either changes.

## References

<!-- Agents: add authoritative sources used to make
implementation decisions. One line each. -->

- [Claude Code documentation](https://code.claude.com/docs)

## Session Checklist

Before ending a session that modified blueprint files:

1. Verify all changes are safe, sound, and concise
2. Verify this file (`CLAUDE.md`) still reflects reality
3. Verify root `README.md` matches current blueprints
4. Run `uv run pytest blueprints/<name>/tests/ -m static -v`
