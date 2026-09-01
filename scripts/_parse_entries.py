import json, sys
from collections import Counter

src = sys.argv[1] if len(sys.argv) > 1 else "logs/clover_entries_raw.json"
dst = sys.argv[2] if len(sys.argv) > 2 else "logs/clover_entries_run.json"

with open(src) as f:
    raw = json.load(f)

results = []
for entry in raw["data"]:
    fields_by_id = {fld["id"]: fld for fld in entry["entity"]["fields"]}

    def fval(fid):
        return fields_by_id.get(fid, {}).get("value", {}).get("data")

    status_field = fval("field-5086705")
    status_text = status_field.get("text") if isinstance(status_field, dict) else None
    status_id = status_field.get("dropdownOptionId") if isinstance(status_field, dict) else None

    results.append({
        "entry_id": entry["id"],
        "entity_id": entry["entity"]["id"],
        "name": entry["entity"]["name"],
        "domain": entry["entity"].get("domain"),
        "status": status_text,
        "status_id": status_id,
        "pass_reason": fval("field-5086710"),
        "linkedin_verified": fval("field-5875046"),
        "linkedin_enriched": fval("affinity-data-linkedin-profile-founders-ceos"),
        "description": fval("affinity-data-description"),
        "year_founded": fval("affinity-data-year-founded"),
        "industry": fval("field-5685231"),
        "location": fval("field-5685235"),
    })

print(f"Total entries: {len(results)}")
print(f"Next cursor:   {raw['pagination'].get('nextCursor')}")
print(f"Total count:   {raw['pagination'].get('totalCount')}")
print()

status_counts = Counter(r["status"] for r in results)
for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
    print(f"  {status or 'None'}: {count}")

with open(dst, "w") as out:
    json.dump(results, out)
print(f"\nSaved to {dst}")
