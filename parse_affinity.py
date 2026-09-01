import json, sys

filepath = "/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/c3186315-6983-47d1-b276-ef9b8fc82ed6/tool-results/mcp-claude_ai_Affinity-search_list_entries-1787924304666.txt"

with open(filepath, 'r') as f:
    raw = f.read()

data = json.loads(raw)
pagination = data.get('pagination', {})
print("PAGINATION:")
print("  totalCount:", pagination.get('totalCount'))
print("  nextCursor:", pagination.get('nextCursor'))
entries = data.get('data', [])
print("  entry count:", len(entries))

# Helper: get field values from fieldValues list by fieldId
def get_field(field_values, field_id):
    for fv in field_values:
        if fv.get('fieldId') == field_id:
            return fv.get('value')
    return None

results = []

for entry in entries:
    entry_id = entry.get('id')
    entity = entry.get('entity', {})
    entity_id = entity.get('id')
    entity_name = entity.get('name')

    field_values = entry.get('fieldValues', [])

    # Status field-5086705 (dropdown)
    status_val = get_field(field_values, 'field-5086705')
    if status_val and isinstance(status_val, list):
        status = status_val[0].get('dropdownOptionId') if status_val else None
    else:
        status = None

    # Pass Reason field-5086710 (dropdown multi)
    pass_reason_val = get_field(field_values, 'field-5086710')
    if pass_reason_val and isinstance(pass_reason_val, list):
        pass_reason = [item.get('dropdownOptionId') for item in pass_reason_val if item.get('dropdownOptionId')]
    else:
        pass_reason = None

    # Owners field-5086706 (person-multi)
    owners_val = get_field(field_values, 'field-5086706')
    owners = []
    if owners_val and isinstance(owners_val, list):
        for person in owners_val:
            first = person.get('firstName', '')
            last = person.get('lastName', '')
            name = person.get('name', '')
            if name:
                owners.append(name)
            elif first or last:
                owners.append(f"{first} {last}".strip())

    # Founder LinkedIn verified field-5875046
    flv = get_field(field_values, 'field-5875046')
    founder_linkedin_verified = flv if isinstance(flv, str) else None

    # Founder LinkedIn enriched - affinity-data-linkedin-profile-founders-ceos
    fle_val = get_field(field_values, 'affinity-data-linkedin-profile-founders-ceos')
    if fle_val and isinstance(fle_val, list):
        founder_linkedin_enriched = [item.get('link') for item in fle_val if item.get('link')]
    else:
        founder_linkedin_enriched = None

    # Description - affinity-data-description
    desc_val = get_field(field_values, 'affinity-data-description')
    description = desc_val[:300] if isinstance(desc_val, str) else None

    # Location - affinity-data-location or field-5685235
    loc_val = get_field(field_values, 'affinity-data-location') or get_field(field_values, 'field-5685235')
    if isinstance(loc_val, list) and loc_val:
        first_loc = loc_val[0]
        location = first_loc.get('text') or first_loc.get('value') if isinstance(first_loc, dict) else str(first_loc)
    elif isinstance(loc_val, str):
        location = loc_val
    else:
        location = None

    # Industry - affinity-data-industry or field-5685231
    ind_val = get_field(field_values, 'affinity-data-industry') or get_field(field_values, 'field-5685231')
    if isinstance(ind_val, list):
        industry = []
        for item in ind_val:
            if isinstance(item, dict):
                industry.append(item.get('text') or item.get('value') or str(item))
            else:
                industry.append(str(item))
    elif isinstance(ind_val, str):
        industry = ind_val
    else:
        industry = None

    # Investment stage - affinity-data-investment-stage
    inv_stage = get_field(field_values, 'affinity-data-investment-stage')
    if isinstance(inv_stage, list) and inv_stage:
        first_inv = inv_stage[0]
        investment_stage = first_inv.get('text') or first_inv.get('value') if isinstance(first_inv, dict) else str(first_inv)
    elif isinstance(inv_stage, str):
        investment_stage = inv_stage
    else:
        investment_stage = None

    # Year founded - affinity-data-year-founded
    yf = get_field(field_values, 'affinity-data-year-founded')
    year_founded = yf if yf else None

    results.append({
        'id': entry_id,
        'entity_id': entity_id,
        'entity_name': entity_name,
        'status': status,
        'pass_reason': pass_reason if pass_reason else None,
        'owners': owners,
        'founder_linkedin_verified': founder_linkedin_verified,
        'founder_linkedin_enriched': founder_linkedin_enriched,
        'description': description,
        'location': location,
        'industry': industry,
        'investment_stage': investment_stage,
        'year_founded': year_founded,
    })

output = json.dumps(results, indent=2, ensure_ascii=False)
print("\n=== RESULTS ===")
print(output)
