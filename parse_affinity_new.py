import json

FILE = '/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/dedefab9-8172-4ef5-9a18-5b2bd5659bfc/tool-results/mcp-claude_ai_Affinity-search_list_entries-1787234487429.txt'

with open(FILE) as f:
    data = json.load(f)

pagination = data.get('pagination', {})
total_count = pagination.get('totalCount')
next_cursor = pagination.get('nextCursor')
entries = data.get('data', [])

def get_field(fields, field_id):
    for fld in fields:
        if fld['id'] == field_id:
            return fld['value']
    return None

def extract_dropdown_id(val):
    if val and val.get('data'):
        d = val['data']
        if isinstance(d, dict):
            return d.get('dropdownOptionId')
        if isinstance(d, list):
            return [x.get('dropdownOptionId') for x in d]
    return None

def extract_text(val):
    if val and val.get('data') is not None:
        return val['data']
    return None

def extract_number(val):
    if val and val.get('data') is not None:
        return val['data']
    return None

def extract_filterable_text_multi(val):
    if val and val.get('data'):
        d = val['data']
        if isinstance(d, list):
            urls = []
            for item in d:
                if isinstance(item, dict):
                    link = item.get('link') or item.get('data') or item.get('text')
                    if link:
                        urls.append(link)
            return urls if urls else None
    return None

def extract_industry(val):
    if val and val.get('data'):
        d = val['data']
        if isinstance(d, list):
            return [item.get('text') for item in d if item.get('text')]
    return None

def extract_location(val):
    if val and val.get('data'):
        d = val['data']
        parts = [d.get('city'), d.get('state'), d.get('country')]
        return ', '.join(p for p in parts if p)
    return None

records = []
for e in entries:
    entity = e.get('entity', {})
    fields = entity.get('fields', [])

    status_val = get_field(fields, 'field-5086705')
    pass_reason_val = get_field(fields, 'field-5086710')
    li_verified_val = get_field(fields, 'field-5875046')
    li_founders_val = get_field(fields, 'affinity-data-linkedin-profile-founders-ceos')
    desc_val = get_field(fields, 'affinity-data-description')
    year_val = get_field(fields, 'affinity-data-year-founded')
    industry_val = get_field(fields, 'field-5685231')
    location_val = get_field(fields, 'field-5685235')
    li_company_val = get_field(fields, 'affinity-data-linkedin-url')

    status_id = extract_dropdown_id(status_val)
    pass_reason = extract_dropdown_id(pass_reason_val)
    li_verified = extract_text(li_verified_val)
    li_founders = extract_filterable_text_multi(li_founders_val)
    desc_raw = extract_text(desc_val)
    desc = (desc_raw[:150] + '...') if desc_raw and len(desc_raw) > 150 else desc_raw
    year = extract_number(year_val)
    industry = extract_industry(industry_val)
    location = extract_location(location_val)
    li_company = extract_text(li_company_val)

    has_li = bool(li_verified or li_founders or li_company)

    records.append({
        'list_entry_id': e.get('id'),
        'company_entity_id': entity.get('id'),
        'name': entity.get('name'),
        'status_dropdownOptionId': status_id,
        'pass_reason_dropdownOptionId': pass_reason if pass_reason else 'empty',
        'li_verified': li_verified if li_verified else 'empty',
        'li_founders': li_founders if li_founders else 'empty',
        'li_company': li_company if li_company else 'empty',
        'desc': desc if desc else 'empty',
        'year': year if year else 'empty',
        'industry': industry if industry else 'empty',
        'location': location if location else 'empty',
        'has_li': has_li,
    })

with_li = [r for r in records if r['has_li']]
without_li = [r for r in records if not r['has_li']]

output = {
    'pagination': {
        'totalCount': total_count,
        'nextCursor_present': bool(next_cursor),
        'nextCursor_preview': next_cursor[:80] if next_cursor else None,
    },
    'entries_in_page': len(records),
    'with_linkedin_count': len(with_li),
    'without_linkedin_count': len(without_li),
    'WITH_LINKEDIN': with_li,
    'WITHOUT_LINKEDIN': without_li,
}

OUT = '/Users/julietta/Documents/CloverAgent/clover-outreach-agent/affinity_parsed.json'
with open(OUT, 'w') as out_f:
    json.dump(output, out_f, indent=2)
print('Written to', OUT)
print('totalCount:', total_count)
print('nextCursor present:', bool(next_cursor))
print('Entries in page:', len(records))
print('With LinkedIn:', len(with_li))
print('Without LinkedIn:', len(without_li))
