#!/usr/bin/env python3
"""Keep a teammate from going idle while a command it ran in the background is unfinished or unread.

A teammate that ends its turn is not woken when its background command finishes: the
completion notice waits in its queue until some other message arrives, and the team
stalls. Commands moved to the background by a timeout or Ctrl+B behave the same way.

tag   (PreToolUse, Bash): append "# cc-agent=<agent_id>" so the agent's shells can be found with ps.
track (PostToolUse):      remember the agent's live tagged shells after each tool call.
idle  (TeammateIdle):     report shells that ended since the last tool call; hold for live ones.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time

# The longest full test suite observed across projects took about 370s; twice that is
# covered by MAX_HOLDS waits, each short enough that the teammate stays reachable in
# between. WAIT_SECONDS must stay below the TeammateIdle hook timeout in settings.json.
WAIT_SECONDS = 300
MAX_HOLDS = 3

mode = sys.argv[1]
d = json.load(sys.stdin)
agent = d.get('agent_id')
if not agent:
    sys.exit(0)

if mode == 'tag':
    tool_input = dict(d['tool_input'])
    # A comment on its own line is ignored by permission matching but stays in the shell's argv.
    tool_input['command'] += '\n# cc-agent=' + agent
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'updatedInput': tool_input}}))
    sys.exit(0)


def live_shells():
    tag = re.compile(r"# cc-agent=" + re.escape(agent) + r"'")
    # Without -A, ps lists only processes with a controlling terminal, which these shells lack.
    out = subprocess.run(['ps', '-ww', '-A', '-o', 'pid=,command='], capture_output=True, text=True).stdout
    return [line.split(None, 1)[0] for line in out.splitlines() if tag.search(line)]


def output_path(pid):
    try:
        return os.readlink(f'/proc/{pid}/fd/1')
    except OSError:
        out = subprocess.run(['lsof', '-a', '-p', pid, '-d', '1', '-Fn'], capture_output=True, text=True).stdout
        return next((line[1:] for line in out.splitlines() if line.startswith('n')), 'unknown')


state_path = os.path.join(tempfile.gettempdir(), f"cc-agentbg-{d['session_id']}-{agent}.json")
try:
    with open(state_path) as f:
        state = json.load(f)
except (OSError, ValueError):
    state = {'live': {}, 'holds': {}}


def save():
    with open(state_path, 'w') as f:
        json.dump(state, f)


live = live_shells()

if mode == 'track':
    # A shell that ended during this tool call has its notice delivered with the tool result.
    state['live'] = {pid: state['live'].get(pid) or output_path(pid) for pid in live}
    save()
    sys.exit(0)

ended = {pid: path for pid, path in state['live'].items() if pid not in live}
if ended:
    for pid in ended:
        del state['live'][pid]
    save()
    sys.stderr.write(
        f"A command you ran in the background has finished since your last tool call. Output: {', '.join(ended.values())}. "
        'If you have not read its result yet, read it and continue your task. If you already handled it, end your turn.\n')
    sys.exit(2)
if not live:
    sys.exit(0)

pid = live[0]
path = state['live'].get(pid) or output_path(pid)
state['live'][pid] = path
holds = state['holds'].get(pid, 0)
if holds >= MAX_HOLDS:
    save()
    sys.exit(0)
state['holds'][pid] = holds + 1
save()

deadline = time.time() + WAIT_SECONDS
while time.time() < deadline and pid in live_shells():
    time.sleep(2)
if pid not in live_shells():
    del state['live'][pid]
    save()
    sys.stderr.write(f'Your background command has finished. Its output is in {path}. Read it and continue your task; do not end your turn yet.\n')
elif holds + 1 >= MAX_HOLDS:
    sys.stderr.write(
        f'Your background command is still running (output: {path}) and this was the last wait; next time you end your turn '
        'you will go idle without being woken when it finishes. Before ending your turn, message the team lead: name the '
        'command you are waiting on and its output path. If it is meant to keep running, such as a server, carry on with your task.\n')
else:
    sys.stderr.write(
        f'Your background command is still running (output: {path}). If you need its result, end your turn again and you '
        'will be held until it finishes. If it is meant to keep running, such as a server, carry on with your task.\n')
sys.exit(2)
