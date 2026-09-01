"""
Reference spec for the Affinity operations this project needs, each one
mapped to a real Affinity MCP tool. As of the 2026-08-17 pivot to running
continuously via local headless Claude Code (docs/RUNNING_LOCALLY.md), the
actual runtime implementation of this logic lives in
prompts/orchestrator.md, executed directly against Claude Code's own bound
Affinity MCP tools, not through this Python class. This file stays as the
precise, testable spec of what each stage needs and why, and as the
starting point if this ever moves to a standalone script calling
Affinity's REST API directly instead of MCP (see ARCHITECTURE.md, "Where
the model boundary sits, and where it bends", for why that has not
happened yet).
"""

from config.fields import (
    LIST_ID,
    FIELD_STATUS,
    STATUS_NEW,
    STATUS_REACHED_OUT,
    STATUS_OUT_OF_SCOPE,
    FIELD_PASS_REASON,
    PASS_REASON_OUT_OF_SCOPE,
    FIELD_LINKEDIN_URL_FOUNDERS,
    FIELD_FOUNDER_LINKEDIN_VERIFIED,
)


class AffinityClient:
    """
    NOTE: the method bodies below are structured as calls into the Affinity
    MCP tools (search_list_entries, upsert_list_entry_field_values,
    create_note, get_notes_for_entity) available in this Cowork session.
    They are left as documented stubs, not live calls, until this runs
    inside the actual scheduled task context where those tools are bound.
    """

    def get_new_unchecked_companies(self):
        """
        Companies at Status = New that have not been through the thesis
        check yet. 'Unchecked' needs one bit of state somewhere; rather
        than a new field, this treats a note containing 'PENDING APPROVAL'
        or 'Routed To Juliette' as 'checked' and anything at New with
        neither as pending. See prompts/orchestrator.md, Stage 1, which is
        the actual current implementation of this logic.
        """
        raise NotImplementedError(
            "Wire to mcp__Affinity__search_list_entries against "
            f"list_id={LIST_ID}, filtering Status == New."
        )

    def get_founder_linkedin_url(self, company_entry):
        """
        Three tier lookup, in this order, per Juliette's own observation
        that Affinity's bulk enrichment sometimes matches the wrong person:

        1. FIELD_FOUNDER_LINKEDIN_VERIFIED. Written by the whatsapp-to-
           affinity skill at intake time from an actual lookup grounded in
           the referral message, not a bulk match. Trust this first.
        2. FIELD_LINKEDIN_URL_FOUNDERS. Affinity's own enrichment. Used
           only if step 1 is empty, e.g. for records created before the
           verified field existed.
        3. Neither present: hold the company at this stage and flag it
           rather than guessing. Juliette can drop the URL into a note
           herself as a last resort.
        """
        raise NotImplementedError(
            f"Try {FIELD_FOUNDER_LINKEDIN_VERIFIED} first, then fall back "
            f"to {FIELD_LINKEDIN_URL_FOUNDERS}, then flag as unresolved."
        )

    def set_status(self, entry_id, status_option_id):
        raise NotImplementedError(
            f"Wire to mcp__Affinity__upsert_list_entry_field_values, "
            f"field={FIELD_STATUS}, value={status_option_id}."
        )

    def mark_out_of_scope(self, entry_id, reason_text):
        """Sets Status to Out of Scope and tags Pass Reason."""
        raise NotImplementedError(
            f"Set {FIELD_STATUS}={STATUS_OUT_OF_SCOPE} and "
            f"{FIELD_PASS_REASON} includes {PASS_REASON_OUT_OF_SCOPE}, "
            f"then log '{reason_text}' as a note for the audit trail."
        )

    def write_pending_note(self, entity_id, draft_text, stage_label):
        """
        Writes the drafted outreach message as a note, then moves Status
        to Pending Approval (config/fields.py: STATUS_PENDING_APPROVAL).
        Juliette edits the note directly in Affinity; the note is still
        where the actual text lives. What changed 2026-08-19: the note is
        no longer also how the agent detects that she has decided. That
        signal is now the Status field itself (Approved / Passed), which
        comes back for every company in one search_list_entries call,
        instead of a get_notes_for_entity call per company per cycle.
        See prompts/orchestrator.md, Stage 3.
        """
        raise NotImplementedError(
            "Wire to mcp__Affinity__create_note with a clear "
            "'PENDING APPROVAL' marker and the stage label in the body, "
            "then mcp__Affinity__upsert_list_entry_field_values to set "
            "Status = STATUS_PENDING_APPROVAL."
        )

    def read_latest_note(self, entity_id):
        """
        Only called once a company's Status is already Approved (Stage 4).
        Never call this just to check whether Juliette has decided yet —
        that is what the Status field is for. Calling this for every
        company still sitting at Pending Approval, every cycle, is exactly
        the pattern that used to make this the single most-called Affinity
        operation in the whole project.
        """
        raise NotImplementedError(
            "Wire to mcp__Affinity__get_notes_for_entity, most recent first."
        )
