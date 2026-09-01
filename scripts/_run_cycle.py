#!/usr/bin/env python3
"""
One-shot cycle helper: resolves LinkedIn profiles, sends invites, sends
messages. Prints one JSON object per action to stdout. Called by the
orchestrator (Claude) when it cannot use shell variable expansion.
Cleans itself up by printing results only — no side effects beyond what
the standard CLI commands do.
"""
import json, os, subprocess, sys

# ── load .env (same logic as unipile_cli.py itself) ──────────────────────────
_env_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _, _v = _line.partition("=")
            if _k.strip():
                os.environ[_k.strip()] = _v.strip()

JULIETTE = os.environ.get("UNIPILE_LINKEDIN_ACCOUNT_ID_JULIETTE", "")
HUGO     = os.environ.get("UNIPILE_LINKEDIN_ACCOUNT_ID_HUGO", "")

CLI = os.path.join(os.path.dirname(__file__), "unipile_cli.py")

def cli(*args):
    r = subprocess.run(
        [sys.executable, CLI] + list(args),
        capture_output=True, text=True
    )
    try:
        return json.loads(r.stdout.strip())
    except Exception:
        return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "returncode": r.returncode}


# ── parse command from argv ───────────────────────────────────────────────────
cmd = sys.argv[1] if len(sys.argv) > 1 else "info"

if cmd == "info":
    print(json.dumps({
        "juliette_account_set": bool(JULIETTE),
        "hugo_account_set": bool(HUGO),
    }))

elif cmd == "resolve-stage4":
    # Resolve LinkedIn slugs needed for Stage 4 (Approved) sends.
    results = {
        "simone": cli("resolve", "simonecasagranda", "--account", JULIETTE),
        "aidan":  cli("resolve", "aidantiruvan",     "--account", JULIETTE),
    }
    print(json.dumps(results))

elif cmd == "resolve-stage2":
    # Resolve LinkedIn slugs for today's 4 new Hugo-owned companies (Stage 2).
    slugs = {
        "bollwerk": ("oisin-maher",                                              HUGO,    "250817539"),
        "hoshi":    ("jiir-awdir-9417a5163",                                     HUGO,    "250817540"),
        "inaya":    ("davidedibenedetto-artificial-intelligence-data-analytics",  HUGO,    "250817541"),
        "manie":    ("andre-pedro-9404426a",                                      HUGO,    "250817542"),
    }
    results = {}
    for name, (slug, account, list_entry_id) in slugs.items():
        results[name] = {
            "resolve": cli("resolve", slug, "--account", account),
            "list_entry_id": list_entry_id,
        }
    print(json.dumps(results))

elif cmd == "send-stage4":
    # Send the two approved follow-up messages (Stage 4).
    # provider_ids are passed as argv[2] (simone) and argv[3] (aidan).
    simone_pid = sys.argv[2]
    aidan_pid  = sys.argv[3]

    results = {}

    # Simone Casagranda — follow up from Juliette
    msg_simone = (
        "Hey Simone,\n\n"
        "Just a friendly nudge. If it makes sense to connect, feel free to grab a slot here:\n"
        "https://calendar.app.google/QVkh2MeVPdneFYUx5\n\n"
        "Cheers,\nJuliette"
    )
    results["simone"] = cli("message", simone_pid, msg_simone, "--account", JULIETTE)

    # Aidan Tiruvan (Archal Labs) — follow up from Juliette
    msg_aidan = (
        "Hey Aidan,\n\n"
        "Just a friendly nudge. If it makes sense to connect, feel free to grab a slot here:\n"
        "https://calendar.app.google/QVkh2MeVPdneFYUx5\n\n"
        "Cheers,\nJuliette"
    )
    results["aidan"] = cli("message", aidan_pid, msg_aidan, "--account", JULIETTE)

    print(json.dumps(results))

elif cmd == "invite-stage2":
    # Send invites for today's 4 new Hugo-owned companies (Stage 2).
    # argv[2..] are: bollwerk_pid hoshi_pid inaya_pid manie_pid
    pids = {
        "bollwerk": (sys.argv[2], "250817539"),
        "hoshi":    (sys.argv[3], "250817540"),
        "inaya":    (sys.argv[4], "250817541"),
        "manie":    (sys.argv[5], "250817542"),
    }
    results = {}
    for name, (provider_id, tag) in pids.items():
        results[name] = cli("invite", provider_id,
                            "--account", HUGO,
                            "--tag",     tag)
    print(json.dumps(results))

else:
    print(json.dumps({"error": f"unknown cmd: {cmd}"}))
    sys.exit(1)
