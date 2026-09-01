const fs = require('fs');

const filepath = "/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/c3186315-6983-47d1-b276-ef9b8fc82ed6/tool-results/mcp-claude_ai_Affinity-search_list_entries-1787924304666.txt";

const raw = fs.readFileSync(filepath, 'utf8');
const data = JSON.parse(raw);

const pagination = data.pagination || {};
console.log("PAGINATION:");
console.log("  totalCount:", pagination.totalCount);
console.log("  nextCursor:", pagination.nextCursor);

const entries = data.data || [];
console.log("  entry count:", entries.length);

function getField(fieldValues, fieldId) {
    if (!Array.isArray(fieldValues)) return null;
    const fv = fieldValues.find(f => f.fieldId === fieldId);
    return fv ? fv.value : null;
}

const results = [];

for (const entry of entries) {
    const entry_id = entry.id;
    const entity = entry.entity || {};
    const entity_id = entity.id;
    const entity_name = entity.name;

    const fieldValues = entry.fieldValues || [];

    // Status field-5086705 (dropdown)
    const statusVal = getField(fieldValues, 'field-5086705');
    let status = null;
    if (Array.isArray(statusVal) && statusVal.length > 0) {
        status = statusVal[0].dropdownOptionId || null;
    }

    // Pass Reason field-5086710 (dropdown multi)
    const passReasonVal = getField(fieldValues, 'field-5086710');
    let pass_reason = null;
    if (Array.isArray(passReasonVal) && passReasonVal.length > 0) {
        pass_reason = passReasonVal.map(item => item.dropdownOptionId).filter(Boolean);
        if (pass_reason.length === 0) pass_reason = null;
    }

    // Owners field-5086706 (person-multi)
    const ownersVal = getField(fieldValues, 'field-5086706');
    let owners = [];
    if (Array.isArray(ownersVal)) {
        for (const person of ownersVal) {
            const name = person.name;
            const first = person.firstName || '';
            const last = person.lastName || '';
            if (name) {
                owners.push(name);
            } else if (first || last) {
                owners.push(`${first} ${last}`.trim());
            }
        }
    }

    // Founder LinkedIn verified field-5875046
    const flv = getField(fieldValues, 'field-5875046');
    const founder_linkedin_verified = typeof flv === 'string' ? flv : null;

    // Founder LinkedIn enriched
    const fleVal = getField(fieldValues, 'affinity-data-linkedin-profile-founders-ceos');
    let founder_linkedin_enriched = null;
    if (Array.isArray(fleVal) && fleVal.length > 0) {
        founder_linkedin_enriched = fleVal.map(item => item.link).filter(Boolean);
        if (founder_linkedin_enriched.length === 0) founder_linkedin_enriched = null;
    }

    // Description
    const descVal = getField(fieldValues, 'affinity-data-description');
    const description = typeof descVal === 'string' ? descVal.substring(0, 300) : null;

    // Location
    let locVal = getField(fieldValues, 'affinity-data-location') || getField(fieldValues, 'field-5685235');
    let location = null;
    if (Array.isArray(locVal) && locVal.length > 0) {
        const first = locVal[0];
        location = (typeof first === 'object') ? (first.text || first.value || JSON.stringify(first)) : String(first);
    } else if (typeof locVal === 'string') {
        location = locVal;
    }

    // Industry
    let indVal = getField(fieldValues, 'affinity-data-industry') || getField(fieldValues, 'field-5685231');
    let industry = null;
    if (Array.isArray(indVal)) {
        industry = indVal.map(item => (typeof item === 'object') ? (item.text || item.value || JSON.stringify(item)) : String(item));
    } else if (typeof indVal === 'string') {
        industry = indVal;
    }

    // Investment stage
    let invStage = getField(fieldValues, 'affinity-data-investment-stage');
    let investment_stage = null;
    if (Array.isArray(invStage) && invStage.length > 0) {
        const first = invStage[0];
        investment_stage = (typeof first === 'object') ? (first.text || first.value || JSON.stringify(first)) : String(first);
    } else if (typeof invStage === 'string') {
        investment_stage = invStage;
    }

    // Year founded
    const yf = getField(fieldValues, 'affinity-data-year-founded');
    const year_founded = yf !== null && yf !== undefined ? yf : null;

    results.push({
        id: entry_id,
        entity_id,
        entity_name,
        status,
        pass_reason: pass_reason || null,
        owners,
        founder_linkedin_verified,
        founder_linkedin_enriched,
        description,
        location,
        industry,
        investment_stage,
        year_founded
    });
}

console.log("\n=== RESULTS ===");
console.log(JSON.stringify(results, null, 2));
