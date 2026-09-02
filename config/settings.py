"""
Tunable runtime settings for continuous local execution. Split out from
fields.py because these are operational knobs (how often, how many, gated
or not), not Affinity schema constants.

Correction from an earlier version of this file, worth stating plainly
rather than quietly fixing: Unipile's own docs
(https://developer.unipile.com/docs/provider-limits-and-restrictions)
describe paid accounts getting "80 to 100 invitations per day," which
this file first read as meaning the free tier caps total invite volume
far lower. Checking LinkedIn's own Help Center directly (surfaced
2026-08-17) shows that is not the real picture: LinkedIn enforces a
weekly connection request ceiling of roughly 100 to 200, "across all
account types, whether Free, Premium, or Sales Navigator." Upgrading does
not raise that core volume ceiling. What upgrading actually changes is
narrower: a free account can attach a personalized note to only about
five connection requests a month; every request beyond that still sends,
just without a note. Paid tiers can attach a note to every request.

Practical effect on this project: MAX_INVITES_PER_DAY below is already
safely inside the roughly 100 to 200 a week ceiling regardless of which
LinkedIn plan is connected, so there is no volume reason to upgrade.

Update 2026-08-17: you decided not to use any of the free tier's monthly
personalized note allowance at all, on purpose, not just as a fallback.
prompts/orchestrator.md's connect stage no longer asks for a note, so
every invite goes out blank. MAX_NOTED_INVITES_PER_MONTH and the note
quota tracking in scripts/unipile_cli.py are left in place, inert, as a
safety net in case you change your mind later, not something you need to
think about day to day. The real personalized outreach message was
always sent separately, as an approved message after the connection is
accepted (see prompts/orchestrator.md, Stage 3), never the invite note,
so nothing about the substance of your outreach changes from skipping
notes entirely.

Unipile's page does not publish a separate limit for ordinary messages to
an existing first degree connection (its message related numbers are
about InMail, a different feature: 800 free InMails per month, 30 to 50
per day recommended pacing). MAX_MESSAGES_PER_DAY below is a self imposed
conservative cap for that reason, not a documented LinkedIn ceiling.

A second correction, from checking a third source (a LinkedIn Pulse post
dated April 2025) after the above: it gives yet another set of numbers,
80 connections a week free versus 100 a week paid, 100 messages a week
free versus 150 a week paid, and a note character limit of 200 for free
accounts versus 300 for paid, not the monthly note count LinkedIn's own
Help Center mentions. Three sources, three different numbers. LinkedIn
does not currently publish one single authoritative figure for any of
this, these are all outside observers describing a moving target, so
treat every number in this file as directional, not exact. The response
to that uncertainty is to sit comfortably under the lowest figure any
source gave rather than pick whichever number is most convenient, and to
let Unipile's actual error responses in logs/run_errors.log be the real
signal once the loop is running, not any blog post. That is why the
defaults below were tightened down from the first draft of this file.
"""

import os

# Fixed times of day (24h "HH:MM", local time) the continuous runner wakes
# up to check Affinity for new companies, read approval notes, and process
# anything the webhook receiver has queued up (see the webhook section
# below). Acceptance and reply detection themselves do not depend on this
# schedule at all, they arrive via the webhook the moment Unipile knows;
# this schedule just controls how quickly a queued webhook event actually
# gets acted on, and how quickly a newly imported company gets its first
# thesis check. LinkedIn's own "new relation" signal can still lag up to
# ~8h regardless (see the webhook section below and docs/ARCHITECTURE.md),
# that part is unrelated to this setting.
#
# Replaced a fixed POLL_INTERVAL_SECONDS with this on 2026-08-24, at your
# request: you said you actually only review approvals around 10am, 1pm,
# and 6pm, so an hourly wake-up (24 fresh headless Claude Code sessions a
# day, per scripts/run_forever.sh) was mostly re-reading the same
# unactioned Affinity notes with nothing new to do. Three wake-ups a day,
# matched to when you actually look, cuts session count roughly 8x with no
# functional loss: the worst case is a newly imported company's first
# thesis check, or a cleared approval, waiting up to ~8h for the next slot
# instead of up to 1h, which does not matter for LinkedIn outreach pacing.
# Add or move times here (and in config/.env via DAILY_RUN_TIMES,
# comma-separated) if your actual review rhythm changes.
DAILY_RUN_TIMES = [
    t.strip()
    for t in os.environ.get("DAILY_RUN_TIMES", "10:00,13:00,18:00").split(",")
    if t.strip()
]

# Hard ceiling on LinkedIn connection requests sent per rolling day, across
# all companies. The lowest weekly figure across three sources checked was
# 80 a week on a free account, call it roughly 11 to 12 a day; 10 a day
# (about 70 a week) sits under that with some margin. Raise it in steps,
# not to whatever the highest cited number was, once a couple of weeks
# pass with no rate limit errors or LinkedIn restriction notices in
# logs/run_errors.log, and once you know for certain which plan is
# actually connected.
MAX_INVITES_PER_DAY = int(os.environ.get("MAX_INVITES_PER_DAY", 20))

# Hard ceiling on first messages and follow ups sent per rolling day,
# combined. The lowest weekly figure seen for messages was 100 a week on a
# free account, call it roughly 14 a day; 10 a day sits under that with
# some margin, same reasoning as the invite cap above.
MAX_MESSAGES_PER_DAY = int(os.environ.get("MAX_MESSAGES_PER_DAY", 20))

# Character limit enforced on an invite note before scripts/unipile_cli.py
# will attach it. The two sources that mention a character limit at all
# disagree on the paid figure (300 in both) but the free figure only
# appears in one, 200. Defaulting to the safer 200 since your account is
# currently free; bump to 300 once you confirm an upgrade actually applies
# to the connected account, via INVITE_NOTE_MAX_CHARS=300 in config/.env.
INVITE_NOTE_MAX_CHARS = int(os.environ.get("INVITE_NOTE_MAX_CHARS", 200))

# Separate from the daily invite cap above: LinkedIn's own Help Center
# (not one of the two third party sources) describes free accounts being
# able to attach a personalized note to only about five connection
# requests a month, with additional requests still sending, just without
# a note. This has not been tested against what actually happens if you
# try to attach one past that count, so scripts/unipile_cli.py tracks this
# separately and silently drops the note once the month's quota is used,
# rather than finding out the hard way. Set to a very high number once you
# confirm a paid plan removes this restriction on your account.
MAX_NOTED_INVITES_PER_MONTH = int(
    os.environ.get("MAX_NOTED_INVITES_PER_MONTH", 5)
)

# Random delay window, in seconds, that scripts/unipile_cli.py sleeps
# before every invite or message send, never before a read like resolve
# or relation-status. Directly implements Unipile's "space calls randomly
# rather than at fixed intervals" guidance, and matters more than it looks
# for a script that might otherwise send several approved messages back to
# back in the same poll cycle the moment a backlog clears.
SEND_DELAY_MIN_SECONDS = int(os.environ.get("SEND_DELAY_MIN_SECONDS", 30))
SEND_DELAY_MAX_SECONDS = int(os.environ.get("SEND_DELAY_MAX_SECONDS", 120))

# --- Dual-account outreach, added 2026-08-24 ---
# Hugo's new Unipile workspace has both his and Juliette's LinkedIn
# connected, so outreach can now go out from either profile instead of
# always Juliette's, roughly doubling the safe daily invite/message
# ceiling (LinkedIn's caps are per profile, not per Affinity pipeline).
# Keyed by the exact string Affinity's Owners field uses for each person.
# prompts/orchestrator.md reads a company's Owners field (already returned
# free in Stage 1's search_list_entries call) and resolves it against this
# dict: if Hugo is listed, use his entry; otherwise (nobody listed, only
# Juliette listed, or someone else entirely) fall back to DEFAULT_OWNER.
# first_name feeds the "from <name> at Clover" line in message_composer's
# prompts; email is where reply-handling drafts ask founders to send
# materials.
OWNERS = {
    "Hugo Mendes": {
        "first_name": "Hugo",
        "email": "hugo.mendes@cloverfund.vc",
        "calendar_link": "https://calendar.app.google/4pQajyWMQULc1oBp9",
        "unipile_account_id": os.environ.get("UNIPILE_LINKEDIN_ACCOUNT_ID_HUGO", ""),
    },
    "Juliette Moortgat": {
        "first_name": "Juliette",
        "email": "juliette.moortgat@cloverfund.vc",
        "calendar_link": "https://calendar.app.google/QVkh2MeVPdneFYUx5",
        "unipile_account_id": os.environ.get("UNIPILE_LINKEDIN_ACCOUNT_ID_JULIETTE", ""),
    },
}
DEFAULT_OWNER = "Juliette Moortgat"

# Whether the one week follow up requires the same approve/edit/reject step
# in an Affinity note as the first message, or sends automatically once
# drafted. Defaulting to True (approval required) for the same reason the
# first message is approval gated: you said yes to auto invite, but
# approve message, and a follow up is still a message, not an invite. Flip
# to False once you are comfortable with the drafts and want one less
# thing to review.
FOLLOW_UP_REQUIRES_APPROVAL = (
    os.environ.get("FOLLOW_UP_REQUIRES_APPROVAL", "true").lower() != "false"
)

# Reply handling always drafts for approval, no setting to disable this:
# a reply is the highest stakes message in the sequence (it often decides
# whether someone gets a booking link), so this one is never auto-sent.

# Where the deterministic send-cap counter lives. Not committed; resets
# are fine, worst case you get one extra send-worth of headroom on a given
# day, never a runaway burst, since the cap script checks this file before
# every single send, not once per run.
SEND_COUNTS_PATH = os.environ.get(
    "SEND_COUNTS_PATH",
    os.path.join(os.path.dirname(__file__), "..", "logs", "send_counts.json"),
)

_LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")

# --- Webhook based acceptance and reply detection, added 2026-08-17 ---
# You asked for this explicitly instead of polling: scripts/webhook_receiver.py
# runs continuously and Unipile POSTs to it the moment it knows a connection
# was accepted or a message arrived, rather than the orchestrator asking
# Unipile every 30 minutes. See docs/RUNNING_LOCALLY.md, "Webhook setup",
# for the one time registration step and why a public URL (via ngrok) is
# required for Unipile to reach a receiver running on your own machine.
#
# Important honest caveat, not solved by switching to a webhook: Unipile's
# own docs state the new_relation event "may be triggered up to 8 hours
# after the connection is accepted," because LinkedIn does not expose
# accurate acceptance in real time to anyone, including Unipile. The
# webhook removes wasted polling and reacts the moment Unipile itself
# knows, it does not make LinkedIn tell Unipile any sooner.

# Port scripts/webhook_receiver.py listens on locally. ngrok points at this.
WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", 8000))

# Shared secret Unipile is configured to send back as the Unipile-Auth
# header on every webhook call, checked by webhook_receiver.py so random
# traffic hitting your public ngrok URL cannot inject fake "connected" or
# "replied" events. Generate your own long random string once; the value
# in config/.env was generated for you already, treat it like a password.
WEBHOOK_SHARED_SECRET = os.environ.get("WEBHOOK_SHARED_SECRET", "")

# Your ngrok (or other tunnel) public base URL, e.g.
# https://your-name.ngrok-free.app. Only used by
# `python scripts/unipile_cli.py register-webhooks`, the one time setup
# command that tells Unipile where to send events. Filled in during
# docs/RUNNING_LOCALLY.md, "Webhook setup".
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL", "")

# Append only logs webhook_receiver.py writes to and unipile_cli.py's
# check-accepted / check-replies commands read from. Deliberately dumb,
# line delimited JSON, so a crash never corrupts more than the last
# partial line, and so you can literally open these in a text editor if
# something looks wrong.
ACCEPTED_CONNECTIONS_LOG = os.path.join(_LOGS_DIR, "accepted_connections.jsonl")
INBOUND_MESSAGES_LOG = os.path.join(_LOGS_DIR, "inbound_messages.jsonl")

# How far into each log file has already been processed, so re-running
# check-accepted / check-replies never re-reports the same event twice.
WEBHOOK_CURSORS_PATH = os.path.join(_LOGS_DIR, "webhook_cursors.json")

# Persistent provider_id -> Affinity entity_id (and a little context)
# registry, written by `invite --tag` at Stage 2 and read by
# check-accepted / check-replies to answer "which company is this
# LinkedIn event actually about," since Unipile's webhook payloads only
# ever include LinkedIn's own identifiers, never yours.
CONTACTS_PATH = os.path.join(_LOGS_DIR, "contacts.json")

# provider_id -> Unipile chat_id, learned the first time a message is
# sent to someone (or the first time they reply), so later messages to
# the same person reuse the existing chat rather than starting a new one,
# per Unipile's own guidance to "always prefer chat_id" when a chat
# already exists.
CHATS_PATH = os.path.join(_LOGS_DIR, "chats.json")
