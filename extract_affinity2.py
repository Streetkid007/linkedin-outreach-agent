#!/usr/bin/env python3
import json, sys

filepath = "/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/46bc5254-efc1-440a-92a0-421717c493f9/tool-results/mcp-claude_ai_Affinity-search_list_entries-1786983044751.txt"

with open(filepath, 'r') as f:
    raw = f.read()

root = json.loads(raw)

# Determine entries list
if isinstance(root, list):
    entries = root
elif isinstance(root, dict):
    entries = root.get('data') or root.get('list_entries') or root.get('entries') or []
    if not entries:
        for v in root.values():
            if isinstance(v, list):
                entries = v
                break

print(f"[DEBUG] Total entries: {len(entries)}", file=sys.stderr)
if entries:
    print(f"[DEBUG] First entry keys: {list(entries[0].keys())}", file=sys.stderr)

def extract_field_value(field_data):
    """Extract the most useful value from a field_value structure."""
    if field_data is None:
        return None
    if isinstance(field_data, list):
        if len(field_data) == 0:
            return None
        results = []
        for item in field_data:
            results.append(extract_single_field_value(item))
        if len(results) == 1:
            return results[0]
        return results
    return extract_single_field_value(field_data)

def extract_single_field_value(item):
    if item is None:
        return None
    if isinstance(item, (str, int, float, bool)):
        return item
    if isinstance(item, dict):
        # Try dropdown_option_id first
        if 'dropdown_option_id' in item:
            return item['dropdown_option_id']
        # Then value
        if 'value' in item:
            return item['value']
        # Then text
        if 'text' in item:
            return item['text']
        # Then url
        if 'url' in item:
            return item['url']
        # Otherwise return whole dict
        return item
    return item

results = []
for e in entries:
    entry_id = e.get('id')
    entity = e.get('entity') or {}
    entity_id = entity.get('id') if isinstance(entity, dict) else None
    company_name = entity.get('name') if isinstance(entity, dict) else None

    # field_values is typically a dict keyed by field_id, or a list of objects
    fv_raw = e.get('field_values') or e.get('fields') or {}

    # Build a lookup: field_id -> value(s)
    if isinstance(fv_raw, dict):
        fv = fv_raw
    elif isinstance(fv_raw, list):
        # Each item may have field_id and value
        fv = {}
        for item in fv_raw:
            if isinstance(item, dict):
                fid = item.get('field_id') or item.get('id')
                if fid:
                    if fid in fv:
                        if not isinstance(fv[fid], list):
                            fv[fid] = [fv[fid]]
                        fv[fid].append(item.get('value') or item)
                    else:
                        fv[fid] = item.get('value') or item
    else:
        fv = {}

    def get_field(key):
        val = fv.get(key)
        return extract_field_value(val)

    obj = {
        "list_entry_id": entry_id,
        "entity_id": entity_id,
        "company_name": company_name,
        "status_field_5086705": get_field('field-5086705'),
        "pass_reason_field_5086710": get_field('field-5086710'),
        "founder_linkedin_verified_field_5875046": get_field('field-5875046'),
        "affinity_data_linkedin_profile_founders_ceos": get_field('affinity-data-linkedin-profile-founders-ceos'),
        "affinity_data_description": get_field('affinity-data-description'),
        "affinity_data_year_founded": get_field('affinity-data-year-founded'),
        "industry_clover_field_5685231": get_field('field-5685231'),
        "location_clover_field_5685235": get_field('field-5685235'),
        "affinity_data_linkedin_url": get_field('affinity-data-linkedin-url'),
        "created_at": e.get('created_at'),
        "updated_at": e.get('updated_at'),
    }
    results.append(obj)

print(json.dumps(results, indent=2))
