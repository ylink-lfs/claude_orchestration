"""Tests for the hook that keeps teammates from stalling on background commands.

A teammate that ends its turn is not woken when a command it ran
in the background finishes: the completion notice waits in its
queue until some other message arrives, and the team sits idle.
`.claude/hooks/agentbg.py` tags each Bash command with the agent
that ran it, tracks that agent's live shells, and holds the
teammate at TeammateIdle until it has seen the result.
"""

import json
import os
import re
import subprocess
import sys

import pytest

from conftest import CLAUDE_DIR, SETTINGS_FILE

pytestmark = pytest.mark.static

HOOK_SCRIPT = CLAUDE_DIR / "hooks" / "agentbg.py"

# Hooks run in the agent's current directory, so a relative path
# breaks once an agent cd's into a subdirectory, and an absolute
# path differs between host and devcontainer.
HOOK_COMMAND = '"$CLAUDE_PROJECT_DIR"/.claude/hooks/agentbg.py'


@pytest.fixture
def settings():
    return json.loads(SETTINGS_FILE.read_text())


def _hooks(settings, event):
    return [
        hook
        for entry in settings.get("hooks", {}).get(event, [])
        for hook in entry.get("hooks", [])
    ]


def _run(mode, payload, tmp_path):
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), mode],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**os.environ, "TMPDIR": str(tmp_path)},
    )


@pytest.mark.parametrize(
    "event,mode",
    [("PreToolUse", "tag"), ("PostToolUse", "track"), ("TeammateIdle", "idle")],
)
def test_hook_is_wired(settings, event, mode):
    commands = [hook.get("command") for hook in _hooks(settings, event)]
    assert f"{HOOK_COMMAND} {mode}" in commands


def test_tag_hook_matches_every_bash_call(settings):
    """Commands moved to the background by a timeout or Ctrl+B start in the foreground."""
    entries = settings["hooks"]["PreToolUse"]
    tagging = [
        entry for entry in entries
        if any(hook.get("command") == f"{HOOK_COMMAND} tag" for hook in entry["hooks"])
    ]
    assert tagging and all(entry.get("matcher") == "Bash" for entry in tagging)


def test_idle_hook_outlasts_its_wait(settings):
    """A hook cancelled mid-wait lets the teammate go idle unwoken."""
    wait = int(re.search(r"^WAIT_SECONDS = (\d+)$", HOOK_SCRIPT.read_text(), re.M).group(1))
    idle = [
        hook for hook in _hooks(settings, "TeammateIdle")
        if hook.get("command") == f"{HOOK_COMMAND} idle"
    ]
    assert idle and idle[0].get("timeout", 0) > wait


def test_hook_script_is_executable():
    assert os.access(HOOK_SCRIPT, os.X_OK)


def test_tag_appends_agent_comment_on_its_own_line(tmp_path):
    """A trailing comment line keeps permission rules matching; an inline one breaks redirects."""
    result = _run(
        "tag",
        {"session_id": "s", "agent_id": "a-test", "tool_input": {"command": "go test ./... > out.log", "run_in_background": True}},
        tmp_path,
    )

    assert result.returncode == 0
    updated = json.loads(result.stdout)["hookSpecificOutput"]["updatedInput"]
    assert updated == {"command": "go test ./... > out.log\n# cc-agent=a-test", "run_in_background": True}


def test_tag_leaves_lead_commands_unchanged(tmp_path):
    result = _run("tag", {"session_id": "s", "tool_input": {"command": "ls"}}, tmp_path)

    assert result.returncode == 0
    assert result.stdout == ""


def test_idle_releases_teammate_with_no_background_commands(tmp_path):
    result = _run("idle", {"session_id": "s", "agent_id": "a-test-none"}, tmp_path)

    assert result.returncode == 0


def test_idle_reports_command_that_ended_after_last_tool_call(tmp_path):
    """The notice of a command ending between the last tool call and idle is never delivered."""
    state = tmp_path / "cc-agentbg-s-a-test-ended.json"
    state.write_text(json.dumps({"live": {"999999": "/tmp/task.output"}, "holds": {}}))

    result = _run("idle", {"session_id": "s", "agent_id": "a-test-ended"}, tmp_path)

    assert result.returncode == 2
    assert "/tmp/task.output" in result.stderr
    assert json.loads(state.read_text())["live"] == {}
