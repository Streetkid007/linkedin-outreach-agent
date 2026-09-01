import json

filepath = "/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/be986fb9-1986-4b10-9094-a769214073ce/tool-results/mcp-claude_ai_Affinity-search_list_entries-1787175536921.txt"

with open(filepath, 'r') as f:
    raw = f.read()

data = json.loads(raw)

pagination = data.get('pagination', {})
total_count = pagination.get('totalCount')
next_cursor = pagination.get('nextCursor')

entries = data.get('data', [])

print("=== PAGINATION ===")
print("totalCount:", total_count)
print("nextCursor:", next_cursor)
print("Entries in this page:", len(entries))
print()

for i, entry in enumerate(entries):
    list_entry_id = entry.get('id')
    created_at = entry.get('createdAt')
    entity = entry.get('entity', {})
    entity_id = entity.get('id')
    company_name = entity.get('name')
    domain = entity.get('domain')

    fields = entry.get('fields', [])

    def get_field(field_id):
        for f in fields:
            if f.get('id') == field_id:
                return f
        return None

    f_verified = get_field('field-5875046')
    founder_linkedin_verified = None
    if f_verified:
        founder_linkedin_verified = f_verified.get('value')

    f_enriched = get_field('affinity-data-linkedin-profile-founders-ceos')
    founder_linkedin_enriched = None
    if f_enriched:
        val = f_enriched.get('value')
        if isinstance(val, list):
            links = []
            for item in val:
                if isinstance(item, dict):
                    link = item.get('link') or item.get('url') or item.get('text') or item.get('filterable-text') or str(item)
                    links.append(link)
                else:
                    links.append(str(item))
            founder_linkedin_enriched = links if links else None
        elif val is not None:
            founder_linkedin_enriched = val

    f_desc = get_field('affinity-data-description')
    company_description = None
    if f_desc:
        company_description = f_desc.get('value')

    f_year = get_field('affinity-data-year-founded')
    year_founded = None
    if f_year:
        year_founded = f_year.get('value')

    f_industry = get_field('field-5685231')
    industry_clover = None
    if f_industry:
        industry_clover = f_industry.get('value')

    f_location = get_field('field-5685235')
    location_clover = None
    if f_location:
        location_clover = f_location.get('value')

    f_linkedin = get_field('affinity-data-linkedin-url')
    company_linkedin_url = None
    if f_linkedin:
        company_linkedin_url = f_linkedin.get('value')

    print("--- Entry", i+1, "---")
    print("list_entry_id:", list_entry_id)
    print("entity_id:", entity_id)
    print("company_name:", company_name)
    print("domain:", domain)
    print("createdAt:", created_at)
    print("founder_linkedin_verified:", founder_linkedin_verified)
    print("founder_linkedin_enriched:", founder_linkedin_enriched)
    print("company_description:", company_description)
    print("year_founded:", year_founded)
    print("industry_clover:", industry_clover)
    print("location_clover:", location_clover)
    print("company_linkedin_url:", company_linkedin_url)
    print()
