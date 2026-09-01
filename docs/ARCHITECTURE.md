# Architecture notes

## Terminal loop, cloud scheduled task, or server: what "always on" actually needs

Four different things get called "running the automation" and they behave
very differently:

- A Claude Code terminal session used interactively. Stops the moment the
  window closes or the laptop sleeps. Good for writing and testing this
  code. Not a runtime for anything that needs to react while you are not
  looking at it.
- A local continuous loop (`scripts/run_forever.sh`), run in the
  foreground, via `nohup`, or as a macOS launchd service. Wakes up three
  times a day, at the clock times in `DAILY_RUN_TIMES`
  (config/settings.py, default 10am/1pm/6pm, matched to when Juliette
  actually reviews approvals), invokes Claude Code non-interactively for
  one pass, then sleeps until the next scheduled time. Handles everything
  that is not event driven: picking up newly imported companies, reading
  approval decisions, sending follow ups.
- A local webhook receiver (`scripts/webhook_receiver.py`), added
  2026-08-17 at Juliette's request, running continuously alongside the
  loop above, exposed to the internet via ngrok. This is the actual
  "always on" mechanism for connection acceptance and reply detection
  specifically, not the three-times-a-day loop; see "Where the model boundary
  sits, and where it bends" below for why it holds no credentials, and
  docs/RUNNING_LOCALLY.md, "Webhook setup," for the mechanics.
- A scheduled task (Claude Code Remote's create_trigger, not local cron).
  This was the original plan, ruled out on 2026-08-17: those tasks run in
  a cloud sandbox with an outbound network allowlist that does not include
  Unipile's API, confirmed by testing an identical Unipile curl call from
  this cloud sandbox (failed, TLS reset) versus from a local terminal
  (worked immediately). No amount of correct code fixes an unreachable
  host, so this path is closed unless that allowlist changes.
- A fully hosted persistent server, as an alternative to running the
  receiver and loop on Juliette's own machine. Would remove the
  dependency on her laptop being on and ngrok staying connected. Not done
  now because it needs hosting, uptime, and someone to notice when it
  falls over, worth revisiting only if the local setup proves unreliable.

Even with a real webhook now in place, one limitation does not go away:
Unipile's own "new relation" event, the one that tells you an invite was
accepted, is documented as capable of lagging up to about 8 hours after
the real acceptance, because LinkedIn does not expose that event live to
anyone, including Unipile. The webhook means this project reacts the
moment Unipile itself knows, which is strictly better than also waiting
for the next 30 minute poll on top of that, but it does not make
LinkedIn's own side any faster. Do not expect acceptance to look instant.

## Why state lives in Affinity, not a separate database

The Clover Deal Pipeline list already has Status, Pass Reason, and enriched
LinkedIn fields. Notes are a first class object with a UI Juliette already
uses daily. Keeping outreach stage and draft messages there, instead of in a
database only this codebase can read, means she can see and correct anything
mid pipeline in the tool she already has open, the same principle behind
Alpgency's "review card carries the score, reasoning, and exact message in
one tap." A hidden state store would be more normal engineering practice and
a worse fit for how she actually works.

Split further on 2026-08-19, once it became clear the two objects were
being used for two different jobs and paying for it: **Status tells the
agent what to do, notes tell it what to send.** Before this, "has Juliette
decided yet" was answered by fetching and text-matching a note, per
company, every poll cycle, for every company still waiting on her — a
transcript audit found the same ~109 companies checked this way ~9 times
in one day. Status = Pending Approval / Approved / Passed
(config/fields.py) answers the same question for every company at once,
for free, in the one search_list_entries call Stage 1 already makes.
Notes still carry the actual drafted text and still are what Juliette
edits directly; the agent now reads a company's notes exactly once, at
the moment Status flips to Approved, not on every cycle it happens to
still be pending. See prompts/orchestrator.md's "Guiding principle" at
the top and Stage 4.

## No Unipile connector exists yet

Checked the MCP connector registry, there is no ready made Unipile
connector to install, unlike Affinity or Google Drive here. That means
Unipile is reached through direct HTTPS calls to their REST API using the
account's API key, not a bound tool, done in exactly one place:
scripts/unipile_cli.py. Confirmed reachable and working from a local
terminal on 2026-08-17 (not from this cloud sandbox, see above).

Traffic runs both directions now, not just outbound. scripts/unipile_cli.py
still makes every outbound call, but scripts/webhook_receiver.py is the
inbound half, a small always running program Unipile calls into over the
internet (via ngrok) when a connection is accepted or a message arrives.
It is intentionally the least capable piece of code in this project: no
Affinity access, no Anthropic access, no judgment, it checks one shared
secret header and appends the event to a log file. See "Where the model
boundary sits, and where it bends" below for why that matters.

## Where the model boundary sits, and where it bends

Two steps use judgment: the thesis fit and stealth check, and drafting the
outreach message (plus the follow up and reply variants). All take
structured input and return structured output (a verdict, a draft), never
a credential, never a raw instruction to send anything outside of calling
the one deterministic script that can actually send.

The boundary bends in one place, deliberately: because the runtime is
headless Claude Code rather than a plain script (see
docs/RUNNING_LOCALLY.md, "How the judgment steps actually run"), the model
itself holds the Affinity MCP tool calls and decides when to write a
Status change or a note, which is looser than "the model returns JSON and
nothing else." What stays hard and deterministic, not delegated to the
model's judgment under any framing, is Unipile: every invite and every
message goes through scripts/unipile_cli.py, which enforces the daily send
cap itself by reading and writing logs/send_counts.json before making the
network call, independent of what the orchestrator prompt believes it is
allowed to do. That is the one action here that is expensive to undo (an
invite sent, a message a founder reads), so it is the one kept outside the
model's discretion entirely, mirroring the boundary Alpgency's own
proposal draws even though the Affinity side of this implementation does
not fully match it.

scripts/webhook_receiver.py sits outside this boundary question entirely
rather than bending it further: it holds zero credentials of any kind, no
Affinity access, no Anthropic access, and makes zero decisions, it only
verifies a shared secret and appends whatever Unipile sent to a log file.
The model only ever sees its output secondhand, through
scripts/unipile_cli.py's check-accepted and check-replies commands, which
do the actual matching against Affinity entity_ids. A bug in the receiver
can lose or duplicate an event; it cannot cause an unwanted send or an
unwanted Affinity write, since it is not wired to either.
