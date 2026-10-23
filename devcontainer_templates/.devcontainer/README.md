# Devcontainer Template

Devcontainer template for sandboxed Claude Code agent execution.

## Setup

1. Copy the contents of this directory to your project's `.devcontainer/` folder
2. Open your project in VS Code and use "Reopen in Container"

## Authentication Modes

The `CLAUDE_AUTH` environment variable controls how Claude Code authenticates.
On first use, `initializeCommand` runs `.devcontainer/init-env` on the host to
create `.devcontainer/.env.local` (gitignored) with the default
`CLAUDE_AUTH=oauth` before Docker needs it. The command is cross-platform:
Unix runs the extensionless `init-env` script via its shebang, Windows resolves
`init-env.cmd` via PATHEXT.

| Mode | `CLAUDE_AUTH` | What gets copied | Use case |
|------|---------------|------------------|----------|
| OAuth (default) | `oauth` | `settings.json` (env block and apiKeyHelper stripped); credentials from a one-time `claude login` in the container | Private Anthropic account |
| Proxy | `proxy` | `settings.json` (with env vars) | Work account via API proxy (e.g. Portkey) |

### OAuth mode (default)

Run `claude login` once inside the container; the session stays in the
`claude-code-config-{project-name}` volume. The host's `.credentials.json`
is never copied: OAuth refresh tokens rotate, so a copy shared by host and
container breaks as soon as either side refreshes it. The script strips the
entire `env` block and `apiKeyHelper` from `settings.json` so OAuth
credentials are used and no proxy config leaks in.
Any env vars needed in oauth mode (e.g.
`CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS`) should be added to
`.devcontainer/.env.local`.

### Proxy mode

No extra setup needed. Your `~/.claude/settings.json` is copied as-is into
the container, including any `env` block with proxy configuration.

### Switching modes

Edit `CLAUDE_AUTH` in `.devcontainer/.env.local` (gitignored):

```bash
# .devcontainer/.env.local
CLAUDE_AUTH=proxy
```

After switching, delete the Docker volume and rebuild the container (see
Troubleshooting).

## Troubleshooting

### Auth errors or "Rate limit reached" after switching modes

The Docker volume `claude-code-config-{project-name}` persists between
container restarts. If you switch authentication modes or change credentials,
stale state in the volume can cause unexpected errors (e.g. "Rate limit
reached" that isn't a real rate limit).

Fix: delete the volume and rebuild the container.

```bash
docker volume ls | grep claude-code-config
docker volume rm claude-code-config-<project-name>
```

### Claude Code ignores settings.json on first run

On fresh volumes, Claude Code >=2.0.65 may ignore `settings.json` and force
the login flow ([#13827](https://github.com/anthropics/claude-code/issues/13827)).
Deleting the volume and setting `CLAUDE_AUTH` before starting the container
resolves this.

## How It Works

- **Project-scoped volume**: Claude config is stored in a Docker volume named
  `claude-code-config-{project-name}`. All devcontainers for the same project
  share history. Different projects have separate histories.

- **Host config as template**: Your `~/.claude/` directory and `~/.claude.json`
  are mounted read-only. On container startup, the post-start script copies
  the appropriate files into the container volume based on `CLAUDE_AUTH`, and
  copies `~/.claude.json` into the container home directory.

- **Global instructions and skills, live**: unlike the rest of `~/.claude/`,
  `CLAUDE.md`, `~/.claude/anti-patterns/`, and `~/.agents/skills` are
  bind-mounted read-write directly into the container instead of copied —
  edits on either side are immediately visible to the other.
  `~/.claude/anti-patterns/` is mounted directly because it's a real
  directory the global `CLAUDE.md` references by path, not a symlink into
  `~/.agents` like `skills/` is. `post-create.sh` recreates the
  `~/.claude/skills -> ~/.agents/skills` symlink inside the container to
  match the host layout, since the container only has `~/.claude` mounted,
  not `~/.agents`. Requires `~/.claude/CLAUDE.md`, `~/.claude/anti-patterns/`,
  and `~/.agents/skills` to already exist on the host — Docker creates an
  empty placeholder at a missing bind source instead of failing, which
  would mount a blank `CLAUDE.md` or empty directories.

- **Go modules, reused from the host**: `~/go` (the default GOPATH,
  including the module cache and installed binaries) is bind-mounted
  read-write so `go mod download` and `go install` reuse whatever the host
  has already fetched or built, and share anything new back. Requires `~/go`
  to already exist on the host — same reasoning as above. Git remotes are
  accessed over HTTPS; no SSH keys are mounted.

- **Claude Code kept current**: `post-start.sh` runs `claude update` on every
  start (two-minute timeout, warn-only) and installs the
  `@claude-plugins-official` plugins the project's `.claude/settings.json`
  enables, both through `claude-proxy.sh`. `post-create.sh` installs the
  TypeScript and Python language servers those plugins use.

## Network Access

Three independent proxy scopes, all pointing at `host.docker.internal:10808`
(matching `~/global-scripts/claude-proxy.sh` on the host) — one build-time,
one runtime, one VS Code-only. None leaks into the others, and none affects
your database/Redis clients.

- **Build time** (`docker build` / container rebuild): `devcontainer.json`'s
  `build.args` sets `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY` using BuildKit's
  predefined proxy args. Every `RUN` step (`apt-get`, the `curl` installs
  for `claude` and `starship`) picks them up automatically — no `ARG`/`ENV`
  needed in the Dockerfile — and they do not persist into the built image's
  runtime environment.
- **Runtime**: `claude` is aliased to `claude-proxy.sh`, which scopes the
  proxy to the Claude Code process only. Every other command run in the
  container — database clients, `redis-cli`, `curl` against internal
  services — gets no proxy env vars and uses the container's default
  network path, which rides whatever the host's system network settings
  provide (e.g. a company VPN already active on the host).
- **VS Code extension host**: `customizations.vscode.settings` sets
  `http.proxy` in the Remote settings scope, which applies only to the
  extension host running inside this container and is never synced back
  to the host's VS Code. Without this, the extension host falls back to
  your host's synced `http.proxy` (typically `127.0.0.1:10808`, correct
  only on the host's own loopback), and extension downloads that need a
  proxy (e.g. `codelldb`) fail with a socket connection error since
  `127.0.0.1` inside the container means "this container."

If your proxy client listens on a different port, edit
`devcontainer.json`'s `build.args` and `customizations.vscode.settings`,
plus `claude-proxy.sh`.

### Reaching Local Middleware

`runArgs` joins the container to an external Docker network named
`dc-local`. Attach the middleware compose stacks in `~/composes` (MySQL,
Redis, Nacos, Postgres, Kafka) to the same network and address them by
their `container_name` (e.g. `mysql_server:3306`, `redis-server:6379`)
instead of `127.0.0.1` or `host.docker.internal` — the latter route
through Docker Desktop's host-gateway, which has been observed to be
flaky. Create the network once, before starting any of the compose
stacks or this container:

```sh
docker network create dc-local
```

## Mounts

| Source | Target | Purpose |
|--------|--------|---------|
| `claude-code-config-${project}` (volume) | `/home/vscode/.claude` | Project-scoped Claude config and history |
| `~/.claude/` (bind, ro) | `/home/vscode/.claude-host/` | Host config template directory |
| `~/.claude.json` (bind, ro) | `/home/vscode/.claude-host.json` | Host Claude config file (copied into container on startup) |
| `~/.claude/CLAUDE.md` (bind, rw) | `/home/vscode/.claude/CLAUDE.md` | Global instructions, live and shared with the host |
| `~/.claude/anti-patterns/` (bind, rw) | `/home/vscode/.claude/anti-patterns/` | Anti-pattern catalog referenced by `CLAUDE.md`, live and shared with the host |
| `~/.agents/skills` (bind, rw) | `/home/vscode/.agents/skills` | Skill set, live and shared with the host |
| `~/go` (bind, rw) | `/home/vscode/go` | Shared GOPATH (module cache, installed binaries) |
| `~/composes` (bind, ro) | `/home/vscode/composes` | Host compose definitions, read-only |
| `claude-code-shellhistory-${id}` (volume) | `/home/vscode/.local/share/fish` | Fish shell history persistence |
