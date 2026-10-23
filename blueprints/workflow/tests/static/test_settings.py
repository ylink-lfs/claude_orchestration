"""Tests that settings.json contains required configuration."""

import json

import pytest

from blueprint_contracts import REQUIRED_SETTINGS
from conftest import SETTINGS_FILE

pytestmark = pytest.mark.static


@pytest.fixture
def settings():
    return json.loads(SETTINGS_FILE.read_text())


@pytest.mark.parametrize("key,expected", list(REQUIRED_SETTINGS.items()))
def test_top_level_setting(settings, key, expected):
    actual = settings.get(key)
    assert actual == expected, (
        f"settings.json[{key!r}] should be {expected!r}, got {actual!r}"
    )


def test_no_auto_memory_directory(settings):
    """settings.json must not set autoMemoryDirectory.

    Claude Code silently ignores a relative value and an absolute one is
    machine-specific, so /ensure-ai-dirs writes the absolute path to the
    gitignored settings.local.json instead.
    """
    assert "autoMemoryDirectory" not in settings, (
        "settings.json must not set autoMemoryDirectory — a relative value "
        "is silently ignored and an absolute one is machine-specific; "
        "/ensure-ai-dirs writes it to .claude/settings.local.json"
    )


def test_no_default_mode(settings):
    """settings.json must not set defaultMode — plan mode enforcement is unreliable."""
    permissions = settings.get("permissions", {})
    assert "defaultMode" not in permissions


def test_subagent_authorization_hook(settings):
    """A SessionStart hook must inject the standing subagent authorization.

    Claude Code injects a session-level instruction not to launch
    subagents unless the user requested it. That instruction tests
    a fact about the conversation, so a claim written in project
    config does not satisfy it — the authorization has to reach the
    message stream, which is what this hook does. Without it the
    lead stops mid-planning to ask permission for the plan-reviewer.
    """
    entries = settings.get("hooks", {}).get("SessionStart", [])
    assert entries, "settings.json must define a SessionStart hook"

    authorizing = [
        entry
        for entry in entries
        if any(
            "authorized" in hook.get("command", "")
            and "subagents" in hook.get("command", "")
            for hook in entry.get("hooks", [])
        )
    ]
    assert authorizing, (
        "no SessionStart hook emits a subagent authorization"
    )

    # Compaction summarizes the message stream, so an authorization
    # that only fires on startup silently disappears mid-session.
    assert any(
        "compact" in entry.get("matcher", "") for entry in authorizing
    ), "the authorization hook's matcher must cover 'compact'"


def test_no_conditional_tool_loading(settings):
    """No defer_loading in settings (tool set must be fixed)."""
    settings_text = SETTINGS_FILE.read_text()
    assert "defer_loading" not in settings_text, (
        "settings.json must not use defer_loading (tool set must be fixed per caching rules)"
    )
