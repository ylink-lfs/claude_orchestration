#!/usr/bin/env bash

# Copy host Claude configuration into the container volume.
#
# Auth mode is controlled by the CLAUDE_AUTH environment variable:
#   - "proxy"  (default): copies settings.json from host, which contains
#     API proxy config (Portkey env vars, custom headers, etc.)
#   - "oauth": never copies the host's .credentials.json — each container
#     runs 'claude login' once and keeps its own OAuth session in the
#     ~/.claude volume. Copies settings.json with the entire env
#     block and apiKeyHelper removed — the env block typically contains
#     proxy config that conflicts with OAuth. Any env vars needed in
#     oauth mode should be added to .devcontainer/.env.local instead.
#
# CLAUDE_AUTH is set via containerEnv in devcontainer.json (default: proxy).
# Override locally via .devcontainer/.env.local (gitignored).
#
# After the settings copy, updates Claude Code and installs the official
# plugins the project enables. Both go through claude-proxy.sh, the only
# process tree that gets the proxy.

set -euo pipefail

SEP="============================================================"
# The claude installer puts its binary here; only fish's config adds it.
export PATH="$HOME/.local/bin:$PATH"
CLAUDE="/workspace/.devcontainer/claude-proxy.sh"
PROJECT_SETTINGS="/workspace/.claude/settings.json"
OFFICIAL_MARKETPLACE="claude-plugins-official"
# Full https URL, never the owner/repo short form, which the CLI may clone
# over SSH.
OFFICIAL_MARKETPLACE_URL="https://github.com/anthropics/claude-plugins-official.git"

if [ -z "${CLAUDE_AUTH:-}" ]; then
  echo "ERROR: CLAUDE_AUTH is not set. Set it in devcontainer.json containerEnv"
  echo "or in .devcontainer/.env.local. Valid values: proxy, oauth"
  exit 1
fi
HOST_DIR="/home/vscode/.claude-host"
CONTAINER_DIR="/home/vscode/.claude"

echo "$SEP"
echo "Initializing Claude Settings (auth mode: $CLAUDE_AUTH)"
echo "$SEP"

mkdir -p "$CONTAINER_DIR"

case "$CLAUDE_AUTH" in
  proxy)
    HOST_SETTINGS="$HOST_DIR/settings.json"
    if [ -f "$HOST_SETTINGS" ]; then
      echo "Copying host settings.json (proxy mode)"
      cp "$HOST_SETTINGS" "$CONTAINER_DIR/settings.json"
    else
      echo "WARNING: No settings.json found at $HOST_SETTINGS"
      echo '{}' > "$CONTAINER_DIR/settings.json"
    fi
    ;;
  oauth)
    # Never copy the host's .credentials.json: OAuth refresh tokens rotate,
    # so a copy shared by host and container dies as soon as one of them
    # refreshes — and a container refresh logs the host out.
    if [ ! -f "$CONTAINER_DIR/.credentials.json" ]; then
      echo "No container credentials yet (OAuth mode)."
      echo "Run 'claude login' once inside the container to authenticate."
    fi
    # Copy settings.json if it exists, but strip the entire env block
    # and apiKeyHelper — the env block contains proxy config that conflicts
    # with OAuth. Any env vars needed in oauth mode go in .env.local.
    HOST_SETTINGS="$HOST_DIR/settings.json"
    if [ -f "$HOST_SETTINGS" ]; then
      echo "Copying host settings.json (stripping env block and apiKeyHelper)"
      if command -v jq &>/dev/null; then
        jq 'del(.apiKeyHelper, .env)' "$HOST_SETTINGS" > "$CONTAINER_DIR/settings.json"
      else
        echo "WARNING: jq not available, copying settings.json as-is"
        echo "Proxy env vars may override OAuth credentials."
        cp "$HOST_SETTINGS" "$CONTAINER_DIR/settings.json"
      fi
    else
      echo '{}' > "$CONTAINER_DIR/settings.json"
    fi
    ;;
  *)
    echo "ERROR: Unknown CLAUDE_AUTH value: $CLAUDE_AUTH"
    echo "Valid values: proxy, oauth"
    exit 1
    ;;
esac

HOST_CONFIG="/home/vscode/.claude-host.json"
if [ -f "$HOST_CONFIG" ]; then
  echo "Copying host .claude.json"
  cp "$HOST_CONFIG" "/home/vscode/.claude.json"
else
  echo "WARNING: No .claude.json found at $HOST_CONFIG"
fi

echo "Written container settings to $CONTAINER_DIR"
echo "$SEP"

echo "$SEP"
echo "Initializing Git Identity"
echo "$SEP"

git config --global user.name "ylink"
git config --global user.email "lfs@live.com"

echo "Git identity set: ylink <lfs@live.com>"
echo "$SEP"

# Without this step the first session after a start finds the update
# itself, installs it in the background and must be restarted to run it.
# The timeout bounds the start (VS Code waits for postStartCommand); a
# failure only warns.
echo "$SEP"
echo "Updating Claude Code"
echo "$SEP"
if ! timeout 120 "$CLAUDE" update </dev/null; then
  echo "WARNING: claude update failed or timed out, keeping the installed release"
fi
echo "$SEP"

# Install the official plugins the project's settings.json enables (e.g. the
# language-server plugins /project-init writes). Install state lives in the
# ~/.claude volume, which starts empty, so without this step Claude reports
# them as "enabled but not installed". Only @claude-plugins-official entries:
# whoever can write settings.json decides what this unattended step installs.
# Every failure warns and lets the start continue.
setup_plugins() {
  [ -f "$PROJECT_SETTINGS" ] || return 0

  local plugins
  if ! plugins="$(jq -r --arg m "@$OFFICIAL_MARKETPLACE" \
    '.enabledPlugins // {} | to_entries[]
     | select(.value == true and (.key | endswith($m))) | .key' \
    "$PROJECT_SETTINGS")"; then
    echo "WARNING: could not parse $PROJECT_SETTINGS, skipping plugin install"
    return 0
  fi
  [ -n "$plugins" ] || return 0

  echo "$SEP"
  echo "Installing Claude plugins"
  echo "$SEP"

  # GIT_TERMINAL_PROMPT=0 makes a credential prompt fail fast instead of
  # blocking the start.
  if ! "$CLAUDE" plugin marketplace list --json 2>/dev/null |
    jq -e --arg n "$OFFICIAL_MARKETPLACE" 'any(.[]; .name == $n)' >/dev/null; then
    if ! GIT_TERMINAL_PROMPT=0 "$CLAUDE" plugin marketplace add "$OFFICIAL_MARKETPLACE_URL"; then
      echo "WARNING: could not add marketplace $OFFICIAL_MARKETPLACE, skipping plugin install"
      echo "$SEP"
      return 0
    fi
  fi

  local installed plugin
  local wanted=() failed=()
  mapfile -t wanted <<<"$plugins"
  installed="$("$CLAUDE" plugin list --json 2>/dev/null | jq -r '.[].id')" || installed=""
  for plugin in "${wanted[@]}"; do
    if grep -Fxq "$plugin" <<<"$installed"; then
      echo "$plugin already installed, skipping."
    elif "$CLAUDE" plugin install "$plugin"; then
      echo "Installed $plugin"
    else
      echo "WARNING: failed to install $plugin"
      failed+=("$plugin")
    fi
  done

  if [ "${#failed[@]}" -gt 0 ]; then
    echo "WARNING: ${#failed[@]} plugin(s) not installed: ${failed[*]}"
  fi
  echo "$SEP"
}

setup_plugins
