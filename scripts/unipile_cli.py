#!/usr/bin/env python3
"""
Deterministic Unipile wrapper. This is the one place in the whole project
that is allowed to actually send a LinkedIn invite or message, the one
place the daily send cap is enforced, and now also the one place that
turns raw webhook events (recorded by scripts/webhook_receiver.py) into
tidy "here is what changed" JSON the orchestrator can act on, so the model
never has to reason about jsonl files, cursors, or matching LinkedIn's own
identifiers back to your Affinity records.

Endpoints below were corrected on 2026-08-17 against developer.unipile.com's
actual reference pages (not just the narrative docs pages), after the
selftest-only verification in the first version of this file. Specifically:
- Sending a message uses POST /chats or POST /chats/{chat_id}/messages,
  not POST /chats with a provider_id, see cmd_message below.
- Invitations take no separate "no note" flag, omitting `message` from the
  body is the documented way to send a bare invite, see cmd_invite below.
Run "selftest" once before trusting this in the continuous loop regardless;
if anything below is still wrong, Unipile's error response will say so
directly, check https://developer.unipile.com/reference for the current
schema and fix the request here.

Usage:
  python scripts/unipile_cli.py selftest
  python scripts/unipile_cli.py resolve <linkedin_public_url> --account <unipile_account_id>
  python scripts/unipile_cli.py invite <provider_id> --account <unipile_account_id> --tag <affinity_entity_id> [--note "text"]
  python scripts/unipile_cli.py message <provider_id> "text" --account <unipile_account_id>
  python scripts/unipile_cli.py contact-for-entity <affinity_entity_id>
  python scripts/unipile_cli.py register-webhooks
  python scripts/unipile_cli.py check-accepted
  python scripts/unipile_cli.py check-replies
  python scripts/unipile_cli.py counts

  Note on message text: the `text` argument interprets literal backslash-n
  sequences (the two characters \\ and n) as real newlines before sending,
  so the orchestrator can pass "Hello\\nWorld" on the command line and the
  message will contain an actual line break. Actual newlines embedded in
  the shell argument also work.

One Unipile workspace (one DSN/API key) can have several LinkedIn accounts
connected to it — see config/settings.py's OWNERS. resolve/invite/message
all take an explicit --account, deliberately not something this script
decides on its own: the orchestrator resolves it fresh from Affinity's
Owners field every time (Juliette rarely changes it — mainly to add Hugo
as a second try when a founder has not accepted her invite — so trusting
it live, every stage, every cycle, costs nothing extra and needs no
account bookkeeping here). contact-for-entity exists only to support
that: given a company's Affinity entity_id, it reports which account(s)
have already sent this person an invite (from contacts.json, written by
`invite --tag`), so the orchestrator can tell a genuinely new connect
from a stalled-invite retry via a not-yet-tried account, and never send
the same person a duplicate invite from an account that already has one
pending.

Every subcommand prints a single JSON object to stdout and exits 0 on
success. On the daily cap being reached, or an error, it prints a JSON
object with an "error" key and exits 1 so the calling orchestrator can
tell "worked" from "did not" without parsing prose.
"""

import argparse
import datetime
import json
import os
import random
import sys
import time

import requests

# Auto-load config/.env, always overwriting any stale system-level env
# vars (mirrors what run_forever.sh does with `set -a; source config/.env;
# set +a` — unconditional, not "only if absent", so the new Unipile
# workspace credentials in config/.env always win over any old ones that
# may have been exported into the shell environment from a previous setup).
_env_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _env_f:
        for _env_line in _env_f:
            _env_line = _env_line.strip()
            if not _env_line or _env_line.startswith("#") or "=" not in _env_line:
                continue
            _env_key, _, _env_val = _env_line.partition("=")
            _env_key = _env_key.strip()
            _env_val = _env_val.strip()
            if _env_key:
                os.environ[_env_key] = _env_val

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import (
    MAX_INVITES_PER_DAY,
    MAX_MESSAGES_PER_DAY,
    MAX_NOTED_INVITES_PER_MONTH,
    INVITE_NOTE_MAX_CHARS,
    SEND_COUNTS_PATH,
    SEND_DELAY_MIN_SECONDS,
    SEND_DELAY_MAX_SECONDS,
    WEBHOOK_BASE_URL,
    WEBHOOK_SHARED_SECRET,
    ACCEPTED_CONNECTIONS_LOG,
    INBOUND_MESSAGES_LOG,
    WEBHOOK_CURSORS_PATH,
    CONTACTS_PATH,
    CHATS_PATH,
)

DSN = os.environ.get("UNIPILE_DSN", "").rstrip("/")
API_KEY = os.environ.get("UNIPILE_API_KEY", "")

HEADERS = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}


# ---------------------------------------------------------------- helpers

def _fail(message, **extra):
    print(json.dumps({"error": message, **extra}))
    sys.exit(1)


def _ok(**data):
    print(json.dumps(data))
    sys.exit(0)


def _require_env():
    # Workspace-level credentials only. Which LinkedIn account_id to use is
    # an explicit --account on every call (resolve/invite/message), not a
    # single global, since one Unipile workspace now has two LinkedIn
    # accounts connected to it and the caller decides per call which one.
    missing = [
        name
        for name, val in [("UNIPILE_DSN", DSN), ("UNIPILE_API_KEY", API_KEY)]
        if not val
    ]
    if missing:
        _fail(f"Missing env vars: {', '.join(missing)}. Check config/.env "
              f"is loaded before running this script.")


def _read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _space_out_send():
    """
    Space calls out randomly rather than at fixed intervals, per the
    general safety guidance seen across every source checked on this.
    Called right before every actual invite or message network call,
    never before a read, and lives here rather than in the orchestrator
    prompt so it cannot be skipped by a prompt that forgets to ask for it.
    """
    time.sleep(random.uniform(SEND_DELAY_MIN_SECONDS, SEND_DELAY_MAX_SECONDS))


def _today_key():
    return datetime.date.today().isoformat()


def _month_key():
    return datetime.date.today().strftime("%Y-%m")


def _reserve_note_slot():
    """
    Inert under the current setup (Stage 2 no longer asks for a note at
    all, per your 2026-08-17 decision), kept as a safety net: if a note
    is ever passed anyway, this still enforces MAX_NOTED_INVITES_PER_MONTH
    rather than attaching one past an unverified failure mode.
    """
    counts = _read_json(SEND_COUNTS_PATH, {})
    month = _month_key()
    monthly = counts.get("monthly_notes", {})
    used = monthly.get(month, 0)
    if used >= MAX_NOTED_INVITES_PER_MONTH:
        return False
    monthly[month] = used + 1
    counts["monthly_notes"] = monthly
    _write_json(SEND_COUNTS_PATH, counts)
    return True


def _check_and_increment(kind, cap, account_id):
    """
    kind is 'invites' or 'messages'. The cap is per Unipile account_id, not
    combined, since LinkedIn's own limits are per profile: two connected
    accounts each get their own MAX_INVITES_PER_DAY / MAX_MESSAGES_PER_DAY
    ceiling, which is the actual point of having two accounts. Exits via
    _fail if today's count for this account is already at cap, otherwise
    increments and persists BEFORE the network call, so a crash mid-send
    never lets a retry double count past the cap.
    """
    counts = _read_json(SEND_COUNTS_PATH, {})
    today = _today_key()
    day_counts = counts.get(today, {})
    account_counts = day_counts.get(account_id, {"invites": 0, "messages": 0})
    if account_counts.get(kind, 0) >= cap:
        _fail(
            f"DAILY CAP REACHED for {kind} on account {account_id}: "
            f"{account_counts.get(kind, 0)}/{cap} already sent today "
            f"({today}). Stop for today on this account, do not retry with "
            f"a different phrasing or provider_id, the cap is per day per "
            f"account, across all companies routed to it. Resume tomorrow.",
            kind=kind, account_id=account_id,
            count_today=account_counts.get(kind, 0), cap=cap,
        )
    account_counts[kind] = account_counts.get(kind, 0) + 1
    day_counts[account_id] = account_counts
    counts[today] = day_counts
    _write_json(SEND_COUNTS_PATH, counts)
    return account_counts[kind]


def _load_jsonl(path):
    if not os.path.exists(path):
        return []
    lines = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)
    return lines


def _new_jsonl_records(path, cursor_key):
    """
    Returns (records, new_cursor) for lines in path beyond what was
    already processed last time, tracked in WEBHOOK_CURSORS_PATH by line
    count, not by deleting or rewriting the log itself. webhook_receiver.py
    only ever appends, so a simple line count cursor is enough and never
    races with a concurrent append the way rewriting the file would.
    """
    lines = _load_jsonl(path)
    cursors = _read_json(WEBHOOK_CURSORS_PATH, {})
    already = cursors.get(cursor_key, 0)
    new_lines = lines[already:]
    records = []
    for line in new_lines:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # a torn write from a crash mid-append; skip, don't crash
    return records, len(lines)


def _advance_cursor(cursor_key, new_cursor):
    cursors = _read_json(WEBHOOK_CURSORS_PATH, {})
    cursors[cursor_key] = new_cursor
    _write_json(WEBHOOK_CURSORS_PATH, cursors)


# --------------------------------------------------------------- commands

def cmd_selftest(_args):
    _require_env()
    resp = requests.get(f"{DSN}/api/v1/accounts", headers=HEADERS, timeout=15)
    resp.raise_for_status()
    _ok(status="reachable", accounts=resp.json())


def cmd_resolve(args):
    _require_env()
    resp = requests.get(
        f"{DSN}/api/v1/users/{args.linkedin_url}",
        headers=HEADERS, params={"account_id": args.account}, timeout=15,
    )
    if resp.status_code != 200:
        _fail(f"Unipile returned {resp.status_code} resolving profile.",
              body=resp.text)
    _ok(**resp.json())


def cmd_invite(args):
    _require_env()
    note = args.note or ""
    if len(note) > INVITE_NOTE_MAX_CHARS:
        _fail(f"Invite note is {len(note)} characters, over the configured "
              f"{INVITE_NOTE_MAX_CHARS} character limit "
              f"(config/settings.py INVITE_NOTE_MAX_CHARS). Shorten before "
              f"sending, do not truncate it yourself and resend blind.")

    note_dropped_reason = None
    if note:
        if not _reserve_note_slot():
            note_dropped_reason = (
                f"MAX_NOTED_INVITES_PER_MONTH ({MAX_NOTED_INVITES_PER_MONTH}) "
                f"already used this month; sending this invite without a "
                f"note rather than risk an unverified failure mode."
            )
            note = ""

    count_after = _check_and_increment("invites", MAX_INVITES_PER_DAY, args.account)

    # Record provider_id -> Affinity entity_id BEFORE sending, not after:
    # if the network call succeeds but this process dies before writing
    # the tag, check-accepted would later see an accepted connection it
    # cannot match to any company. Recording first costs nothing if the
    # send then fails (an unused tag is harmless), the reverse ordering
    # can lose a real event.
    #
    # invited_accounts is a dict, not a single value, because the same
    # provider_id can legitimately be invited twice, from two different
    # accounts: Juliette invites, the founder does not accept, Juliette
    # adds Hugo as a second Affinity Owner to try him instead — the
    # orchestrator's Stage 2 retry then sends a second, separate invite
    # from Hugo's account for the same provider_id. Merging in (not
    # overwriting) preserves that history so contact-for-entity can tell
    # which accounts have already been tried.
    if args.tag:
        contacts = _read_json(CONTACTS_PATH, {})
        contact = contacts.get(args.provider_id, {})
        contact["entity_id"] = args.tag
        invited_accounts = contact.get("invited_accounts", {})
        invited_accounts[args.account] = datetime.datetime.utcnow().isoformat() + "Z"
        contact["invited_accounts"] = invited_accounts
        contacts[args.provider_id] = contact
        _write_json(CONTACTS_PATH, contacts)

    _space_out_send()
    payload = {"provider_id": args.provider_id, "account_id": args.account}
    if note:
        payload["message"] = note
    resp = requests.post(
        f"{DSN}/api/v1/users/invite", headers=HEADERS, json=payload, timeout=15,
    )
    if resp.status_code not in (200, 201):
        _fail(f"Unipile returned {resp.status_code} sending invite.",
              body=resp.text, count_today=count_after)
    result = dict(status="invite_sent", count_today=count_after,
                  cap=MAX_INVITES_PER_DAY, response=resp.json())
    if note_dropped_reason:
        result["note_dropped"] = True
        result["note_dropped_reason"] = note_dropped_reason
    _ok(**result)


def cmd_message(args):
    """
    Sends a text message to an existing first degree connection.
    Corrected 2026-08-17 against Unipile's API reference: prefers an
    existing chat_id when this project has already messaged this
    provider_id before (POST /chats/{chat_id}/messages), otherwise starts
    a new chat (POST /chats with attendees_ids), which Unipile's own docs
    say only works for existing relations, exactly this project's case.

    --account is required and explicit, not looked up from contacts.json:
    the orchestrator resolves it fresh from Affinity's Owners field every
    time (Juliette's call — she rarely changes it, so re-checking is
    cheap and simpler than this script tracking which account "owns" a
    thread). If Owners is stale relative to which account actually holds
    the LinkedIn connection, Unipile will reject the send below with a
    4xx rather than silently misdirecting it.

    The text argument interprets literal backslash-n sequences as real
    newlines before sending, so the orchestrator can pass "Hello\\nWorld"
    on the command line and the message arrives with an actual line break.
    """
    _require_env()
    text = args.text.replace("\\n", "\n")
    count_after = _check_and_increment("messages", MAX_MESSAGES_PER_DAY, args.account)
    chats = _read_json(CHATS_PATH, {})
    chat_id = chats.get(args.provider_id)

    _space_out_send()
    if chat_id:
        resp = requests.post(
            f"{DSN}/api/v1/chats/{chat_id}/messages",
            headers=HEADERS, json={"text": text}, timeout=15,
        )
    else:
        payload = {
            "account_id": args.account,
            "attendees_ids": [args.provider_id],
            "text": text,
        }
        resp = requests.post(
            f"{DSN}/api/v1/chats", headers=HEADERS, json=payload, timeout=15,
        )

    if resp.status_code not in (200, 201):
        _fail(f"Unipile returned {resp.status_code} sending message. If "
              f"this is a 4xx about the recipient not being a connection, "
              f"either the connect step ran ahead of acceptance, or "
              f"Affinity's Owners field now points at an account that "
              f"never actually connected with this person — do not retry, "
              f"flag the company for Juliette to check the Owners field "
              f"and wait for the next accepted-connection event instead.",
              body=resp.text, count_today=count_after)

    data = resp.json() if resp.text else {}
    new_chat_id = data.get("chat_id") or data.get("id")
    if new_chat_id and not chat_id:
        chats[args.provider_id] = new_chat_id
        _write_json(CHATS_PATH, chats)

    _ok(status="message_sent", count_today=count_after,
        cap=MAX_MESSAGES_PER_DAY, response=data)


def cmd_contact_for_entity(args):
    """
    For a given Affinity entity_id, reports its provider_id and which
    Unipile account_id(s) have already sent that person an invite,
    scanning contacts.json for the entry tagged with this entity_id (the
    same record cmd_invite writes). Used by the orchestrator's Stage 2 to
    tell three cases apart: never invited at all (empty invited_accounts,
    or no contact yet — not an error, a brand new company legitimately
    has none), already invited from the account Owners currently resolves
    to (skip, already pending), or invited from a different account only
    (a stalled-invite retry: send a second invite from the new account
    too, do not touch the first one).
    """
    contacts = _read_json(CONTACTS_PATH, {})
    for provider_id, contact in contacts.items():
        if contact.get("entity_id") == args.entity_id:
            _ok(provider_id=provider_id,
                invited_accounts=list(contact.get("invited_accounts", {}).keys()))
    _ok(provider_id=None, invited_accounts=[])


def cmd_register_webhooks(_args):
    """
    One time setup: tells Unipile to POST to your public ngrok URL
    whenever a connection is accepted or a new message arrives. Requires
    WEBHOOK_BASE_URL in config/.env to already point at your running
    ngrok tunnel, see docs/RUNNING_LOCALLY.md, "Webhook setup".
    """
    _require_env()
    if not WEBHOOK_BASE_URL:
        _fail("WEBHOOK_BASE_URL is not set in config/.env yet. Start "
              "ngrok first, copy the https URL it prints, put it in "
              "config/.env, then run this again.")
    if not WEBHOOK_SHARED_SECRET:
        _fail("WEBHOOK_SHARED_SECRET is not set in config/.env. Generate "
              "a random string and set it there before registering, this "
              "is what stops random internet traffic hitting your ngrok "
              "URL from injecting fake events.")

    base = WEBHOOK_BASE_URL.rstrip("/")
    results = {}
    for source, event, path in [
        ("users", "new_relation", "/webhooks/new-relation"),
        ("messaging", "message_received", "/webhooks/new-message"),
    ]:
        payload = {
            "request_url": f"{base}{path}",
            "source": source,
            "events": [event],
            "format": "json",
            "headers": [{"key": "Unipile-Auth", "value": WEBHOOK_SHARED_SECRET}],
        }
        resp = requests.post(
            f"{DSN}/api/v1/webhooks", headers=HEADERS, json=payload, timeout=15,
        )
        results[event] = {
            "status_code": resp.status_code,
            "body": resp.json() if resp.text else None,
        }
        if resp.status_code not in (200, 201):
            _fail(f"Unipile returned {resp.status_code} registering the "
                  f"{event} webhook. Nothing else was changed; fix this "
                  f"before re-running, do not assume the other webhook "
                  f"registered successfully without checking.",
                  results=results)
    _ok(status="registered", results=results)


def cmd_check_accepted(_args):
    """
    Reads new lines webhook_receiver.py has appended to
    ACCEPTED_CONNECTIONS_LOG since the last check, matches each against
    CONTACTS_PATH (written by `invite --tag`) to find which Affinity
    company this is about, and returns only the new, matched events. Also
    advances the cursor so nothing is reported twice, and so a company
    with no invite on record (should not normally happen) is still
    reported, with entity_id null, rather than silently dropped.
    """
    records, new_cursor = _new_jsonl_records(ACCEPTED_CONNECTIONS_LOG, "accepted")
    contacts = _read_json(CONTACTS_PATH, {})
    events = []
    for r in records:
        provider_id = r.get("user_provider_id")
        contact = contacts.get(provider_id)
        events.append({
            "provider_id": provider_id,
            "entity_id": contact.get("entity_id") if contact else None,
            "user_full_name": r.get("user_full_name"),
            "accepted_signal_received_at": r.get("received_at"),
        })
    _advance_cursor("accepted", new_cursor)
    _ok(new_events=events, count=len(events))


def cmd_check_replies(_args):
    """
    Same pattern as check-accepted, for inbound messages. Also caches the
    chat_id from the reply into CHATS_PATH, since a reply proves a chat
    already exists even if this project had not sent the first message
    through cmd_message itself for some reason.
    """
    records, new_cursor = _new_jsonl_records(INBOUND_MESSAGES_LOG, "inbound")
    contacts = _read_json(CONTACTS_PATH, {})
    chats = _read_json(CHATS_PATH, {})
    events = []
    chats_changed = False
    for r in records:
        sender = r.get("sender", {}) or {}
        provider_id = sender.get("attendee_provider_id")
        contact = contacts.get(provider_id)
        chat_id = r.get("chat_id")
        if provider_id and chat_id and chats.get(provider_id) != chat_id:
            chats[provider_id] = chat_id
            chats_changed = True
        events.append({
            "provider_id": provider_id,
            "entity_id": contact.get("entity_id") if contact else None,
            "chat_id": chat_id,
            "text": r.get("message"),
            "reply_signal_received_at": r.get("received_at"),
        })
    if chats_changed:
        _write_json(CHATS_PATH, chats)
    _advance_cursor("inbound", new_cursor)
    _ok(new_events=events, count=len(events))


def cmd_counts(_args):
    counts = _read_json(SEND_COUNTS_PATH, {})
    today_counts = counts.get(_today_key(), {})
    notes_this_month = counts.get("monthly_notes", {}).get(_month_key(), 0)
    by_account = {}
    legacy_today = {}
    for key, value in today_counts.items():
        if isinstance(value, dict):
            by_account[key] = {
                "invites_sent": value.get("invites", 0),
                "invites_cap": MAX_INVITES_PER_DAY,
                "messages_sent": value.get("messages", 0),
                "messages_cap": MAX_MESSAGES_PER_DAY,
            }
        else:
            # Counters from before the 2026-08-24 dual-account cutover,
            # written under the old single-account schema (today's date ->
            # {"invites": n, "messages": n} directly, no account_id level).
            # Not attributable to either account now, surfaced here rather
            # than silently dropped.
            legacy_today[key] = value
    result = dict(
        today=_today_key(), by_account=by_account, month=_month_key(),
        noted_invites_sent_this_month=notes_this_month,
        noted_invites_cap_this_month=MAX_NOTED_INVITES_PER_MONTH,
    )
    if legacy_today:
        result["legacy_pre_cutover_today"] = legacy_today
    _ok(**result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("selftest").set_defaults(func=cmd_selftest)

    p = sub.add_parser("resolve")
    p.add_argument("linkedin_url")
    p.add_argument("--account", required=True,
                    help="Unipile account_id to resolve this profile "
                         "through (one of config/settings.py OWNERS's "
                         "unipile_account_id values).")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("invite")
    p.add_argument("provider_id")
    p.add_argument("--account", required=True,
                    help="Unipile account_id to send this invite from. "
                         "Must match the --account used to resolve this "
                         "provider_id. Recorded in contacts.json's "
                         "invited_accounts so contact-for-entity can later "
                         "tell this account has already been tried.")
    p.add_argument("--tag", default="",
                    help="Affinity entity_id this invite is for, so "
                         "check-accepted can report which company got "
                         "connected.")
    p.add_argument("--note", default="",
                    help="Not used by the current orchestrator prompt "
                         "(Juliette opted out of the free tier note "
                         "quota entirely on 2026-08-17). Left available "
                         "in case that changes.")
    p.set_defaults(func=cmd_invite)

    p = sub.add_parser("message")
    p.add_argument("provider_id")
    p.add_argument("text")
    p.add_argument("--account", required=True,
                    help="Unipile account_id to send this message from. "
                         "Resolve fresh from Affinity's Owners field every "
                         "time, do not cache from a previous call.")
    p.set_defaults(func=cmd_message)

    p = sub.add_parser("contact-for-entity")
    p.add_argument("entity_id", help="Affinity list entry id (the --tag "
                    "value used when this company was invited).")
    p.set_defaults(func=cmd_contact_for_entity)

    sub.add_parser("register-webhooks").set_defaults(func=cmd_register_webhooks)
    sub.add_parser("check-accepted").set_defaults(func=cmd_check_accepted)
    sub.add_parser("check-replies").set_defaults(func=cmd_check_replies)
    sub.add_parser("counts").set_defaults(func=cmd_counts)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
