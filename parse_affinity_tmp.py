import json

filepath = '/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/55c8d31f-fe51-4ce6-a69a-56909d2ae2fb/tool-results/mcp-claude_ai_Affinity-search_list_entries-1787645787262.txt'

with open(filepath, 'r') as f:
    data = json.load(f)

next_cursor = data.get('nextCursor', 'N/A')
entries = data.get('data', [])

print(f'Total entries: {len(entries)}')
print(f'nextCursor: {next_cursor}')
print()
print('list_entry_id | entity_id | company_name')
print('-' * 80)
for entry in entries:
    list_entry_id = entry.get('id', 'N/A')
    entity = entry.get('entity', {})
    entity_id = entity.get('id', 'N/A')
    company_name = entity.get('name', 'N/A')
    print(f'{list_entry_id} | {entity_id} | {company_name}')
