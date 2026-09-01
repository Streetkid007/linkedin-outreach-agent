const fs = require('fs');

const FILE = '/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/68a36199-7b90-4434-9d48-8f1ca3402016/tool-results/mcp-claude_ai_Affinity-search_list_entries-1788172894313.txt';
const OUT = '/Users/julietta/Documents/CloverAgent/clover-outreach-agent/affinity_entries_parsed.json';

const STATUS_MAP = {
  19399924: 'New',
  25636245: 'Invite Sent',
  25636246: 'Connected',
  25653157: 'Pending Approval',
  25653158: 'Approved',
  19399925: 'Reached Out',
  25636247: 'Follow Up Sent',
  19719669: 'Passed',
  19399931: 'Out of Scope',
};

const data = JSON.parse(fs.readFileSync(FILE, 'utf8'));
const pagination = data.pagination || {};
const entries = data.data || [];

console.log('=== PAGINATION ===');
console.log('totalCount:', pagination.totalCount);
console.log('nextCursor:', pagination.nextCursor);
console.log('prevUrl:', pagination.prevUrl);
console.log('nextUrl:', pagination.nextUrl);
console.log('Entries in page:', entries.length);
console.log();

function getField(fields, fieldId) {
  if (!Array.isArray(fields)) return null;
  const f = fields.find(f => f.id === fieldId);
  return f ? f.value : null;
}

function extractDropdownId(val) {
  if (!val) return null;
  const d = val.data;
  if (!d) return null;
  if (typeof d === 'object' && !Array.isArray(d)) {
    return d.dropdownOptionId || null;
  }
  if (Array.isArray(d) && d.length > 0) {
    return d[0].dropdownOptionId || null;
  }
  return null;
}

function extractDropdownIds(val) {
  if (!val) return [];
  const d = val.data;
  if (!d) return [];
  if (typeof d === 'object' && !Array.isArray(d)) {
    return d.dropdownOptionId ? [d.dropdownOptionId] : [];
  }
  if (Array.isArray(d)) {
    return d.map(x => x.dropdownOptionId).filter(Boolean);
  }
  return [];
}

function extractOwners(val) {
  if (!val) return [];
  const d = val.data;
  if (!d) return [];
  const items = Array.isArray(d) ? d : [d];
  return items.map(o => {
    if (!o || typeof o !== 'object') return null;
    const fn = (o.firstName || '').trim();
    const ln = (o.lastName || '').trim();
    return [fn, ln].filter(Boolean).join(' ') || null;
  }).filter(Boolean);
}

function extractText(val) {
  if (!val) return null;
  const d = val.data;
  if (typeof d === 'string') return d;
  if (typeof d === 'number') return d;
  return null;
}

function extractUrl(val) {
  if (!val) return null;
  const d = val.data;
  if (typeof d === 'string') return d;
  if (Array.isArray(d) && d.length > 0) {
    const item = d[0];
    if (typeof item === 'string') return item;
    if (typeof item === 'object') return item.link || item.url || item.text || null;
  }
  if (d && typeof d === 'object' && !Array.isArray(d)) {
    return d.link || d.url || d.text || null;
  }
  return null;
}

const results = [];

for (const entry of entries) {
  const entity = entry.entity || {};
  const entityFields = entity.fields || [];

  const statusVal = getField(entityFields, 'field-5086705');
  const statusId = extractDropdownId(statusVal);
  const statusName = STATUS_MAP[statusId] || null;

  const passReasonVal = getField(entityFields, 'field-5086710');
  const passReasonIds = extractDropdownIds(passReasonVal);

  const ownersVal = getField(entityFields, 'field-5086706');
  const owners = extractOwners(ownersVal);

  const liVerifiedVal = getField(entityFields, 'field-5875046');
  const founderLinkedInVerified = extractUrl(liVerifiedVal) || extractText(liVerifiedVal);

  const liEnrichedVal = getField(entityFields, 'affinity-data-linkedin-profile-founders-ceos');
  const affinityLinkedInFounders = extractUrl(liEnrichedVal);

  const descVal = getField(entityFields, 'affinity-data-description');
  const description = extractText(descVal);

  const yearVal = getField(entityFields, 'affinity-data-year-founded');
  const yearFounded = yearVal ? yearVal.data : null;

  results.push({
    list_entry_id: entry.id,
    entity_id: entity.id,
    name: entity.name,
    created_at: entry.createdAt || '',
    status_id: statusId,
    status_name: statusName,
    pass_reason_ids: passReasonIds,
    owners,
    founder_linkedin_verified: founderLinkedInVerified,
    affinity_linkedin_founders: affinityLinkedInFounders,
    description: description ? String(description).substring(0, 300) : null,
    year_founded: yearFounded,
  });
}

// Group by status
const byStatus = {};
const STATUS_ORDER = ['New', 'Invite Sent', 'Connected', 'Pending Approval', 'Approved',
  'Reached Out', 'Follow Up Sent', 'Passed', 'Out of Scope', 'None/Unknown'];

for (const r of results) {
  const key = r.status_name || 'None/Unknown';
  if (!byStatus[key]) byStatus[key] = [];
  byStatus[key].push(r);
}

const summary = {};
for (const s of STATUS_ORDER) {
  if (byStatus[s] && byStatus[s].length > 0) summary[s] = byStatus[s].length;
}
for (const [s, g] of Object.entries(byStatus)) {
  if (!STATUS_ORDER.includes(s)) summary[s] = g.length;
}

const output = {
  pagination: {
    totalCount: pagination.totalCount,
    nextCursor: pagination.nextCursor || null,
    prevUrl: pagination.prevUrl || null,
    nextUrl: pagination.nextUrl || null,
  },
  entries_in_page: results.length,
  summary_by_status: summary,
  by_status: byStatus,
  all_entries: results,
};

fs.writeFileSync(OUT, JSON.stringify(output, null, 2));
console.log('Written to', OUT);
console.log();
console.log('Summary by status:');
for (const [s, c] of Object.entries(summary)) {
  console.log(' ', s + ':', c);
}

console.log();
console.log('=== ALL ENTRIES ===');

for (const status of STATUS_ORDER) {
  const group = byStatus[status] || [];
  if (!group.length) continue;
  console.log(`\n--- ${status} (${group.length}) ---`);
  for (const r of group) {
    console.log(`  list_entry_id=${r.list_entry_id} | entity_id=${r.entity_id} | name=${r.name} | created_at=${r.created_at}`);
    console.log(`    owners=${JSON.stringify(r.owners)}`);
    console.log(`    pass_reason_ids=${JSON.stringify(r.pass_reason_ids)}`);
    console.log(`    founder_linkedin_verified=${r.founder_linkedin_verified}`);
    console.log(`    affinity_linkedin_founders=${r.affinity_linkedin_founders}`);
    console.log(`    year_founded=${r.year_founded}`);
    let d = r.description;
    if (d && d.length > 130) d = d.substring(0, 130) + '...';
    console.log(`    description=${d}`);
  }
}

for (const [s, group] of Object.entries(byStatus)) {
  if (STATUS_ORDER.includes(s)) continue;
  console.log(`\n--- ${s} (${group.length}) ---`);
  for (const r of group) {
    console.log(`  list_entry_id=${r.list_entry_id} | entity_id=${r.entity_id} | name=${r.name} | created_at=${r.created_at}`);
    console.log(`    owners=${JSON.stringify(r.owners)}`);
    console.log(`    pass_reason_ids=${JSON.stringify(r.pass_reason_ids)}`);
    console.log(`    founder_linkedin_verified=${r.founder_linkedin_verified}`);
    console.log(`    affinity_linkedin_founders=${r.affinity_linkedin_founders}`);
    console.log(`    year_founded=${r.year_founded}`);
    let d = r.description;
    if (d && d.length > 130) d = d.substring(0, 130) + '...';
    console.log(`    description=${d}`);
  }
}
