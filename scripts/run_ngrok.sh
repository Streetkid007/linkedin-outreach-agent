#!/usr/bin/env bash
# Wrapper for ngrok, intended to be run as a macOS launchd service
# (com.clover.ngrok.plist). Sources config/.env to get WEBHOOK_BASE_URL,
# then starts ngrok pointing at the local webhook receiver port.
set -euo pipefail
cd "$(dirname "$0")/.."

set -a
source config/.env
set +a

WEBHOOK_PORT="${WEBHOOK_PORT:-8000}"

exec /opt/homebrew/bin/ngrok http "${WEBHOOK_PORT}" --url "${WEBHOOK_BASE_URL}"
