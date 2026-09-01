import json
import sys
from collections import defaultdict

FILE = '/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/68a36199-7b90-4434-9d48-8f1ca3402016/tool-results/mcp-claude_ai_Affinity-search_list_entries-1788172894313.txt'

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

with open(FILE, 'r') as f:
    data = json.load(f)

pagination = data.get('pagination', {})
entries = data.get('data', [])

print(f"=== PAGINATION ===")
print(f"totalCount: {pagination.get('totalCount')}")
print(f"nextCursor: {pagination.get('nextCursor')}")
print(f"prevUrl: {pagination.get('prevUrl')}")
print(f"nextUrl: {pagination.get('nextUrl')}")
print(f"Entries in this page: {len(entries)}")
print()

def get_field_value(fields, field_id):
    for f in fields:
        if f.get('id') == field_id:
            return f.get('value')
    return None

def extract_status(fields):
    val = get_field_value(fields, 'field-5086705')
    if not val:
        return None, None
    d = val.get('data')
    if not d:
        return None, None
    if isinstance(d, list):
        opt_id = d[0].get('dropdownOptionId') if d else None
    elif isinstance(d, dict):
        opt_id = d.get('dropdownOptionId')
    else:
        return None, None
    return opt_id, STATUS_MAP.get(opt_id, f'Unknown({opt_id})')

def extract_pass_reason(fields):
    val = get_field_value(fields, 'field-5086710')
    if not val:
        return []
    d = val.get('data')
    if not d:
        return []
    if isinstance(d, list):
        return [item.get('dropdownOptionId') for item in d if item]
    elif isinstance(d, dict):
        return [d.get('dropdownOptionId')]
    return []

def extract_owners(fields):
    val = get_field_value(fields, 'field-5086706')
    if not val:
        return []
    d = val.get('data')
    if not d:
        return []
    owners = []
    items = d if isinstance(d, list) else [d]
    for p in items:
        if isinstance(p, dict):
            fn = p.get('firstName', '') or ''
            ln = p.get('lastName', '') or ''
            name = f"{fn} {ln}".strip()
            if name:
                owners.append(name)
    return owners

def extract_url_field(fields, field_id):
    val = get_field_value(fields, field_id)
    if not val:
        return None
    d = val.get('data')
    if not d:
        return None
    if isinstance(d, str):
        return d
    if isinstance(d, dict):
        return d.get('url') or d.get('text') or None
    if isinstance(d, list) and d:
        item = d[0]
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            return item.get('url') or item.get('text') or None
    return None

def extract_text_field(fields, field_id):
    val = get_field_value(fields, field_id)
    if not val:
        return None
    d = val.get('data')
    if d is None:
        return None
    if isinstance(d, str):
        return d
    if isinstance(d, (int, float)):
        return d
    if isinstance(d, dict):
        return d.get('text') or d.get('data') or None
    return None

def extract_number_field(fields, field_id):
    val = get_field_value(fields, field_id)
    if not val:
        return None
    return val.get('data')

results = []

for entry in entries:
    entry_id = entry.get('id')
    created_at = entry.get('createdAt')
    entity = entry.get('entity', {})
    company_name = entity.get('name')
    entity_id = entity.get('id')

    entity_fields = entity.get('fields', [])
    entry_fields = entry.get('fields', [])

    status_id, status_name = extract_status(entry_fields)
    pass_reasons = extract_pass_reason(entry_fields)
    owners = extract_owners(entry_fields)

    founder_linkedin_verified = extract_url_field(entity_fields, 'field-5875046')
    affinity_linkedin_founders = extract_url_field(entity_fields, 'affinity-data-linkedin-profile-founders-ceos')
    description = extract_text_field(entity_fields, 'affinity-data-description')
    year_founded = extract_number_field(entity_fields, 'affinity-data-year-founded')

    results.append({
        'id': entry_id,
        'company_name': company_name,
        'entity_id': entity_id,
        'created_at': created_at,
        'status_id': status_id,
        'status_name': status_name,
        'pass_reasons': pass_reasons,
        'owners': owners,
        'founder_linkedin_verified': founder_linkedin_verified,
        'affinity_linkedin_founders': affinity_linkedin_founders,
        'description': description,
        'year_founded': year_founded,
    })

by_status = defaultdict(list)
for r in results:
    key = r['status_name'] if r['status_name'] else 'None/Unknown'
    by_status[key].append(r)

status_order = ['New', 'Invite Sent', 'Connected', 'Pending Approval', 'Approved', 'Reached Out', 'Follow Up Sent', 'Passed', 'Out of Scope', 'None/Unknown']

print(f"=== SUMMARY ===")
print(f"Total entries parsed: {len(results)}")
for s in status_order:
    g = by_status.get(s, [])
    if g:
        print(f"  {s}: {len(g)}")
print()

print(f"=== ENTRIES BY STATUS ===")

for status in status_order:
    group = by_status.get(status, [])
    if not group:
        continue
    print(f"\n--- {status} ({len(group)}) ---")
    for r in group:
        print(f"  ID={r['id']} | entity_id={r['entity_id']} | name={r['company_name']} | created={r['created_at']}")
        print(f"    owners={r['owners']} | pass_reasons={r['pass_reasons']}")
        print(f"    founder_linkedin_verified={r['founder_linkedin_verified']}")
        print(f"    affinity_linkedin_founders={r['affinity_linkedin_founders']}")
        print(f"    year_founded={r['year_founded']}")
        desc = r['description']
        if desc and len(str(desc)) > 150:
            desc = str(desc)[:150] + '...'
        print(f"    description={desc}")

# Check for any statuses not in order
for status, group in by_status.items():
    if status not in status_order:
        print(f"\n--- {status} ({len(group)}) ---")
        for r in group:
            print(f"  ID={r['id']} | entity_id={r['entity_id']} | name={r['company_name']} | created={r['created_at']}")
            print(f"    owners={r['owners']} | pass_reasons={r['pass_reasons']}")
            print(f"    founder_linkedin_verified={r['founder_linkedin_verified']}")
            print(f"    affinity_linkedin_founders={r['affinity_linkedin_founders']}")
            print(f"    year_founded={r['year_founded']}")
            desc = r['description']
            if desc and len(str(desc)) > 150:
                desc = str(desc)[:150] + '...'
            print(f"    description={desc}")
