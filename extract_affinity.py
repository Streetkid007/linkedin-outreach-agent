import json, sys

filepath = "/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/46bc5254-efc1-440a-92a0-421717c493f9/tool-results/mcp-claude_ai_Affinity-search_list_entries-1786983044751.txt"

with open(filepath, 'r') as f:
    raw = f.read()

data = json.loads(raw)

# Determine entries list
if isinstance(data, list):
    entries = data
elif isinstance(data, dict):
    # Try common keys
    entries = data.get('data') or data.get('list_entries') or data.get('entries') or []
    if not entries:
        # find first list value
        for v in data.values():
            if isinstance(v, list):
                entries = v
                break

print(f"Total entries: {len(entries)}", file=sys.stderr)

# Show structure of first entry
if entries:
    e = entries[0]
    print(f"First entry keys: {list(e.keys())}", file=sys.stderr)
    # Look at field_values
    fv = e.get('field_values') or e.get('fields') or {}
    print(f"Field value keys (first 20): {list(fv.keys())[:20]}", file=sys.stderr)

results = []
for e in entries:
    list_entry_id = e.get('id')
    entity_id = None
    company_name = None

    # entity info
    entity = e.get('entity') or e.get('company') or {}
    if isinstance(entity, dict):
        entity_id = entity.get('id')
        company_name = entity.get('name')

    # field_values
    fv = e.get('field_values') or e.get('fields') or {}

    def get_fv(key):
        val = fv.get(key)
        if val is None:
            return None
        # Could be a list or dict
        if isinstance(val, list):
            if len(val) == 0:
                return None
            if len(val) == 1:
                item = val[0]
                if isinstance(item, dict):
                    return item.get('dropdown_option_id') or item.get('value') or item.get('text') or item
                return item
            # multiple
            out = []
            for item in val:
                if isinstance(item, dict):
                    out.append(item.get('dropdown_option_id') or item.get('value') or item.get('text') or item)
                else:
                    out.append(item)
            return out
        if isinstance(val, dict):
            return val.get('dropdown_option_id') or val.get('value') or val.get('text') or val
        return val

    # Status field-5086705
    status = get_fv('field-5086705')
    # Pass Reason field-5086710
    pass_reason = get_fv('field-5086710')
    # Founder LinkedIn Verified field-5875046
    founder_li_verified = get_fv('field-5875046')
    # Enriched founders LinkedIn
    enriched_founders_li = get_fv('affinity-data-linkedin-profile-founders-ceos')
    # Company description
    description = get_fv('affinity-data-description')
    # Year founded
    year_founded = get_fv('affinity-data-year-founded')
    # Industry Clover added field-5685231
    industry = get_fv('field-5685231')
    # Location Clover added field-5685235
    location = get_fv('field-5685235')
    # Company LinkedIn URL
    company_li = get_fv('affinity-data-linkedin-url')

    created_at = e.get('created_at')
    updated_at = e.get('updated_at')

    results.append({
        "list_entry_id": list_entry_id,
        "entity_id": entity_id,
        "company_name": company_name,
        "status_field_5086705": status,
        "pass_reason_field_5086710": pass_reason,
        "founder_linkedin_verified_field_5875046": founder_li_verified,
        "affinity_data_linkedin_profile_founders_ceos": enriched_founders_li,
        "affinity_data_description": description,
        "affinity_data_year_founded": year_founded,
        "industry_clover_field_5685231": industry,
        "location_clover_field_5685235": location,
        "affinity_data_linkedin_url": company_li,
        "created_at": created_at,
        "updated_at": updated_at,
    })

print(json.dumps(results, indent=2))
