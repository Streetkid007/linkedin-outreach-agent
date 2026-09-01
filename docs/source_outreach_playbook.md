# Source: Clover Founder Outreach Playbook (Google Doc, May 2026)

Kept as the source of truth for message_composer.py. Four profile
categories, not the stealth or not binary this project started with:

1. **Stealth Founder**: heard about a new project, not yet announced.
2. **Active Company**: live company or publicly announced project. Always
   the specific version, the generic "I heard great things" variant was
   explicitly removed from the playbook, do not resurrect it.
3. **High-Profile Founder**: receives heavy cold outreach. Every placeholder
   must be a real, specific observation, no vague compliments. Follow up
   also cannot be a generic nudge, it needs a fresh data point.
4. **Warm Intro or Referred**: a mutual made the connection. OPEN QUESTION,
   see chat: likely should route to Juliette directly rather than through
   the automated connect and message pipeline, since getting the mutual or
   the context wrong here costs more than automating it saves.

Each of the four has French and English versions live in the Google Doc
(id 1Yy4n3wP8U8vUwqrAulkwueaf7p-rjUrEgbuNp_KBrTU). Pull fresh at build time
rather than copying the text here, so edits in the Doc stay the source of
truth instead of drifting from a copy.

## Additional stages this adds to the pipeline

- **Follow up (new)**: sent if no reply after about a week. Stealth and
  Active Company founders get a simple calendar nudge. High-Profile
  founders need a fresh, specific data point (fundraise, launch, press,
  hire) gathered at send time, not reused from the original outreach.
- **Reply handling (new)**: when a founder replies, run a second thesis
  judgment on what they actually describe, not just the original scored
  data, since a reply can reveal a company is not actually a fit even after
  clearing the first check. If it fits, send the booking link and ask for
  materials at that company's owner's email (Juliette or Hugo — see
  config/settings.py OWNERS). If not, send the specific pass message from
  the playbook, not a generic decline.
