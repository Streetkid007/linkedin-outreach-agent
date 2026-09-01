"""
Field and option ids for the Clover Deal Pipeline (Affinity list 296071),
pulled live from the list on 2026-08-13. Keeping these as named constants
instead of magic strings scattered through the codebase, since Affinity
field ids are opaque and easy to typo.
"""

LIST_ID = 296071  # Clover Deal Pipeline

# --- Status field (ranked-dropdown) ---
#
# Updated 2026-08-19: superseding the 2026-08-17 decision below. A token
# usage audit found the same ~109 companies having their Affinity notes
# re-read ~9 times a day, because "has Juliette decided yet" could only be
# answered by fetching and text-matching a note, for every company still
# pending, every single poll cycle. STATUS_PENDING_APPROVAL and
# STATUS_APPROVED already existed on the live field (created during the
# 2026-08-17 pass below, then never wired into code) and are now used for
# real: Status becomes the only thing the orchestrator checks to decide
# what to do, and it comes back for every company in one search_list_entries
# call, at no extra cost per company. Notes stay purely as the content
# surface, read once per company, only at the moment Status flips to
# Approved. See prompts/orchestrator.md, Stages 3-6, and docs/ARCHITECTURE.md,
# "Why state lives in Affinity, not a separate database."
#
# STATUS_CONNECTED narrows back to its plain meaning (invite accepted,
# message not yet drafted) now that Pending Approval is a real status
# instead of a second meaning bolted onto Connected.
#
# STATUS_PASSED is used only for a rejection at the Pending Approval stage
# (Juliette saw the drafted message and said no), deliberately kept
# distinct from STATUS_OUT_OF_SCOPE (Stage 1 thesis reject, unchanged) per
# Juliette's own call: these are different kinds of "no" and worth
# reporting on separately.
#
# --- Superseded 2026-08-17 note, kept for the history ---
# "Connected is repurposed rather than adding a fifth status: it covers
# the whole span from invite accepted through message drafted, until
# Juliette approves it, matching the Pending Approval concept discussed in
# chat but under the label she actually created." That decision is what
# created STATUS_PENDING_APPROVAL / STATUS_APPROVED as live dropdown
# options in Affinity without ever having code reference them; both are
# now wired up below instead of staying dead options.
FIELD_STATUS = "field-5086705"
STATUS_NEW = 19399924
STATUS_INVITE_SENT = 25636245
STATUS_CONNECTED = 25636246  # accepted, not yet drafted
STATUS_PENDING_APPROVAL = 25653157  # drafted, awaiting Juliette's decision
STATUS_APPROVED = 25653158  # Juliette approved; agent has not sent yet
STATUS_REACHED_OUT = 19399925  # message actually sent
STATUS_FOLLOW_UP_SENT = 25636247
STATUS_PASSED = 19719669  # rejected at Pending Approval, stop permanently
STATUS_OUT_OF_SCOPE = 19399931  # rejected at Stage 1 thesis check

# --- Pass Reason field (dropdown-multi) ---
FIELD_PASS_REASON = "field-5086710"
PASS_REASON_OUT_OF_SCOPE = 19399922

# --- Existing enrichment fields worth reading before doing any web research ---
FIELD_LINKEDIN_URL_COMPANY = "affinity-data-linkedin-url"
FIELD_LINKEDIN_URL_FOUNDERS = "affinity-data-linkedin-profile-founders-ceos"
FIELD_DESCRIPTION = "affinity-data-description"
FIELD_YEAR_FOUNDED = "affinity-data-year-founded"
FIELD_INDUSTRY_CLOVER = "field-5685231"  # "Industry (Clover added)"
FIELD_LOCATION_CLOVER = "field-5685235"  # "Location (Clover added)"

# --- Verified LinkedIn field, created 2026-08-17 ---
# Deliberately NOT the same field Affinity's own enrichment populates
# (affinity-data-linkedin-profile-founders-ceos above). enrichment_source is
# "none" on this one, confirmed at creation, so Affinity's own enrichment
# pipeline will never silently overwrite it. Written directly by the
# whatsapp-to-affinity skill at intake (verified lookup, not Affinity's bulk
# match) and read first, before the enriched field, by get_founder_linkedin_url.
FIELD_FOUNDER_LINKEDIN_VERIFIED = "field-5875046"

# --- SUPERSEDED, kept only as a record of the decision ---
# An earlier plan was a separate Outreach Stage field for these same
# substates. Juliette preferred folding them into the existing fund-wide
# Status field instead (see the FIELD_STATUS block above, updated
# 2026-08-17 with Invite Sent / Connected / Follow Up Sent). Nothing in
# this codebase should read or write FIELD_OUTREACH_STAGE; it is None on
# purpose and staying that way.
FIELD_OUTREACH_STAGE = None
