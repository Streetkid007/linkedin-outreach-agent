# Getting started, step by step

This is the one document to follow top to bottom the first time. It
assumes you have never used a terminal before, so every step spells out
exactly what to type and what you should see afterward. If something on
your screen does not match what is described, stop at that step rather
than continuing, and either fix it or come back and ask before moving on.

By the end of this document you will have three terminal windows (or
three tabs in one window) open at the same time, each doing one job,
continuously:

1. A small local program that listens for LinkedIn events from Unipile.
2. ngrok, which gives that local program a real internet address so
   Unipile can actually reach it.
3. The main loop, which checks Affinity every 30 minutes and does the
   actual work: thesis checks, sending invites, drafting messages.

All three need to keep running. Closing all your terminal windows stops
everything (there is a way to make it survive that too, covered at the
end, but get the basic version working first).

## Step 0: what "the terminal" is

On a Mac, the terminal is an app called Terminal, already installed,
found in Applications, Utilities, Terminal, or by pressing Command and
Space together, typing "Terminal," and pressing Return. Opening it shows
a mostly empty window with some text ending in a `$` or `%` symbol,
this is called the prompt, it means the terminal is waiting for you to
type a command. Every instruction below that starts with a `$` is
something to type there and press Return to run; you do not type the
`$` itself, that is just there to show it is a command.

You already have some experience with this specifically for Claude Code,
since you ran a curl command successfully in a Claude Code terminal
session before. This document assumes only that level of familiarity,
nothing more.

## Step 1: unzip the project

Find the zip file you downloaded (probably in your Downloads folder),
double click it, this creates a folder called `clover-outreach-agent`
next to it. Move that whole folder somewhere you will keep it, for
example directly in your home folder or in Documents, not somewhere
temporary like Downloads that you might clean out later.

Open Terminal, then navigate into that folder. Replace the path below
with wherever you actually put it:

```
$ cd ~/clover-outreach-agent
```

Check you are in the right place:

```
$ ls
```

You should see a list of folders including `config`, `docs`, `scripts`,
`src`, and `prompts`. If you instead see an error like "No such file or
directory," the path in the `cd` command above does not match where you
put the folder, adjust it and try again.

Every command in the rest of this document assumes you are inside this
folder. If you close Terminal and reopen it later, you will need to `cd`
back into it again first before anything else will work.

## Step 2: install the two things this project needs

```
$ pip3 install requests flask
```

You should see a series of lines ending in something like
"Successfully installed ..." If instead you see "pip3: command not
found," Python itself is not installed or not on your PATH, that is
outside the scope of this document, but this is unlikely given your
existing setup.

## Step 3: load your credentials into this terminal window

Your Unipile keys and a few settings live in a file called `config/.env`
inside the project, already filled in for you. Before any of the
commands below will work, this terminal window needs to read that file
into memory:

```
$ set -a && source config/.env && set +a
```

Nothing visible happens when this works, that is normal, it does not
print anything on success. This step only affects the one terminal
window you ran it in. Every new terminal tab or window you open later in
this guide needs this same command run again in it first, that is not a
mistake, it is just how this works: think of it as unlocking this
specific window.

## Step 4: confirm Unipile actually works from here

```
$ python3 scripts/unipile_cli.py selftest
```

You should see a line of JSON text containing your connected LinkedIn
account's details, this is the same account you saw in your very first
curl test. If you instead see something starting with `{"error":`,
re-check Step 3 ran in this same window with no typos, and that you are
in the right folder (Step 1).

## Step 5: set up ngrok, so Unipile can reach your computer

Unipile needs to send a message to a real internet address whenever
something happens (a connection accepted, a reply received). Your
computer does not have one of those by default, ngrok creates one that
points at a program running on your machine.

1. Go to ngrok.com in your browser and create a free account.
2. After signing up, their dashboard shows a command that looks like
   `ngrok config add-authtoken <a long code>`. Copy that exact command
   and run it in your terminal (the same window is fine, no need for
   Step 3 again for this one).
3. Still on the ngrok dashboard, look for "Domains" or "Dev domain,"
   free accounts get one fixed web address that is yours permanently,
   something like `https://your-name.ngrok-free.app`. If you do not see
   one already assigned, there should be a button to claim one, do that
   now. Write this address down, you will need it in Step 8.
4. If you do not already have the `ngrok` command available, their
   dashboard also has a "Download" or "Install" link for Mac, follow
   that, it is usually a single command using Homebrew
   (`brew install ngrok`) if you have Homebrew, or a downloadable
   installer otherwise.

Do not start ngrok yet, that happens in Step 7, in its own terminal tab.

## Step 6: open a new terminal tab for the webhook receiver

In Terminal, press Command and T to open a new tab (or Command and N for
a whole new window, either is fine). In this new tab, run Steps 1 and 3
again (navigate into the folder, load the credentials), then start the
receiver:

```
$ cd ~/clover-outreach-agent
$ set -a && source config/.env && set +a
$ .venv/bin/python3 scripts/webhook_receiver.py
```

You should see:
```
Listening on http://0.0.0.0:8000 (health check at /healthz)
```

Leave this tab open and running, do not close it or press Control and C
in it. This is job 1 of the three described at the top of this document.

## Step 7: open another new tab for ngrok

Command and T again for a third tab. This one does not need the project
folder or the credentials, just run:

```
$ ngrok http 8000 --url https://YOUR-ACTUAL-NGROK-DOMAIN.ngrok-free.app
```

Replace the placeholder with the exact address you claimed in Step 5.
You should see a screen with a box showing "Session Status: online" and
a line labeled "Forwarding" showing that same https address pointing at
`http://localhost:8000`.

Leave this tab open too, running, this is job 2.

## Step 8: tell this project your ngrok address, and register the webhooks

Go back to your very first terminal tab (or open a fourth one, running
Steps 1 and 3 again if so). Open the file `config/.env` in a text editor
(TextEdit works, or ask Claude Code to open it for you), find the line
that says:

```
WEBHOOK_BASE_URL=
```

and change it to your actual ngrok address from Step 5/7, for example:

```
WEBHOOK_BASE_URL=https://your-name.ngrok-free.app
```

Save the file. Back in the terminal, reload it (Step 3 again, since the
file changed) and run the one time registration command:

```
$ set -a && source config/.env && set +a
$ python3 scripts/unipile_cli.py register-webhooks
```

You should see JSON containing `"status": "registered"`. This tells
Unipile, permanently, to start sending events to your ngrok address. You
only need to run this once, ever, unless your ngrok address changes.

## Step 9: verify the whole chain actually works, end to end

Still in that same tab:

```
$ curl https://YOUR-ACTUAL-NGROK-DOMAIN.ngrok-free.app/healthz
```

You should see `{"secret_configured":true,"status":"ok"}`. If this
works, a request went from your terminal, over the internet, through
ngrok, back down to the receiver running on your machine in Step 6, and
back. That is the same path a real Unipile event will take.

## Step 10: start the actual continuous loop

One more new tab (Command and T), Steps 1 and 3 again, then:

```
$ ./scripts/run_forever.sh
```

You should see lines like:
```
starting continuous runner, scheduled for 10:00 13:00 18:00 local time daily
sleeping 8213s until next scheduled run at 2026-08-25 10:00 CEST
```
and then nothing else until that time arrives, by design: it always waits
for the next entry in `DAILY_RUN_TIMES` (config/settings.py) rather than
running immediately on start, so starting or restarting this script never
sneaks in an extra cycle outside its three-times-a-day schedule (see
docs/RUNNING_LOCALLY.md for why it runs three times a day, not
continuously). This is job 3, the main loop. Leave this tab running.

To actually see a poll cycle happen during this walkthrough instead of
waiting for the next scheduled hour, either run the exact `claude -p ...`
command from inside `scripts/run_forever.sh` directly in a scratch tab, or
temporarily set `DAILY_RUN_TIMES` in `config/.env` to a time a couple of
minutes from now, restart this script, and set it back to the real
schedule once you have seen it fire (this can take a minute or two once it
does, it is genuinely doing work: reading Affinity, running thesis
checks).

You should now have three tabs open and running: the receiver (Step 6),
ngrok (Step 7), and this loop. Nothing needs your attention right now,
this is the "always on" state described everywhere else in this project.

## Checking on it later

Open a new tab, `cd` into the folder, and:

```
$ tail -f logs/run.log
```

shows the loop's activity live, press Control and C to stop watching
(this does not stop the loop itself, just this view of it).

```
$ python3 scripts/unipile_cli.py counts
```

shows how many invites and messages have gone out today and this month.

## Stopping everything

Go to each of the three tabs and press Control and C in each. Closing
the Terminal app entirely also stops all of them.

## Making it survive closing Terminal or restarting your Mac

Once you are comfortable it is working correctly over a few days, see
`docs/RUNNING_LOCALLY.md`, "Starting it," for how to move the loop (and,
if you want, the receiver) into a background service that keeps running
without a terminal window open. This is optional and not needed to get
started.
