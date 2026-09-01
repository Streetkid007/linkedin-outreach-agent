# Running this continuously, locally

## Why local, not a Cowork scheduled task

Tested directly on 2026-08-17: a `curl` to Unipile's API from this Cowork
cloud sandbox failed with a TLS connection reset, traced to the sandbox's
outbound network allowlist not including unipile.com. The identical curl
command from your own terminal worked immediately. Cowork's scheduled
tasks run in that same kind of cloud sandbox, so the same block almost
certainly applies there too. Your machine has no such restriction. That is
the actual reason this runs locally now, not a preference, a hard
constraint discovered by testing it.

## What "continuous" means here

Two mechanisms working together, added 2026-08-17 at your request to use
a webhook rather than pure polling for connection and reply detection:

- `scripts/webhook_receiver.py` runs continuously and Unipile POSTs to it
  the instant it learns a connection was accepted or a message arrived.
  This needs a public internet address, which your machine does not have
  by default, so it is exposed through ngrok. See
  `docs/GETTING_STARTED_TERMINAL.md` for the full setup, this section is
  the reasoning behind it, not the walkthrough.
- `scripts/run_forever.sh` still wakes up at each clock time in
  `DAILY_RUN_TIMES` (config/settings.py, default 10am/1pm/6pm local time)
  for everything a webhook does not cover: picking up newly imported
  companies for a thesis check, reading your approval decisions from
  Affinity notes, and sending follow ups. It also asks
  `scripts/unipile_cli.py check-accepted` and `check-replies` each cycle,
  which is how whatever the webhook has queued up since the last cycle
  actually gets acted on.

  Changed from a fixed 60 minute interval to three fixed times a day on
  2026-08-24, for cost, not correctness: each cycle is a brand new
  headless Claude Code session, and every company still sitting in an
  approval or reply wait state gets its Affinity notes re-read from
  scratch every cycle until you act. An hourly loop ran 24 of those
  sessions a day (already halved down from 30 minutes on 2026-08-19 for
  the same reason; see git history if you want the transcript-audit
  numbers behind that first change) regardless of whether there was
  anything new to do. You said you actually only review approvals around
  10am, 1pm, and 6pm, so matching the schedule to that cuts session count
  to 3 a day, roughly an 8x reduction from the original hourly loop, with
  no functional loss: acceptance and reply detection are webhook driven
  regardless of this setting, so all this trades off is a newly imported
  company's first thesis check, or a cleared approval, waiting up to ~8h
  for the next slot instead of up to an hour, which does not matter for
  LinkedIn outreach pacing. Drop to two times a day (`DAILY_RUN_TIMES=10:00,18:00`
  in config/.env) if you want to cut this further; only add more times back
  in, or move them earlier/later, if you actually find yourself wanting
  faster turnaround on approvals in practice, not by default.

Honest limitation this does not remove: Unipile's own docs state the
`new_relation` webhook event "may be triggered up to 8 hours after the
connection is accepted," because LinkedIn does not expose real time
acceptance to anyone, including Unipile. The webhook means this project
reacts the moment Unipile itself knows, rather than however long until
the next poll on top of that, but it cannot make LinkedIn tell Unipile
any sooner. If you invite someone and they accept within a minute, do not
expect an instant reaction, up to several hours is normal and expected.

## How the judgment steps actually run

Each poll cycle shells out to your local Claude Code CLI, non-interactively:
`claude -p "$(cat prompts/orchestrator.md)" --allowedTools "..."`. That
prompt tells Claude exactly which Affinity MCP tools it may use, points it
at the real prompt templates and thesis rules already in this repo
(src/thesis_check.py, src/message_composer.py), and hard-requires every
single Unipile action to go through `scripts/unipile_cli.py` rather than
being called directly.

This was a real decision, not the only option: a standalone Python script
calling the Anthropic API directly, with its own Affinity REST
integration, was the other path. Local Claude Code won because your
session already has Affinity MCP authenticated against the exact field
ids config/fields.py was built from, and there is no confirmation that
those same field ids work against Affinity's raw REST API outside of MCP.
One integration point beats two, especially one already proven to work.
If you would rather move to a fully standalone script later (no
dependency on the `claude` CLI being installed and licensed on whatever
machine runs this), that is a bounded rewrite of src/affinity_client.py
plus filling in ANTHROPIC_API_KEY in config/.env; everything else,
including scripts/unipile_cli.py, stays as is.

## Setup, one time

Follow `docs/GETTING_STARTED_TERMINAL.md` top to bottom, it is the actual
step by step walkthrough (unzip, install dependencies, load credentials,
set up ngrok, register the webhooks, start all three pieces). This
section only covers what comes after you have done that once and want to
understand the background/reboot-surviving options.

## Starting it, once you have done the one time setup above

The webhook receiver (`python3 scripts/webhook_receiver.py`) and ngrok
(`ngrok http 8000 --url <your domain>`) each need their own terminal tab
running continuously, exactly as set up in
`docs/GETTING_STARTED_TERMINAL.md`. What follows is specifically about
the main loop, `scripts/run_forever.sh`.

Foreground, for testing, stops when you close the terminal:
```
./scripts/run_forever.sh
```
Watch `logs/run.log` and `logs/run_errors.log` in another terminal tab
while it runs the first couple of cycles.

Background, survives closing the terminal, does not survive a reboot on
its own:
```
nohup ./scripts/run_forever.sh > /dev/null 2>&1 &
```

Background, survives closing the terminal AND reboots (starts back up
next time you log in): install the launchd service.
```
cp scripts/com.clover.outreach-agent.plist ~/Library/LaunchAgents/
# then edit ~/Library/LaunchAgents/com.clover.outreach-agent.plist and
# replace every /Users/juliette/REPLACE_WITH_PATH with the real path
launchctl load ~/Library/LaunchAgents/com.clover.outreach-agent.plist
```
To stop it: `launchctl unload ~/Library/LaunchAgents/com.clover.outreach-agent.plist`.
The webhook receiver and ngrok do not currently have their own launchd
templates, they are simple enough to leave running in terminal tabs for
now; ask if you want those turned into background services too once the
basic setup has run reliably for a while.

## Stopping it

Foreground: Ctrl+C, in each of the three tabs (receiver, ngrok, loop).
Background (`nohup`): find and kill the process, `pgrep -f run_forever.sh`
then `kill <pid>`.
launchd: `launchctl unload ~/Library/LaunchAgents/com.clover.outreach-agent.plist`.

## The daily send cap, and why the numbers moved

Three sources were checked for LinkedIn's actual limits, and they do not
agree with each other. Unipile's own docs describe a paid account sending
80 to 100 invitations a day, about 200 a week, versus a free account far
lower. LinkedIn's own Help Center, surfaced through a search, describes a
weekly connection request ceiling of roughly 100 to 200 that applies "to
all account types," with the free versus paid difference being about
whether you can attach a personalized note to more than about 5 requests
a month, not about total volume. A third source, a LinkedIn Pulse post,
gives yet another set of numbers again: 80 connections a week free versus
100 paid, 100 messages a week free versus 150 paid, and a note character
limit of 200 free versus 300 paid.

LinkedIn does not currently publish one clear figure for any of this, so
none of these three is simply correct while the others are wrong, they
are outside observers describing a system that is not fully documented
and may not be static. Rather than pick whichever number was most
convenient, `config/settings.py` now sits under the lowest figure any
source gave: `MAX_INVITES_PER_DAY` and `MAX_MESSAGES_PER_DAY` are both 10
(about 70 a week), comfortably under even the 80 a week free tier figure.
`INVITE_NOTE_MAX_CHARS` defaults to 200, the more conservative of the two
character limits cited, since your connected account is currently free.

Separately, `MAX_NOTED_INVITES_PER_MONTH` defaults to 5, following
LinkedIn's own Help Center specifically (not either third party source),
which describes free accounts being able to attach a note to only about 5
connection requests a month, with the rest still sending, just blank.

Update 2026-08-17: you decided not to use any of that allowance at all,
by choice, not as a fallback. `prompts/orchestrator.md`'s connect stage no
longer asks for a note, every invite goes out blank, always. The
`MAX_NOTED_INVITES_PER_MONTH` tracking and the automatic note dropping in
`scripts/unipile_cli.py` are still there, inert, only relevant if you ever
pass `--note` by hand or decide to turn notes back on later. As before,
this does not cost you anything substantive: the real, fully personalized
outreach message was always the separate approved message
`scripts/unipile_cli.py message` sends after the connection is accepted
(prompts/orchestrator.md, Stage 3), never the invite note.

`scripts/unipile_cli.py` enforces every cap above itself, counting in
`logs/send_counts.json`, independent of whatever the orchestrator prompt
thinks it is allowed to do, and adds a random 30 to 120 second delay
before every actual send, per the general advice across all three sources
to space calls out rather than fire them at fixed intervals. This matters
specifically for continuous polling: without the daily cap, clearing a
backlog of 20 approved messages in your first session would fire all 20
in the same poll cycle seconds apart, which is exactly the burst pattern
that gets accounts flagged. Check today's and this month's usage any time
with:
```
python3 scripts/unipile_cli.py counts
```
If you upgrade off the free plan, update `config/.env`:
`MAX_NOTED_INVITES_PER_MONTH` to something effectively unlimited and
`INVITE_NOTE_MAX_CHARS` to 300, and only then consider raising
`MAX_INVITES_PER_DAY` / `MAX_MESSAGES_PER_DAY`, in small steps, watching
`logs/run_errors.log` for a couple of weeks each time rather than jumping
straight to the highest number any source cited.

## Webhook setup, technical reference

This is the reasoning and exact mechanics behind the webhook; for the
actual click by click steps, use `docs/GETTING_STARTED_TERMINAL.md`.

Unipile supports registering a URL it will POST to when something
happens, documented at
https://developer.unipile.com/reference/webhookscontroller_createwebhook.
`python3 scripts/unipile_cli.py register-webhooks` calls that endpoint
twice, once for `source: "users"`, `events: ["new_relation"]` (a
connection got accepted), once for `source: "messaging"`,
`events: ["message_received"]` (a new inbound message arrived), both
pointing at your ngrok address plus `/webhooks/new-relation` or
`/webhooks/new-message`.

Two things worth knowing about the payload Unipile actually sends,
straight from their docs: the `new_relation` event does not include any
reference back to the specific invitation you sent, only the LinkedIn
profile that accepted (`user_provider_id`). That is why Stage 2 tags every
invite with your Affinity `entity_id` via `invite --tag`, recorded in
`logs/contacts.json`, so `check-accepted` can answer "which company is
this about" itself instead of asking the model to guess. Second, Unipile
requires your endpoint to respond with status 200 within 30 seconds, or
it retries up to five times with increasing delay; `scripts/webhook_receiver.py`
does nothing but write one line to a log file and return 200, so this
should never be close.

Security is a shared secret, not a cryptographic signature: Unipile's own
docs describe no HMAC-style verification, just a custom header you define
yourself when registering (`Unipile-Auth` here, value is
`WEBHOOK_SHARED_SECRET` from `config/.env`, already generated for you).
`scripts/webhook_receiver.py` rejects any request missing or mismatching
that header with a 401. Since your ngrok URL is public, anyone who
guessed it could otherwise inject a fake "connection accepted" event; this
header is what stops that.

## Follow up approval

`FOLLOW_UP_REQUIRES_APPROVAL` in config/settings.py defaults to `true`,
meaning the one week follow up goes through the same PENDING APPROVAL note
and your review as the first message, on the reasoning that you asked for
auto invite but approve message, and a follow up is a message. Set it to
`false` in config/.env if you would rather it send automatically once
drafted. Reply handling has no such switch; it always requires approval,
since it is the message most likely to hinge on a nuance a first pass
judgment would miss.
