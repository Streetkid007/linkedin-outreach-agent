const fs = require('fs');
const raw = fs.readFileSync('/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/bb41346b-5d05-46b1-b3f4-8bd0f29930c0/tool-results/toolu_01NFuNEeuJ5N2W85fecVtb9g.json', 'utf8');
const outer = JSON.parse(raw);
const text = outer[0].text;
const match = text.match(/```json\s*(\[[\s\S]*?\])\s*```/);
if (match) {
  const entries = JSON.parse(match[1]);
  fs.writeFileSync('/Users/julietta/Documents/CloverAgent/clover-outreach-agent/affinity_entries_extracted.json', JSON.stringify(entries, null, 2));
  console.log('OK: ' + entries.length + ' entries');
  const tcMatch = text.match(/totalCount[^:]*:\s*`?(\d[\d,]+)`?/);
  const ncMatch = text.match(/nextCursor[^:]*:\s*`?([A-Za-z0-9+/=]+)`?/);
  console.log('TC: ' + (tcMatch ? tcMatch[1] : 'not found'));
  console.log('NC: ' + (ncMatch ? ncMatch[1] : 'not found'));
  // Status breakdown
  const byStatus = {};
  entries.forEach(e => {
    if (!byStatus[e.status_name]) byStatus[e.status_name] = 0;
    byStatus[e.status_name]++;
  });
  Object.keys(byStatus).sort().forEach(s => console.log(s + ': ' + byStatus[s]));
} else {
  console.log('NOMATCH len=' + text.length);
  console.log(text.substring(0, 300));
}
