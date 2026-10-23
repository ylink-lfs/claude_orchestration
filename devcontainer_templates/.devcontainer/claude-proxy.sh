#!/usr/bin/env bash
# Scopes the local SOCKS/HTTP proxy to the `claude` process only.
#
# Mirrors ~/global-scripts/claude-proxy.sh, adapted for use inside the
# devcontainer: the proxy client (v2ray/clash) runs on the host, so
# 127.0.0.1 from inside the container would point at the container
# itself. host.docker.internal resolves to the host on Docker Desktop.
#
# Only this process tree gets the proxy env vars — other commands run
# in the container (mysql, redis-cli, etc.) are unaffected and reach
# internal hosts through the container's default network path, which
# rides whatever the host's system network settings provide (e.g. a
# company VPN already active on the host).

set -euo pipefail

export HTTP_PROXY="http://host.docker.internal:10808"
export HTTPS_PROXY="http://host.docker.internal:10808"
export ALL_PROXY="socks5://host.docker.internal:10808"

export http_proxy="$HTTP_PROXY"
export https_proxy="$HTTPS_PROXY"
export all_proxy="$ALL_PROXY"

# Middleware containers reachable on the dc-local network (see
# devcontainer.json's --network=dc-local) must bypass the proxy too —
# otherwise traffic to them gets tunneled through the proxy client instead
# of going direct over dc-local.
export NO_PROXY="localhost,127.0.0.1,::1,mysql_server,redis-server,nacos,postgres_server,kafka,kafka-ui"
export no_proxy="$NO_PROXY"

exec claude "$@"
