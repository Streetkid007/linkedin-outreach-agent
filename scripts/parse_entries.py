import json, sys

with open(sys.argv[1]) as fh:
    data = json.load(fh)

entries = data['data']
pagination = data['pagination']
print(f"Total count: {pagination['totalCount']}")
print(f"Next cursor: {pagination.get('nextCursor', None)}")
print(f"Entries in this page: {len(entries)}")
print()

for e in entries:
    entity = e.get('entity', {})
    entity_id = entity.get('id', 'N/A')
    entity_name = entity.get('name', 'N/A')
    list_entry_id = e.get('id', 'N/A')

    fields = e.get('fields', [])

    status_val = None
    pass_reason_val = None
    linkedin_verified = None
    linkedin_enriched = None

    for f in fields:
        fid = f.get('id', '')
        val = f.get('value', None)

        if fid == 'field-5086705':
            if val and isinstance(val, list) and len(val) > 0:
                status_val = val[0].get('id', None) if isinstance(val[0], dict) else val[0]
        elif fid == 'field-5086710':
            if val and isinstance(val, list) and len(val) > 0:
                pass_reason_val = val[0].get('id', None) if isinstance(val[0], dict) else val[0]
        elif fid == 'field-5875046':
            linkedin_verified = val
        elif fid == 'affinity-data-linkedin-profile-founders-ceos':
            linkedin_enriched = val

    li_e_str = str(linkedin_enriched)[:100] if linkedin_enriched else None
    print(f"{entity_name} | list_entry={list_entry_id} | entity={entity_id} | status={status_val} | pass_reason={pass_reason_val} | li_verified={linkedin_verified} | li_enriched={li_e_str}")
