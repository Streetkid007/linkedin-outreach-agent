import json

filepath = '/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/c5f237bb-4078-4f4e-96d0-6fd66c53870e/tool-results/mcp-claude_ai_Affinity-search_list_entries-1787743795203.txt'

with open(filepath, 'r') as f:
    raw = json.load(f)

if isinstance(raw, dict):
    entries = raw.get('data', raw.get('list_entries', []))
    pagination = raw.get('pagination', {})
elif isinstance(raw, list):
    entries = raw
    pagination = {}

print(f"PAGINATION: totalCount={pagination.get('totalCount')}, nextCursor={pagination.get('nextCursor')}")
print(f"ENTRY COUNT: {len(entries)}")
print()

# Understand first entry
if entries:
    e = entries[0]
    print("KEYS:", list(e.keys()))
    fields = e.get('fields', {})
    print("FIELD KEYS (first 30):", list(fields.keys())[:30])
    print()
    print(json.dumps(e, indent=2)[:4000])
