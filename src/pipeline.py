"""
Original orchestrator design, six stages, still the correct spec for what
each stage does and in what order. As of the 2026-08-17 pivot to running
continuously via local headless Claude Code (docs/RUNNING_LOCALLY.md), the
runtime version of this same logic is prompts/orchestrator.md, run every
poll cycle by scripts/run_forever.sh, not this file. Kept here, unwired,
as the readable reference this project was actually built against; the
stage order, the "never call Unipile directly" rule, and the approval gate
below all still apply exactly as written.

Every step below is a plain function call, not a model call, except the
ones explicitly marked. Kept that way on purpose.

Six stages now, the original four plus the two the outreach playbook
actually requires: follow up and reply handling.
"""

from src.affinity_client import AffinityClient
from src.unipile_client import UnipileClient
from src import thesis_check, message_composer, approval_loop


def run_once():
    affinity = AffinityClient()
    unipile = UnipileClient()

    # Stage 1: thesis check on anything new and unchecked.
    for company in affinity.get_new_unchecked_companies():
        prompt = thesis_check.build_prompt(company_data=company)
        # verdict = call_model(prompt)  # <- model call, structured output only
        verdict = None  # placeholder until wired to a real model call
        if verdict is None:
            continue
        if not verdict["in_scope"]:
            affinity.mark_out_of_scope(company["id"], verdict["reason"])
            continue
        # in scope: Status stays New. Stash profile_category and language
        # somewhere stage 2 and 3 can read it back from, a note or a new
        # field, not recomputed each stage.
        if verdict["profile_category"] == "warm_intro":
            routed = message_composer.route_warm_intro(company)
            affinity.write_pending_note(company["id"], routed["reason"],
                                         "Routed To Juliette")
            continue  # skip stages 2 and 3 entirely for this one

    # Stage 2: connect. For in scope, non warm intro companies without a
    # resolved relation.
    for company in affinity.get_new_unchecked_companies():  # replace with
                                                             # "in scope,
                                                             # not warm
                                                             # intro, not
                                                             # yet invited"
        linkedin_url = affinity.get_founder_linkedin_url(company)
        if not linkedin_url:
            continue  # needs a research fallback, not built yet
        provider_id = unipile.resolve_provider_id(linkedin_url)
        relation = unipile.get_relation_status(provider_id)
        if relation == "not_connected":
            unipile.send_invite(provider_id, note_text="")  # note text is
                                                             # the real
                                                             # opening line,
                                                             # not empty,
                                                             # once pulled
                                                             # from the
                                                             # playbook

    # Stage 3: message. For anyone who accepted since the last run.
    for provider_id in unipile.list_relations():  # filter to new since
                                                    # last check
        profile_category = None  # from stage 1's verdict, read back
        language = None  # from stage 1's verdict, read back
        playbook_text = None  # pulled from the Google Doc, see
                               # message_composer's module docstring
        prompt = message_composer.build_first_message_prompt(
            company_data=None, profile_category=profile_category,
            language=language, playbook_text=playbook_text, style_log=None,
        )
        # draft = call_model(prompt)
        draft = None
        if draft:
            affinity.write_pending_note(provider_id, draft, "Message Drafted")

    # Stage 4: approval and feedback. For anything pending a decision.
    # Superseded 2026-08-19: this loop's shape (iterate everything drafted,
    # read its note, parse the decision out of the text) is the pattern
    # that made get_notes_for_entity the most-called Affinity operation in
    # the project. The live version in prompts/orchestrator.md instead
    # filters Status == Approved / Passed from the one list-wide query and
    # only reads a note for the Approved ones, once. See approval_loop.py's
    # module docstring and docs/ARCHITECTURE.md, "Why state lives in
    # Affinity, not a separate database."
    for entity_id in []:  # anything with a Message Drafted stage
        note_text = affinity.read_latest_note(entity_id)
        decision = approval_loop.parse_decision(note_text)
        if decision["status"] == "approved":
            unipile.send_message(entity_id, decision["final_text"])
            message_composer.append_feedback(
                "approved", decision["final_text"], decision["reason"]
            )
        elif decision["status"] == "rejected":
            message_composer.append_feedback(
                "rejected", None, decision["reason"]
            )

    # Stage 5: follow up. For anyone messaged about a week ago with no
    # reply since.
    for entity_id in []:  # Message Sent, sent_at older than ~7 days, no
                           # reply detected
        profile_category = None
        language = None
        playbook_text = None
        original_message = None
        prompt = message_composer.build_follow_up_prompt(
            profile_category=profile_category, language=language,
            playbook_text=playbook_text, original_message=original_message,
        )
        # draft = call_model(prompt)  # for high_profile this call needs
        # fresh research (fundraise, launch, press, hire) as part of the
        # same pass, not a separate step
        draft = None
        if draft:
            affinity.write_pending_note(entity_id, draft, "Follow Up Drafted")

    # Stage 6: reply handling. For anyone who has replied since the last
    # run, detected via Unipile's new message signal.
    for entity_id, founder_reply in []:  # (entity_id, reply_text) pairs
        original_verdict = None  # stage 1's verdict for this company
        playbook_text = None
        prompt = message_composer.build_reply_handling_prompt(
            founder_reply=founder_reply, original_verdict=original_verdict,
            playbook_text=playbook_text,
        )
        # response_verdict = call_model(prompt)  # judges fit fresh, then
        # drafts either the booking response or the specific pass message
        response_verdict = None
        if response_verdict:
            affinity.write_pending_note(
                entity_id, response_verdict["draft"], "Reply Drafted"
            )
            new_status = ("Reached Out" if response_verdict["in_scope"]
                          else "Out of Scope")
            # affinity.set_status(entity_id, ...) once status option ids
            # for this path are confirmed


if __name__ == "__main__":
    run_once()
