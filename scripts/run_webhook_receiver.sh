#!/usr/bin/env bash
# Wrapper for scripts/webhook_receiver.py, intended to be run as a macOS
# launchd service (com.clover.webhook-receiver.plist). Sources config/.env
# and activates the venv so the receiver has everything it needs.
set -euo pipefail
cd "$(dirname "$0")/.."

source .venv/bin/activate

set -a
source config/.env
set +a

mkdir -p logs

exec .venv/bin/python3 scripts/webhook_receiver.py
