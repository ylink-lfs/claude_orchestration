"""Tests that agent definition files satisfy structural and behavioral contracts."""

import pytest

from blueprint_contracts import AGENT_EFFORT, AGENT_FILES, AGENT_MODELS, AGENT_TOOLS
from conftest import AGENTS_DIR, RULES_DIR, parse_frontmatter

pytestmark = pytest.mark.static


@pytest.mark.parametrize(
    "agent_name,filename",
    list(AGENT_FILES.items()),
    ids=list(AGENT_FILES.keys()),
)
def test_agent_has_name(agent_name, filename):
    """Frontmatter 'name' must match the contract key exactly."""
    fm = parse_frontmatter(AGENTS_DIR / filename)
    assert fm.get("name") == agent_name, (
        f"Agent {filename}: expected name {agent_name!r}, got {fm.get('name')!r}"
    )


@pytest.mark.parametrize(
    "agent_name,filename",
    list(AGENT_FILES.items()),
    ids=list(AGENT_FILES.keys()),
)
def test_agent_has_description(agent_name, filename):
    """Frontmatter 'description' must be a non-empty string."""
    fm = parse_frontmatter(AGENTS_DIR / filename)
    desc = fm.get("description", "")
    assert isinstance(desc, str) and desc.strip(), (
        f"Agent {filename}: description must be a non-empty string"
    )


@pytest.mark.parametrize(
    "agent_name,filename",
    list(AGENT_FILES.items()),
    ids=list(AGENT_FILES.keys()),
)
def test_agent_model_matches(agent_name, filename):
    """Frontmatter 'model' must match the contract."""
    fm = parse_frontmatter(AGENTS_DIR / filename)
    expected = AGENT_MODELS[agent_name]
    assert fm.get("model") == expected, (
        f"Agent {filename}: expected model {expected!r}, got {fm.get('model')!r}"
    )


@pytest.mark.parametrize(
    "agent_name,filename",
    list(AGENT_FILES.items()),
    ids=list(AGENT_FILES.keys()),
)
def test_agent_effort_matches(agent_name, filename):
    """Frontmatter 'effort' must match the contract."""
    fm = parse_frontmatter(AGENTS_DIR / filename)
    expected = AGENT_EFFORT[agent_name]
    assert fm.get("effort") == expected, (
        f"Agent {filename}: expected effort {expected!r}, got {fm.get('effort')!r}"
    )


@pytest.mark.parametrize(
    "agent_name,filename",
    list(AGENT_FILES.items()),
    ids=list(AGENT_FILES.keys()),
)
def test_agent_tools_match_exactly(agent_name, filename):
    """Frontmatter 'tools' must match the contract set exactly."""
    fm = parse_frontmatter(AGENTS_DIR / filename)
    actual = set(fm.get("tools", []))
    expected = AGENT_TOOLS[agent_name]
    assert actual == expected, (
        f"Agent {filename}: expected tools {sorted(expected)}, got {sorted(actual)}"
    )


def _agent_text(agent_name: str) -> str:
    return (AGENTS_DIR / f"{agent_name}.md").read_text().lower()


def test_comment_guidance_prefers_self_explanatory_code():
    developer_text = _agent_text("developer")
    simplicity_text = (RULES_DIR / "simplicity.md").read_text().lower()

    assert "self-explanatory code" in developer_text
    assert "comments drift from behavior" in developer_text
    assert "self-explanatory code" in simplicity_text
    assert "comments drift from behavior" in simplicity_text


def test_reviewer_does_not_block_on_missing_explanatory_comments():
    text = _agent_text("reviewer")

    assert "not a finding and must never\n  block approval" in text
    assert "required by\n  the task but missing" in text


def test_mutation_verification_runs_in_a_separate_worktree():
    reviewer_text = " ".join(_agent_text("reviewer").split())
    safe_git_text = (RULES_DIR / "safe-git.md").read_text()

    assert "separate worktree" in reviewer_text
    assert "never mutate the shared working tree" in reviewer_text
    assert ".bak" not in reviewer_text
    assert 'git worktree add --detach "$wt"' in safe_git_text
    assert ".bak" not in safe_git_text
