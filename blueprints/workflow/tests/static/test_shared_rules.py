"""Tests that shared files stay in sync across blueprints.

Some files exist in both blueprints (workflow and
autonomous) and are intended to be identical — rule files
encoding cross-cutting concerns like simplicity, code
style, and testing principles, plus the plan review
checklist. When one copy is updated but the other is not,
agents in the stale blueprint follow outdated guidance.
These tests catch that drift.
"""

from pathlib import Path

import pytest

from conftest import ENSURE_AI_DIRS_SKILL, REPO_ROOT, RULES_DIR

pytestmark = pytest.mark.static

WORKFLOW_RULES = RULES_DIR
AUTONOMOUS_RULES = REPO_ROOT / "blueprints" / "autonomous" / ".claude" / "rules"

AUTONOMOUS_ENSURE_AI_DIRS = (
    REPO_ROOT / "blueprints" / "autonomous" / ".claude" / "skills" / "ensure-ai-dirs"
)

# Skill templates shared verbatim between blueprints. The
# other ensure-ai-dirs templates (plan-format.md,
# claude-md-template.md, SKILL.md) differ by design and are
# deliberately absent here.
SHARED_SKILL_TEMPLATES = ["plan-review-checklist.md"]

SHARED_HOOK_SCRIPTS = ["agentbg.py"]

# Files that exist in both blueprints but differ
# intentionally — they contain blueprint-specific content.
KNOWN_DIVERGENT: set[str] = {
    "advisor-gate-independence.md",
    "communication-hygiene.md",
    "risk-assessment.md",
    "safe-git.md",
}


def _shared_rule_files() -> list[str]:
    """Return filenames that exist in both blueprints' rules dirs."""
    if not WORKFLOW_RULES.is_dir() or not AUTONOMOUS_RULES.is_dir():
        return []
    workflow_names = {p.name for p in WORKFLOW_RULES.glob("*.md")}
    autonomous_names = {p.name for p in AUTONOMOUS_RULES.glob("*.md")}
    return sorted(workflow_names & autonomous_names - KNOWN_DIVERGENT)


@pytest.mark.parametrize("filename", _shared_rule_files(), ids=lambda f: f)
def test_shared_rule_file_is_identical(filename):
    workflow_file = WORKFLOW_RULES / filename
    autonomous_file = AUTONOMOUS_RULES / filename
    workflow_text = workflow_file.read_text()
    autonomous_text = autonomous_file.read_text()
    assert workflow_text == autonomous_text, (
        f"Shared rule file {filename} has drifted between blueprints. "
        f"Update both copies to match, or add the filename to "
        f"KNOWN_DIVERGENT if the difference is intentional."
    )


@pytest.mark.parametrize("filename", SHARED_SKILL_TEMPLATES, ids=lambda f: f)
def test_shared_skill_template_is_identical(filename):
    workflow_file = ENSURE_AI_DIRS_SKILL / filename
    autonomous_file = AUTONOMOUS_ENSURE_AI_DIRS / filename
    assert workflow_file.exists(), f"Missing {filename} in workflow blueprint"
    assert autonomous_file.exists(), f"Missing {filename} in autonomous blueprint"
    assert workflow_file.read_text() == autonomous_file.read_text(), (
        f"Shared skill template {filename} has drifted between blueprints. "
        f"Update both copies to match, or remove the filename from "
        f"SHARED_SKILL_TEMPLATES if the difference is intentional."
    )


@pytest.mark.parametrize("filename", SHARED_HOOK_SCRIPTS, ids=lambda f: f)
def test_shared_hook_script_is_identical(filename):
    workflow_file = REPO_ROOT / "blueprints" / "workflow" / ".claude" / "hooks" / filename
    autonomous_file = REPO_ROOT / "blueprints" / "autonomous" / ".claude" / "hooks" / filename
    assert workflow_file.exists(), f"Missing hook {filename} in workflow blueprint"
    assert autonomous_file.exists(), f"Missing hook {filename} in autonomous blueprint"
    assert workflow_file.read_text() == autonomous_file.read_text(), (
        f"Shared hook script {filename} has drifted between blueprints. "
        f"Update both copies to match, or remove the filename from "
        f"SHARED_HOOK_SCRIPTS if the difference is intentional."
    )
