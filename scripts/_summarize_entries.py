import json, sys

FILE = "/Users/julietta/.claude/projects/-Users-julietta-Documents-CloverAgent-clover-outreach-agent/b55c0f04-0f1e-4837-ba6b-3a6cbe6bc818/tool-results/blbupfjlz.txt"

with open(FILE) as f:
    data = json.load(f)

STATUS_NEW = 19399924
STATUS_INVITE_SENT = 25636245
STATUS_CONNECTED = 25636246
STATUS_PENDING_APPROVAL = 25653157
STATUS_APPROVED = 25653158
STATUS_REACHED_OUT = 19399925
STATUS_FOLLOW_UP_SENT = 25636247
STATUS_PASSED = 19719669
STATUS_OUT_OF_SCOPE = 19399931

status_names = {
    STATUS_NEW: "New",
    STATUS_INVITE_SENT: "Invite Sent",
    STATUS_CONNECTED: "Connected",
    STATUS_PENDING_APPROVAL: "Pending Approval",
    STATUS_APPROVED: "Approved",
    STATUS_REACHED_OUT: "Reached Out",
    STATUS_FOLLOW_UP_SENT: "Follow Up Sent",
    STATUS_PASSED: "Passed",
    STATUS_OUT_OF_SCOPE: "Out of Scope",
    None: "None/Missing"
}

by_status = {}
for item in data:
    s = item["status_id"]
    by_status.setdefault(s, []).append(item)

print("=== SUMMARY BY STATUS ===")
for sid, items in sorted(by_status.items(), key=lambda x: str(x[0])):
    print("  " + status_names.get(sid, str(sid)) + ": " + str(len(items)))

print("\n=== NEW ===")
for item in by_status.get(STATUS_NEW, []):
    li = item["founder_li_verified"] or item["founder_li_enriched"] or "MISSING"
    pr = item["pass_reason"]
    print("  entity=" + str(item["entity_id"]) + " entry=" + str(item["entry_id"]) + " | " + repr(item["entity_name"]) + " | pass_reason=" + str(pr) + " | li=" + repr(li))

print("\n=== CONNECTED ===")
for item in by_status.get(STATUS_CONNECTED, []):
    li = item["founder_li_verified"] or item["founder_li_enriched"] or "MISSING"
    print("  entity=" + str(item["entity_id"]) + " entry=" + str(item["entry_id"]) + " | " + repr(item["entity_name"]) + " | li=" + repr(li))

print("\n=== APPROVED ===")
for item in by_status.get(STATUS_APPROVED, []):
    li = item["founder_li_verified"] or item["founder_li_enriched"] or "MISSING"
    print("  entity=" + str(item["entity_id"]) + " entry=" + str(item["entry_id"]) + " | " + repr(item["entity_name"]) + " | li=" + repr(li))

print("\n=== REACHED OUT (for follow-up check) ===")
for item in by_status.get(STATUS_REACHED_OUT, []):
    print("  entity=" + str(item["entity_id"]) + " entry=" + str(item["entry_id"]) + " | " + repr(item["entity_name"]))

print("\n=== TOTAL entries: " + str(len(data)) + " ===")
