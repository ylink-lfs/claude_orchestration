"""Tests that lead instructions (CLAUDE.md) contain required contracts."""

import re

import pytest

from conftest import CLAUDE_MD

pytestmark = pytest.mark.static


@pytest.fixture
def lead_instructions():
    return CLAUDE_MD.read_text()


def _extract_section(text, heading):
    """Extract content from ## heading to the next ## heading or EOF."""
    pattern = rf"^## {re.escape(heading)}\b.*?(?=\n## |\Z)"
    match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
    return match.group(0) if match else ""


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


# --- Plan review cycle: severity gate ---


def test_presentation_always_includes_override_list(lead_instructions):
    """Every declined Blocking finding reaches the user, even when there are none."""
    text = " ".join(lead_instructions.lower().split())
    for phrase in (
        "always present the override list",
        "even when it is empty",
        "a decline must quote the plan text that refutes the finding",
    ):
        assert phrase in text, (
            f"CLAUDE.md must say {phrase!r} — declining a reviewer's "
            f"blocking finding is the author judging its own plan, so the "
            f"user sees every such call"
        )
