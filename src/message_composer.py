"""
Judgment step two: draft the outreach message once a connection is
accepted, and the two later stages the outreach playbook actually requires,
follow up and reply handling, which are separate judgments from the first
draft, not the same prompt reused.

Source of truth for template content is the Google Doc
(id 1Yy4n3wP8U8vUwqrAulkwueaf7p-rjUrEgbuNp_KBrTU), pulled at build or run
time via mcp__Google_Drive__read_file_content rather than copied here, so
edits in the Doc are what future drafts actually use. See
docs/source_outreach_playbook.md for the categories and structure.

profile_category comes from thesis_check.py's output: stealth,
active_company, high_profile, or warm_intro. warm_intro is intentionally
NOT drafted here, see route_warm_intro below, pending confirmation with
Juliette that referred founders should go to her directly instead.
"""

STYLE_LOG_PATH = "docs/style_feedback_log.md"

FIRST_MESSAGE_PROMPT_TEMPLATE = """
Draft a first LinkedIn message from {sender_name} at Clover to a founder
whose connection request was just accepted.

Profile category: {profile_category}. Language: {language}.
Use the matching template for this category and language from the outreach
playbook below as the base, filling placeholders with real specifics from
the company data, never leaving a placeholder generic or vague. For
high_profile specifically, every observation must be concrete, no version
of "I heard great things."

Outreach playbook (source of truth, pulled live from the Google Doc):
{playbook_text}

Style notes from Juliette's past feedback, most recent first, weigh recent
corrections more heavily than older ones:
{style_log}

Rules: no hyphens or long dashes anywhere in the message. Never call the
founder "exceptional." {check_size_note}

Regardless of whatever sign-off the playbook template above shows, end the
message with exactly "Cheers, {sender_name}" as its own final line,
replacing that template's sign-off. This message may go out from either
Juliette's or Hugo's LinkedIn account depending on who owns this company,
so the sign-off must always match the actual sender, never whichever name
happens to be baked into the playbook doc.

Company and founder data:
{company_data}
"""

FOLLOW_UP_PROMPT_TEMPLATE = """
Draft the one week follow up for a founder who has not replied to the first
outreach message.

Profile category: {profile_category}. Language: {language}.

If profile_category is high_profile, do not use a generic calendar nudge.
Research and include one fresh, specific data point that has appeared since
the first message (fundraise, launch, press coverage, a notable hire).
Otherwise use the simple nudge template from the playbook below.

Outreach playbook:
{playbook_text}

Original message sent, for continuity and to avoid repeating the same
observation:
{original_message}

Regardless of whatever sign-off the playbook template above shows, end the
message with exactly "Cheers, {sender_name}" as its own final line, the
same rule as the first message: it must match whoever's LinkedIn account
actually owns this thread, not whichever name the playbook doc happens to
show.
"""

REPLY_HANDLING_PROMPT_TEMPLATE = """
A founder replied to Clover's outreach. Before drafting a response, judge
thesis fit fresh from what they actually describe in their reply, since a
reply can reveal a company is not a fit even after clearing the first
automated check.

Their reply:
{founder_reply}

Original company data and first pass thesis verdict, for context only, do
not defer to it if the reply contradicts it:
{original_verdict}

If in scope: use the "if thesis fit yes" template for this profile category
from the playbook, sending the booking link and asking for materials to be
shared to {sender_email}.
If not in scope: use the specific pass template, not a generic decline.

Outreach playbook:
{playbook_text}

Regardless of whatever sign-off the playbook template above shows, end the
message with exactly "Cheers, {sender_name}" as its own final line, the
same rule as the first message and follow up: it must match whoever's
LinkedIn account actually owns this thread, not whichever name the
playbook doc happens to show.
"""


def route_warm_intro(company_data):
    """
    Warm intro or referred founders are not drafted automatically pending
    Juliette's confirmation. This just flags the case clearly rather than
    silently sending nothing.
    """
    return {
        "action": "route_to_juliette",
        "reason": "Warm intro case, playbook template exists but getting "
                  "the mutual or context wrong costs more than automating "
                  "this saves. Confirm before wiring this path.",
    }


def build_first_message_prompt(company_data, profile_category, language,
                                playbook_text, style_log, sender_name,
                                check_size_note=None):
    if profile_category == "warm_intro":
        raise ValueError(
            "warm_intro should be routed via route_warm_intro(), not "
            "drafted through this function, until confirmed otherwise."
        )
    return FIRST_MESSAGE_PROMPT_TEMPLATE.format(
        sender_name=sender_name,
        profile_category=profile_category,
        language=language,
        playbook_text=playbook_text,
        style_log=style_log or "None yet, this is the first draft.",
        check_size_note=check_size_note or (
            "If a check size figure is needed, use 100 to 200k euros, "
            "confirmed current by Juliette on 2026-08-13. Only state it if "
            "the matching template calls for it, do not add it where the "
            "template does not mention a number."
        ),
        company_data=company_data,
    )


def build_follow_up_prompt(profile_category, language, playbook_text,
                            original_message, sender_name):
    return FOLLOW_UP_PROMPT_TEMPLATE.format(
        profile_category=profile_category,
        language=language,
        playbook_text=playbook_text,
        original_message=original_message,
        sender_name=sender_name,
    )


def build_reply_handling_prompt(founder_reply, original_verdict,
                                 playbook_text, sender_email, sender_name):
    return REPLY_HANDLING_PROMPT_TEMPLATE.format(
        founder_reply=founder_reply,
        original_verdict=original_verdict,
        playbook_text=playbook_text,
        sender_email=sender_email,
        sender_name=sender_name,
    )


def append_feedback(decision, original_draft, edited_or_reason):
    """
    Called after Juliette's decision is read from the Affinity note.
    Appends a dated entry to STYLE_LOG_PATH so the next draft, for anyone,
    benefits from it.
    """
    raise NotImplementedError(
        "Append a timestamped entry to STYLE_LOG_PATH: decision, what was "
        "drafted, and what Juliette actually wanted instead or why it "
        "worked as is."
    )
