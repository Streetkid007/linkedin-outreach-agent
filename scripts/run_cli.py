#!/usr/bin/env python3
"""
Thin wrapper around unipile_cli.py that pre-loads config/.env before
running. Needed because the Claude Code Bash tool cannot run 'source'
shell built-ins, so env vars from config/.env are not available when
unipile_cli.py is invoked directly through Bash(python scripts/unipile_cli.py ...).

Usage: python scripts/run_cli.py <same args as unipile_cli.py>
"""
import os, sys

_env_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _key, _, _val = _line.partition("=")
            _key = _key.strip()
            _val = _val.strip()
            if _key and _key not in os.environ:
                os.environ[_key] = _val

# Now delegate to unipile_cli.main() with the same argv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import scripts.unipile_cli as _cli
sys.argv[0] = "unipile_cli.py"
_cli.main()
