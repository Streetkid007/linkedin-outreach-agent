"""Extracts key outreach fields from a search_list_entries JSON file."""
import json
import sys

file_path = sys.argv[1]

with open(file_path) as f:
    data = json.load(f)

print(f"Total count: {data['pagination']['totalCount']}")
print(f"Entries in this page: {len(data['data'])}")
print(f"Has more: {data['pagination'].get('nextCursor') is not None}")
print()

results = []
for entry in data['data']:
    eid = entry['entity']['id']
    ename = entry['entity']['name']
    list_entry_id = entry['id']
    created_at = entry.get('createdAt', '')

    fields_by_id = {f['id']: f for f in entry['entity']['fields']}

    # Status
    status_f = fields_by_id.get('field-5086705', {})
    status_val = (status_f.get('value') or {}).get('data')
    status_id = status_val.get('dropdownOptionId') if isinstance(status_val, dict) else None

    # Owners
    owners_f = fields_by_id.get('field-5086706', {})
    owners_data = (owners_f.get('value') or {}).get('data') or []
    owners = [o.get('firstName', '') + ' ' + o.get('lastName', '') for o in owners_data]

    # Founder LinkedIn Verified
    li_verified_f = fields_by_id.get('field-5875046', {})
    li_verified = (li_verified_f.get('value') or {}).get('data')

    # Enriched Founder LinkedIn
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

    # Description
    desc_f = fields_by_id.get('affinity-data-description', {})
    desc = (desc_f.get('value') or {}).get('data') or ''
    desc = str(desc)[:200] if desc else ''

    # Location
    loc_f = fields_by_id.get('affinity-data-location', {})
    loc_val = (loc_f.get('value') or {}).get('data')
    loc = ''
    if isinstance(loc_val, dict):
        parts = [loc_val.get('city'), loc_val.get('state'), loc_val.get('country')]
        loc = ', '.join(p for p in parts if p)

    # Industry
    ind_f = fields_by_id.get('affinity-data-industry', {})
    ind_data = (ind_f.get('value') or {}).get('data') or []
    industry = ', '.join(ind_data) if ind_data else ''

    # Dealroom description (fallback)
    dr_desc_f = fields_by_id.get('dealroom-description', {})
    dr_desc = (dr_desc_f.get('value') or {}).get('data') or ''

    results.append({
        'list_entry_id': list_entry_id,
        'entity_id': eid,
        'name': ename,
        'created_at': created_at,
        'status_id': status_id,
        'owners': owners,
        'li_verified': li_verified,
        'li_enriched': li_enriched,
        'desc': desc or dr_desc[:200],
        'location': loc,
        'industry': industry,
    })

print(json.dumps(results, indent=2))
