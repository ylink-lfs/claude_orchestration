#!/usr/bin/env bash

# Runs once after the container is created (postCreateCommand).
# Use this for one-time setup that only needs to happen on first build.

set -euo pipefail

# Fix volume ownership — Docker creates the pnpm store and shell history
# volumes as root, but pnpm and fish run as vscode and need write access.
sudo chown -R vscode:vscode /home/vscode/.local/share/pnpm /home/vscode/.local/share/fish

npm install -g @cometix/ccline

# Mirror the host's skill layout: ~/.claude/skills is a symlink to
# ~/.agents/skills there, and Claude Code resolves skills through that
# symlink. /home/vscode/.agents/skills is bind-mounted directly (see
# devcontainer.json), so recreate the same symlink here.
if [ ! -e /home/vscode/.claude/skills ]; then
  ln -s /home/vscode/.agents/skills /home/vscode/.claude/skills
fi

# Language servers for the official TypeScript and Python code intelligence
# plugins (installed by post-start.sh); gopls comes with the Go feature.
npm install -g --no-fund --no-audit typescript typescript-language-server pyright
