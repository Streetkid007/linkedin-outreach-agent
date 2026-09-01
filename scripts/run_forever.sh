#!/usr/bin/env bash
# Continuous local runner. Wakes up at each of DAILY_RUN_TIMES (config/
# settings.py, default 10:00/13:00/18:00 local time), runs one poll cycle
# via your local Claude Code CLI in non-interactive mode, and logs the
# result. Intended to be started either directly in a terminal
# (foreground, stops when the terminal closes) or as a macOS launchd
# service (background, survives terminal/logout, see
# docs/RUNNING_LOCALLY.md).
#
# Deliberately does not run a cycle immediately on start: it always waits
# for the next scheduled time, so loading this as a launchd service or
# restarting it mid-afternoon does not sneak in a bonus cycle outside the
# three times a day it is meant to run. To test without waiting, run the
# claude command below by hand once (see docs/RUNNING_LOCALLY.md).
#
# Why headless Claude Code and not a plain Python script calling the
# Anthropic API directly: your local Claude Code session already has the
# Affinity MCP connector authenticated, using the exact field ids this
# project's config/fields.py was built against. A standalone script would
# need its own Affinity REST integration and a separate API key, and there
# is no confirmation yet that the field ids in config/fields.py (pulled
# via the MCP tools) are valid outside of MCP calls. This keeps one
# integration point instead of two. Unipile, which has no MCP connector,
# is still called through scripts/unipile_cli.py, a plain deterministic
# script, not through the model directly. See prompts/orchestrator.md for
# the full division of labor.

set -euo pipefail
cd "$(dirname "$0")/.."

# Activate the project's virtual environment so python3 below resolves to
# the one that has requests and flask installed.
# shellcheck disable=SC1091
source .venv/bin/activate

set -a
# shellcheck disable=SC1091
source config/.env
set +a

# Read into an array without mapfile/readarray: launchd (see the .plist)
# invokes this via /bin/bash directly, which on macOS is the ancient
# bash 3.2 that ships with the OS for licensing reasons, not whatever
# `bash` resolves to on your interactive PATH. mapfile is bash 4+ only.
DAILY_RUN_TIMES=()
while IFS= read -r _run_time; do
  DAILY_RUN_TIMES+=("${_run_time}")
done < <(python3 -c 'from config.settings import DAILY_RUN_TIMES as t; print("\n".join(t))')
WEBHOOK_PORT="${WEBHOOK_PORT:-8000}"

mkdir -p logs

echo "$(date -u +%FT%TZ) starting continuous runner, scheduled for ${DAILY_RUN_TIMES[*]} local time daily" | tee -a logs/run.log

# Epoch seconds of the next occurrence (today or tomorrow) of the earliest
# time in DAILY_RUN_TIMES that is still in the future. Uses BSD date (-j,
# -v+1d), this project's target platform is macOS.
next_run_epoch() {
  local now_epoch best candidate
  now_epoch="$(date +%s)"
  best=""
  for t in "${DAILY_RUN_TIMES[@]}"; do
    candidate="$(date -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) ${t}:00" +%s)"
    if [ "$candidate" -le "$now_epoch" ]; then
      candidate="$(date -j -v+1d -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) ${t}:00" +%s)"
    fi
    if [ -z "$best" ] || [ "$candidate" -lt "$best" ]; then
      best="$candidate"
    fi
  done
  echo "$best"
}

# This loop only runs the thesis check / connect / message / approval /
# follow up / reply logic. It depends on scripts/webhook_receiver.py and
# ngrok already running in their own terminal tabs (see
# docs/GETTING_STARTED_TERMINAL.md); it does not start them itself, on
# purpose, so a crash in one is visible in its own tab instead of hidden
# inside this loop's log. This just checks and warns, once per cycle,
# rather than assuming.
check_webhook_receiver() {
  if ! curl -sf "http://localhost:${WEBHOOK_PORT}/healthz" > /dev/null 2>&1; then
    echo "$(date -u +%FT%TZ) WARNING: scripts/webhook_receiver.py does not appear to be running on port ${WEBHOOK_PORT}. Accepted-connection and reply detection will silently miss events until it is started (see docs/GETTING_STARTED_TERMINAL.md, Step 6)." | tee -a logs/run.log
  fi
}

while true; do
  target_epoch="$(next_run_epoch)"
  sleep_secs=$(( target_epoch - $(date +%s) ))
  echo "$(date -u +%FT%TZ) sleeping ${sleep_secs}s until next scheduled run at $(date -r "${target_epoch}" '+%Y-%m-%d %H:%M %Z')" | tee -a logs/run.log
  sleep "${sleep_secs}"

  check_webhook_receiver
  echo "$(date -u +%FT%TZ) poll cycle starting" >> logs/run.log
  # --output-format text keeps the log readable; switch to --output-format
  # json if you want to parse cycle results programmatically later.
  # No --dangerously-skip-permissions here: --allowedTools below
  # pre-approves exactly the Affinity MCP tools and the one Bash command
  # this project needs, so it runs non-interactively without granting
  # blanket permissions. Widen this list if prompts/orchestrator.md ever
  # needs another Affinity MCP tool.
  claude -p "$(cat prompts/orchestrator.md)" \
    --allowedTools "mcp__Affinity__search_list_entries,mcp__Affinity__get_single_list_entry,mcp__Affinity__upsert_list_entry_field_values,mcp__Affinity__create_note,mcp__Affinity__get_notes_for_entity,mcp__Affinity__get_list_fields,mcp__Affinity__get_list_field_dropdown_options,mcp__Google_Drive__read_file_content,mcp__claude_ai_Affinity__search_list_entries,mcp__claude_ai_Affinity__get_single_list_entry,mcp__claude_ai_Affinity__upsert_list_entry_field_values,mcp__claude_ai_Affinity__create_note,mcp__claude_ai_Affinity__get_notes_for_entity,mcp__claude_ai_Affinity__get_list_fields,mcp__claude_ai_Affinity__get_list_field_dropdown_options,mcp__claude_ai_Google_Drive__read_file_content,WebSearch,Read,Write,Bash(python scripts/unipile_cli.py:*)" \
    >> logs/run.log 2>> logs/run_errors.log \
    || echo "$(date -u +%FT%TZ) poll cycle FAILED, see logs/run_errors.log" >> logs/run.log

  echo "$(date -u +%FT%TZ) poll cycle finished" >> logs/run.log
done
