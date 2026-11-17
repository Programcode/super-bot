#!/usr/bin/env bash
# ask-pip.sh: send a message from Claude Code to Pip (Adam's Grok Bot build partner).
#
# Usage:
#   scripts/ask-pip.sh <kind> "<message>" [thread]
#     kind:    question | decision-needed | status | done | blocker
#     message: what you need Pip to know or answer (no secrets, ever)
#     thread:  T3 thread id or title (defaults to $T3_THREAD_ID, then $PIP_THREAD, then the git branch)
#
# Config: PIP_WEBHOOK_URL, PIP_WEBHOOK_KEY and PIP_WEBHOOK_AUTH_HEADER come from the
# environment or from .env.pip in the repo root (gitignored; see .env.pip.example).
# Adam copies the values from the Grok Bot routine panel "Super bot: messages from Claude Code".
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$repo_root/.env.pip" ]]; then
  set -a; source "$repo_root/.env.pip"; set +a
fi

kind="${1:-}"; message="${2:-}"
thread="${3:-${T3_THREAD_ID:-${PIP_THREAD:-$(git -C "$repo_root" branch --show-current 2>/dev/null || echo unknown)}}}"

case "$kind" in
  question|decision-needed|status|done|blocker) ;;
  *) echo "usage: $0 <question|decision-needed|status|done|blocker> \"message\" [thread]" >&2; exit 2 ;;
esac
[[ -n "$message" ]] || { echo "error: empty message" >&2; exit 2; }

: "${PIP_WEBHOOK_URL:?PIP_WEBHOOK_URL is not set (see .env.pip.example)}"
: "${PIP_WEBHOOK_KEY:?PIP_WEBHOOK_KEY is not set (see .env.pip.example)}"

# >>> AUTH HEADER <<<
# Copy the EXACT header name and value format from the Grok Bot routine panel.
# Write {KEY} where the sender key goes, e.g. "Some-Header: {KEY}" or "Authorization: Bearer {KEY}".
# Do not guess: if this is empty the script refuses to send.
PIP_WEBHOOK_AUTH_HEADER="${PIP_WEBHOOK_AUTH_HEADER:-}"
[[ -n "$PIP_WEBHOOK_AUTH_HEADER" ]] || { echo "error: PIP_WEBHOOK_AUTH_HEADER is not set; copy it from the routine panel" >&2; exit 2; }
auth_header="${PIP_WEBHOOK_AUTH_HEADER//\{KEY\}/$PIP_WEBHOOK_KEY}"

payload="$(python3 -c 'import json,sys; print(json.dumps({"thread":sys.argv[1],"kind":sys.argv[2],"message":sys.argv[3]}))' "$thread" "$kind" "$message")"

# The header is passed via a config on stdin so the key never shows up in `ps`.
curl --fail-with-body -sS -X POST "$PIP_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  --config - --data "$payload" <<<"header = \"${auth_header//\"/\\\"}\""
echo
