"""Extracts key outreach fields from a search_list_entries JSON file, output to JSON."""
import json
from collections import defaultdict

FILE = '/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/68a36199-7b90-4434-9d48-8f1ca3402016/tool-results/mcp-claude_ai_Affinity-search_list_entries-1788172894313.txt'
OUT_FILE = '/Users/julietta/Documents/CloverAgent/clover-outreach-agent/affinity_entries_parsed.json'

STATUS_MAP = {
    19399924: 'New',
    25636245: 'Invite Sent',
    25636246: 'Connected',
    25653157: 'Pending Approval',
    25653158: 'Approved',
    19399925: 'Reached Out',
    25636247: 'Follow Up Sent',
    19719669: 'Passed',
    19399931: 'Out of Scope',
}

with open(FILE) as f:
    data = json.load(f)

pagination = data.get('pagination', {})
entries = data.get('data', [])

results = []

for entry in entries:
    eid = entry['entity']['id']
    ename = entry['entity']['name']
    list_entry_id = entry['id']
    created_at = entry.get('createdAt', '')

    fields_by_id = {f['id']: f for f in entry['entity'].get('fields', [])}

    # Status field-5086705
    status_f = fields_by_id.get('field-5086705', {})
    status_val = (status_f.get('value') or {}).get('data')
    if isinstance(status_val, dict):
        status_id = status_val.get('dropdownOptionId')
    elif isinstance(status_val, list) and status_val:
        status_id = status_val[0].get('dropdownOptionId') if isinstance(status_val[0], dict) else None
    else:
        status_id = None
    status_name = STATUS_MAP.get(status_id) if status_id else None

    # Pass Reason field-5086710
    pass_reason_f = fields_by_id.get('field-5086710', {})
    pass_reason_val = (pass_reason_f.get('value') or {}).get('data')
    pass_reason_ids = []
    if isinstance(pass_reason_val, dict):
        pr_id = pass_reason_val.get('dropdownOptionId')
        if pr_id:
            pass_reason_ids = [pr_id]
    elif isinstance(pass_reason_val, list):
        for item in pass_reason_val:
            if isinstance(item, dict) and item.get('dropdownOptionId'):
                pass_reason_ids.append(item['dropdownOptionId'])

    # Owners field-5086706
    owners_f = fields_by_id.get('field-5086706', {})
    owners_data = (owners_f.get('value') or {}).get('data') or []
    owners = []
    for o in owners_data:
        if isinstance(o, dict):
            fn = (o.get('firstName') or '').strip()
            ln = (o.get('lastName') or '').strip()
            name = (fn + ' ' + ln).strip()
            if name:
                owners.append(name)

    # Founder LinkedIn Verified field-5875046
    li_verified_f = fields_by_id.get('field-5875046', {})
    li_verified_val = (li_verified_f.get('value') or {}).get('data')
    if isinstance(li_verified_val, str):
        li_verified = li_verified_val
    elif isinstance(li_verified_val, list) and li_verified_val:
        item = li_verified_val[0]
        li_verified = item.get('link') or item.get('url') or item.get('text') or (item if isinstance(item, str) else None)
    else:
        li_verified = None

    # Affinity enriched founders LinkedIn affinity-data-linkedin-profile-founders-ceos
    li_enriched_f = fields_by_id.get('affinity-data-linkedin-profile-founders-ceos', {})
    li_enriched_data = (li_enriched_f.get('value') or {}).get('data') or []
    li_enriched = None
    for item in li_enriched_data:
        if isinstance(item, dict):
            li_enriched = item.get('link') or item.get('url') or item.get('text')
        elif isinstance(item, str):
            li_enriched = item
        if li_enriched:
            break

    # Description affinity-data-description
    desc_f = fields_by_id.get('affinity-data-description', {})
    desc_raw = (desc_f.get('value') or {}).get('data') or ''
    desc = str(desc_raw)[:300] if desc_raw else ''

    # Year founded affinity-data-year-founded
    year_f = fields_by_id.get('affinity-data-year-founded', {})
    year_founded = (year_f.get('value') or {}).get('data')

    results.append({
        'list_entry_id': list_entry_id,
        'entity_id': eid,
        'name': ename,
        'created_at': created_at,
        'status_id': status_id,
        'status_name': status_name,
        'pass_reason_ids': pass_reason_ids,
        'owners': owners,
        'founder_linkedin_verified': li_verified,
        'affinity_linkedin_founders': li_enriched,
        'description': desc,
        'year_founded': year_founded,
    })

# Group by status
by_status = defaultdict(list)
for r in results:
    key = r['status_name'] or 'None/Unknown'
    by_status[key].append(r)

status_order = ['New', 'Invite Sent', 'Connected', 'Pending Approval', 'Approved',
                'Reached Out', 'Follow Up Sent', 'Passed', 'Out of Scope', 'None/Unknown']

output = {
    'pagination': {
        'totalCount': pagination.get('totalCount'),
        'nextCursor': pagination.get('nextCursor'),
        'prevUrl': pagination.get('prevUrl'),
        'nextUrl': pagination.get('nextUrl'),
    },
    'entries_in_page': len(results),
    'summary_by_status': {s: len(by_status.get(s, [])) for s in status_order if by_status.get(s)},
    'by_status': {s: by_status[s] for s in status_order if by_status.get(s)},
    'all_entries': results,
}

with open(OUT_FILE, 'w') as f:
    json.dump(output, f, indent=2)

print(f"Written to {OUT_FILE}")
print(f"totalCount: {pagination.get('totalCount')}")
print(f"nextCursor: {pagination.get('nextCursor')}")
print(f"Entries in page: {len(results)}")
print()
print("Summary by status:")
for s in status_order:
    cnt = len(by_status.get(s, []))
    if cnt:
        print(f"  {s}: {cnt}")
for s, g in by_status.items():
    if s not in status_order:
        print(f"  {s}: {len(g)}")

print()
print("=== ALL ENTRIES ===")
for status in status_order:
    group = by_status.get(status, [])
    if not group:
        continue
    print(f"\n--- {status} ({len(group)}) ---")
    for r in group:
        print(f"  list_entry_id={r['list_entry_id']} | entity_id={r['entity_id']} | name={r['name']} | created_at={r['created_at']}")
        print(f"    owners={r['owners']}")
        print(f"    pass_reason_ids={r['pass_reason_ids']}")
        print(f"    founder_linkedin_verified={r['founder_linkedin_verified']}")
        print(f"    affinity_linkedin_founders={r['affinity_linkedin_founders']}")
        print(f"    year_founded={r['year_founded']}")
        d = r['description']
        if d and len(d) > 130:
            d = d[:130] + '...'
        print(f"    description={d}")

for s, group in by_status.items():
    if s not in status_order:
        print(f"\n--- {s} ({len(group)}) ---")
        for r in group:
            print(f"  list_entry_id={r['list_entry_id']} | entity_id={r['entity_id']} | name={r['name']} | created_at={r['created_at']}")
            print(f"    owners={r['owners']}")
            print(f"    pass_reason_ids={r['pass_reason_ids']}")
            print(f"    founder_linkedin_verified={r['founder_linkedin_verified']}")
            print(f"    affinity_linkedin_founders={r['affinity_linkedin_founders']}")
            print(f"    year_founded={r['year_founded']}")
            d = r['description']
            if d and len(d) > 130:
                d = d[:130] + '...'
            print(f"    description={d}")
