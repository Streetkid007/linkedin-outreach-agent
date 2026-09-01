# Clover Outreach Agent

Closes the gap in the Alpgency proposal's own pipeline: once a company clears
your thesis check in Affinity, this connects with the founder on LinkedIn
first, waits for acceptance (LinkedIn will not let you message someone who
has not accepted), then sends the real outreach message, drafted for your
approval, and learns from your feedback over time.

## Why this runs locally, continuously, not as a cloud scheduled task

Originally planned as a Claude Code Remote scheduled task. Tested directly
on 2026-08-17: Unipile's API is unreachable from that cloud sandbox
(outbound network allowlist blocks it), while it works immediately from a
normal local terminal. So this runs as three pieces on your own machine
instead, all covered step by step in `docs/GETTING_STARTED_TERMINAL.md`:
a small webhook receiver Unipile talks to directly, ngrok giving that
receiver a public address, and `scripts/run_forever.sh`, which wakes up
three times a day (config/settings.py `DAILY_RUN_TIMES`, default
10am/1pm/6pm) for everything the webhook does not cover. See `docs/RUNNING_LOCALLY.md` for the reasoning and background/
reboot surviving options, and `docs/ARCHITECTURE.md` for the full model.

## Pipeline

1. Thesis check. Reads companies at Status = New in the Clover Deal Pipeline
   (Affinity list 296071) that have not been checked yet, judges them against
   your thesis, and either leaves Status = New (in scope) or sets it to
   Out of Scope with a Pass Reason. Also flags whether the target company
   looks like it is still in stealth, which decides the message template.
2. Connect. For in scope companies with an unresolved LinkedIn relation,
   resolves the founder's LinkedIn profile (already enriched in most records
   under LinkedIn Profile (Founders/CEOs)) and sends a bare connection
   request, no note attached, by your choice. Acceptance is detected via
   Unipile's webhook, not polling, see Stage 2b in prompts/orchestrator.md.
3. Message. Once the webhook reports the invite accepted, drafts the
   outreach message (branched by profile category and language) and
   writes it as an Affinity note marked pending approval. Nothing sends
   here without you.
4. Approval and feedback. Reads your decision on that note (approve as is,
   edited text, or rejected with a reason), sends on approval, and appends
   your reasoning to a running style log that future drafts read from.
5. Reply and booking. Watches for a reply via the same webhook mechanism,
   updates Status to Reached Out or further along the pipeline, and flags
   it for you.

## Status as of 2026-08-17

Unipile is connected and confirmed reachable from a local terminal.
Affinity's Status field has the outreach substates (New, Invite Sent,
Connected, Reached Out, Follow Up Sent, Out of Scope). The thesis rules,
check size, and outreach playbook templates are sourced and confirmed. The
Founder LinkedIn (Verified) field exists and is populated at intake by the
whatsapp-to-affinity skill. Acceptance and reply detection now run on
Unipile's webhook rather than polling, and invites are sent with no
personalized note by design. What is left is operational, not design: work
through `docs/GETTING_STARTED_TERMINAL.md` once, start to finish, then it
runs on its own.
