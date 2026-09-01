"""
Superseded 2026-08-19: the decision itself is no longer encoded in note
text. Juliette signals approve/reject by changing Status to Approved or
Passed (config/fields.py), read for free off the one list-wide query in
prompts/orchestrator.md's Stage 4, instead of by typing APPROVED/REJECTED
into the note and having every cycle re-fetch and re-parse it for every
company still pending. The note is still where the drafted text lives and
where she edits it, just no longer also the decision signal. This file is
kept as a record of the old approach, not a spec to build against; do not
wire this into anything new.

Reads Juliette's decision back out of the Affinity note the composer wrote,
since the note itself is the approval surface, not a separate channel.

Expected shape in Affinity once she has responded, all in the same note
thread on the company or the founder's person record:

    PENDING APPROVAL
    <drafted message>

    -- her reply, added as a follow up note or an edit --
    APPROVED
    or
    APPROVED, edited:
    <her version>
    or
    REJECTED: <why, in her own words>

Parsing this on a schedule instead of asking her to use a separate tool is
the point: it stays inside Affinity, which she already has open every day.
"""

import re


def parse_decision(note_thread_text):
    """
    Returns a dict: {status: "pending" | "approved" | "rejected",
    final_text: str or None, reason: str or None}

    Kept intentionally simple and pattern based rather than another LLM
    call, since a misread here either sends nothing (safe) or needs her to
    just re annotate the note, versus an LLM misclassification silently
    sending the wrong text.
    """
    if "PENDING APPROVAL" in note_thread_text and "APPROVED" not in note_thread_text \
            and "REJECTED" not in note_thread_text:
        return {"status": "pending", "final_text": None, "reason": None}

    if "REJECTED" in note_thread_text:
        reason_match = re.search(r"REJECTED:?\s*(.*)", note_thread_text, re.DOTALL)
        return {
            "status": "rejected",
            "final_text": None,
            "reason": reason_match.group(1).strip() if reason_match else None,
        }

    if "APPROVED, edited:" in note_thread_text:
        edited_match = re.search(
            r"APPROVED, edited:\s*(.*)", note_thread_text, re.DOTALL
        )
        return {
            "status": "approved",
            "final_text": edited_match.group(1).strip() if edited_match else None,
            "reason": "edited before sending",
        }

    if "APPROVED" in note_thread_text:
        original_match = re.search(
            r"PENDING APPROVAL\s*(.*?)\s*--", note_thread_text, re.DOTALL
        )
        return {
            "status": "approved",
            "final_text": original_match.group(1).strip() if original_match else None,
            "reason": "sent as drafted",
        }

    return {"status": "pending", "final_text": None, "reason": None}
