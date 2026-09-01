#!/usr/bin/env python3
"""
Local webhook receiver for Unipile events. Runs continuously in its own
terminal tab, exposed to the internet via ngrok (see docs/RUNNING_LOCALLY.md,
"Webhook setup"). Unipile POSTs here the instant it learns a connection
request was accepted, or a new LinkedIn message arrives.

Deliberately the dumbest possible piece of this project: it holds no
Affinity credentials, no Anthropic access, and makes no judgment calls. It
checks one shared secret header, then appends the raw event to a log file
and returns 200. That's it. scripts/unipile_cli.py's check-accepted and
check-replies commands are what actually turn these into something the
orchestrator acts on, on its own schedule. Keeping this receiver this
simple means a bug here can, at worst, fail to record an event or record a
duplicate, never send anything or write anything to Affinity by itself.

Requires: pip3 install flask (see docs/RUNNING_LOCALLY.md).
"""

import datetime
import json
import os
import sys

from flask import Flask, jsonify, request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import (
    WEBHOOK_PORT,
    WEBHOOK_SHARED_SECRET,
    ACCEPTED_CONNECTIONS_LOG,
    INBOUND_MESSAGES_LOG,
)

app = Flask(__name__)


def _secret_ok():
    return bool(WEBHOOK_SHARED_SECRET) and (
        request.headers.get("Unipile-Auth") == WEBHOOK_SHARED_SECRET
    )


def _append(path, record):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    record = dict(record)
    record["received_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")


@app.route("/webhooks/new-relation", methods=["POST"])
def new_relation():
    if not _secret_ok():
        return jsonify({"error": "bad or missing Unipile-Auth header"}), 401
    payload = request.get_json(force=True, silent=True) or {}
    _append(ACCEPTED_CONNECTIONS_LOG, payload)
    print(f"[new-relation] recorded: {payload.get('user_full_name')} "
          f"({payload.get('user_provider_id')})")
    return jsonify({"status": "recorded"}), 200


@app.route("/webhooks/new-message", methods=["POST"])
def new_message():
    if not _secret_ok():
        return jsonify({"error": "bad or missing Unipile-Auth header"}), 401
    payload = request.get_json(force=True, silent=True) or {}
    _append(INBOUND_MESSAGES_LOG, payload)
    sender = payload.get("sender", {}) or {}
    print(f"[new-message] recorded: from {sender.get('attendee_name')}")
    return jsonify({"status": "recorded"}), 200


@app.route("/healthz", methods=["GET"])
def healthz():
    """
    Not a Unipile endpoint. Hit this yourself, locally or through your
    ngrok URL, to confirm the receiver (and the tunnel, if you go through
    ngrok) is actually up: `curl http://localhost:8000/healthz`.
    """
    return jsonify({"status": "ok", "secret_configured": bool(WEBHOOK_SHARED_SECRET)}), 200


if __name__ == "__main__":
    if not WEBHOOK_SHARED_SECRET:
        print("WARNING: WEBHOOK_SHARED_SECRET is not set in config/.env. "
              "Every incoming request will be rejected with 401 until you "
              "set one. See docs/RUNNING_LOCALLY.md, 'Webhook setup'.")
    print(f"Listening on http://0.0.0.0:{WEBHOOK_PORT} "
          f"(health check at /healthz)")
    app.run(host="0.0.0.0", port=WEBHOOK_PORT)
