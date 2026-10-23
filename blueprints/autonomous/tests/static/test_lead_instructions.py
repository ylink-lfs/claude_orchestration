"""Tests that lead instructions (CLAUDE.md) contain required contracts."""

import re

import pytest

from conftest import CLAUDE_MD, RULES_DIR

pytestmark = pytest.mark.static


@pytest.fixture
def lead_instructions():
    return CLAUDE_MD.read_text()


@pytest.fixture
def handoff_verification():
    return (RULES_DIR / "handoff-verification.md").read_text()


@pytest.fixture
def commit_sequence():
    return (RULES_DIR / "commit-sequence.md").read_text()


def _extract_section(text, heading):
    """Extract content from ## heading to the next ## heading or EOF."""
    pattern = rf"^## {re.escape(heading)}\b.*?(?=\n## |\Z)"
    match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
    return match.group(0) if match else ""


# --- Plan progress ---


def test_lead_owns_plan_updates_during_execution(lead_instructions):
    """Lead must own plan progress updates during execution."""
    text = lead_instructions.lower()
    assert "update the plan" in text and "mark all checkboxes" in text, (
        "CLAUDE.md must instruct the lead to update the plan after "
        "each task approval by marking every checkbox. Plan files are "
        "not committed, so the working tree is the only record"
    )


def test_plan_files_are_not_committed(lead_instructions):
    """Plan files must be documented as uncommitted local records."""
    text = lead_instructions.lower()
    assert "do not commit plan files" in text, (
        "CLAUDE.md must state that plan files are never committed — "
        "the plans directory is normally gitignored, so an instruction "
        "to stage a plan file either fails or overrides that policy"
    )


def test_progress_evidence_is_the_working_tree(lead_instructions):
    """Lead must know checkboxes are local and can disagree with git."""
    text = lead_instructions.lower()
    assert "progress evidence" in text and "working" in text, (
        "CLAUDE.md must state where progress evidence lives now that "
        "plan files are not committed, and that commits win when the "
        "checkboxes disagree with them"
    )


# --- Skill-output commits ---


def test_skill_output_commit_rule_exists(lead_instructions):
    """Lead instructions must define the skill-output commit rule."""
    assert "skill-output commits" in lead_instructions.lower(), (
        "CLAUDE.md must contain a 'Skill-Output Commits' section — "
        "this is the unified rule that allows the lead to commit "
        "files that skills explicitly name as outputs"
    )


def test_skill_output_commit_scoped_to_skill_outputs(commit_sequence):
    """The rule must limit commits to files a skill's SKILL.md names."""
    text = commit_sequence.lower()
    assert "`skill.md`" in text and "explicitly\nnames as outputs" in text, (
        "The skill-output commit rule must state that only files a "
        "skill's SKILL.md explicitly names as outputs may be committed "
        "by the lead — without this constraint, the lead can use the "
        "rule to bypass the reviewer for arbitrary files"
    )


def test_skill_output_commit_immediately_after(commit_sequence):
    """The rule must require committing immediately after the skill."""
    assert "immediately after" in commit_sequence.lower(), (
        "The skill-output commit rule must require committing "
        "immediately after the skill completes — deferred commits "
        "can accumulate unrelated changes under the skill-output "
        "exception"
    )


def test_skill_output_commit_not_general_permission(commit_sequence):
    """The rule must explicitly state it is not a general commit permission."""
    text = commit_sequence.lower()
    assert "not a general permission" in text, (
        "The skill-output commit rule must explicitly state that it "
        "is not a general permission to commit — without this "
        "guardrail, the lead can rationalize any commit as a "
        "'skill-like' operation"
    )


def test_skill_output_commit_removal_test(commit_sequence):
    """The rule must include the removal test for identifying skill outputs."""
    text = commit_sequence.lower()
    assert "removed the skill invocation" in text, (
        "The skill-output commit rule must include the removal test: "
        "'if you removed the skill invocation, would this file still "
        "need to exist?' — this gives the lead a bright-line test "
        "to distinguish skill infrastructure from project work"
    )


def test_skill_output_commit_covers_project_init(commit_sequence):
    """The rule must list /project-init as a covered skill."""
    assert "/project-init" in commit_sequence, (
        "The skill-output commit rule must explicitly list "
        "/project-init outputs — without this, the lead has no "
        "guidance on committing the project context files"
    )


def test_idle_notification_carries_an_obligation(lead_instructions):
    """An idle notification must oblige the lead to check the handoff."""
    text = lead_instructions.lower()
    assert "idle notification" in text and "handoff check" in text, (
        "CLAUDE.md must tie teammate idle notifications to the handoff "
        "check. The notification is the only signal separating 'someone "
        "is working' from 'a handoff was dropped'; an earlier version "
        "called it informational and a dropped handoff cost ~6 hours"
    )
    assert "handoff-verification" in text, (
        "CLAUDE.md must point at handoff-verification.md for the "
        "procedure — the obligation without the procedure leaves the "
        "lead to invent the check"
    )


def test_dispatch_subscribes_to_idle(lead_instructions):
    """Dispatch must set notify_when_idle so the check gets armed."""
    assert "notify_when_idle" in lead_instructions, (
        "CLAUDE.md must require notify_when_idle: true on dispatch. "
        "Setting a field at send time is checkable; remembering to "
        "poll later is not"
    )


def _extract_subsection(text, heading):
    """Extract content from ### heading to the next ## or ### heading."""
    pattern = rf"^### {re.escape(heading)}\b.*?(?=\n#{{2,3}} |\Z)"
    match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
    return match.group(0) if match else ""


def _extract_numbered_step(text, number, heading):
    """Extract one numbered step from the subsection under `heading`."""
    section = _extract_subsection(text, heading)
    pattern = rf"^{number}\. .*?(?=^\d+\. |\Z)"
    match = re.search(pattern, section, re.DOTALL | re.MULTILINE)
    return match.group(0) if match else ""


@pytest.fixture
def cycle_step(lead_instructions):
    return _extract_numbered_step(lead_instructions, 6, "After Reviewer Approval")


# --- Instance cycling leaves no empty window ---


def test_cycling_spawns_before_shutdown(cycle_step):
    """The next task's instances must be spawned before the current ones exit."""
    assert cycle_step, "After Reviewer Approval must have a numbered step 6"
    spawn = cycle_step.find("spawn")
    shutdown = cycle_step.find("shutdown request")
    assert spawn != -1 and shutdown != -1, (
        "step 6 must mention both the spawn and the shutdown request"
    )
    assert spawn < shutdown, (
        "step 6 must spawn the next task's instances before shutting the "
        "current ones down. Shutting down first opens a window with no "
        "teammate alive, and a teammate idle notification is the only "
        "event that can restart a stopped lead — a production session "
        "sent the shutdown requests, never spawned, and sat idle 26 "
        "minutes until the user asked why nothing was running"
    )


def test_cycling_resends_plan_before_shutdown(cycle_step):
    """The plan re-send must precede the shutdown — it is what arms the check."""
    resend = cycle_step.find("plan file path")
    shutdown = cycle_step.find("shutdown request")
    assert resend != -1, "step 6 must re-send the plan file path to the new reviewer"
    assert resend < shutdown, (
        "the plan re-send must move with the spawn, ahead of the "
        "shutdown. Spawning alone does not arm the idle subscription; "
        "a SendMessage does, and this re-send is the only one in the "
        "cycle that lands before the next dispatch"
    )


def test_cycling_between_tasks_is_not_a_team_down_window(commit_sequence):
    """No rule may still describe the cycling gap as a team-down window."""
    text = commit_sequence.lower()
    assert "cycling between tasks is **not** a team-down window" in text, (
        "commit-sequence.md must state that cycling is not a team-down "
        "window. The removed bullet was the standing authorization a "
        "lead cited when it paused a plan to ask about optional work "
        "it could do 'in the next team-down window'"
    )


def test_handoff_check_covers_a_missing_dispatch(handoff_verification):
    """The lead must recognise itself as the party owing the next move."""
    text = handoff_verification.lower()
    assert "may be you" in text, (
        "handoff-verification.md must include the branch where the lead "
        "itself owes the next move — instances spawned, commit landed, "
        "no dispatch sent. Without it the check runs to completion and "
        "concludes nothing: a production lead ran the whole check with "
        "every teammate shut down and went to work on an optional "
        "comment fix instead of dispatching"
    )
    assert "step 7" in text, (
        "the branch must name the action (After Reviewer Approval "
        "step 7) — recognising the state without naming the recovery "
        "leaves the lead to invent one"
    )


def test_execution_is_unattended(lead_instructions):
    """The lead must know execution runs with no one watching."""
    text = lead_instructions.lower()
    assert "unattended" in text, (
        "CLAUDE.md must declare that execution runs unattended, with "
        "the two cases that still stop for the user — otherwise the "
        "lead stops overnight on a question no one will answer"
    )


def test_skill_output_commit_excludes_plans_directory(commit_sequence):
    """Plans-directory outputs must be excluded from skill commits."""
    text = commit_sequence.lower()
    assert "/ensure-ai-dirs" in text and "gitignored" in text, (
        "commit-sequence.md must state that /ensure-ai-dirs writes into "
        "the gitignored plans directory and therefore produces nothing "
        "to commit — otherwise the lead retries a staging step that "
        "cannot succeed"
    )


# --- No standalone startup section ---


def test_no_startup_section(lead_instructions):
    """Lead instructions must not have a standalone Startup section.

    Startup procedures that rely on proactive execution before
    the user's first message are not enforced by Claude Code.
    Preconditions belong in the Clarification section where
    they fire on user interaction.
    """
    headings = re.findall(r"^## .+", lead_instructions, re.MULTILINE)
    startup_headings = [h for h in headings if "startup" in h.lower()]
    assert not startup_headings, (
        f"CLAUDE.md must not have a Startup section — "
        f"found: {startup_headings}. Preconditions belong in "
        f"the Clarification section"
    )


# --- Clarification preconditions ---


def test_project_init_in_clarification(lead_instructions):
    """Clarification section must include /project-init check.

    Without this, new projects lack the context all agents
    need to produce project-appropriate code.
    """
    clarification = _extract_section(lead_instructions, "Clarification")
    assert "/project-init" in clarification, (
        "The Clarification section must reference /project-init — "
        "without this precondition, new projects get no project "
        "context and agents default to generic patterns"
    )


def test_existing_plan_scan_in_clarification(lead_instructions):
    """Clarification section must instruct scanning for existing plans.

    Without this, incomplete work from prior sessions is
    silently ignored when the lead starts a new session.
    """
    clarification = _extract_section(
        lead_instructions, "Clarification"
    ).lower()
    assert "existing plan" in clarification, (
        "The Clarification section must instruct the lead to "
        "scan for existing plan files — without this, prior "
        "session work is silently ignored"
    )


def test_new_file_check_uses_summary_not_stat(commit_sequence):
    assert 'git show --summary HEAD | grep "create mode"' in commit_sequence
    assert 'git show --stat HEAD | grep "create mode"' not in commit_sequence, (
        "git show --stat never prints 'create mode' lines, so the grep "
        "cannot detect a dropped new file"
    )
