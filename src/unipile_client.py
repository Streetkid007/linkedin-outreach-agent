"""
Original stub for a Unipile wrapper. Superseded by scripts/unipile_cli.py,
which is the real, live implementation actually used by the continuous
runner (see docs/RUNNING_LOCALLY.md) and enforces the daily send cap from
config/settings.py. Kept here as the original research notes on what
Unipile supports; scripts/unipile_cli.py is what to edit and run.

Wrapper over Unipile's LinkedIn actions, matching what their docs actually
support (checked live, see chat for sources):

- POST /users/invite sends a connection request and accepts an optional
  message field, used here as the real opening line rather than a separate
  first message, since it lets a reply to the invite double as message one.
- Detecting acceptance has three paths: the "new relation" webhook (delayed
  up to ~8h, not real time), a "new message" webhook firing if the invite
  note itself gets a reply, or polling the relations and sent invitations
  lists. This project uses polling on a schedule since the webhook is not
  real time anyway.
- Sending an actual message still requires the recipient to be a first
  degree connection unless the sending account has InMail rights (Sales
  Navigator or Recruiter), which is a separate cost and license question
  worth confirming before assuming it as a fallback path.
"""

import os


class UnipileClient:
    def __init__(self):
        self.dsn = os.environ.get("UNIPILE_DSN")
        self.api_key = os.environ.get("UNIPILE_API_KEY")
        self.account_id = os.environ.get("UNIPILE_LINKEDIN_ACCOUNT_ID")

    def resolve_provider_id(self, linkedin_public_url):
        """GET /users/{identifier} to turn a profile URL into a provider_id."""
        raise NotImplementedError

    def get_relation_status(self, provider_id):
        """
        Returns first_degree, pending_sent, pending_received, or
        not_connected. Needed before deciding whether to invite or go
        straight to messaging.
        """
        raise NotImplementedError

    def send_invite(self, provider_id, note_text):
        """
        POST /users/invite. note_text doubles as message one; keep it under
        LinkedIn's ~300 character invite note limit.
        """
        raise NotImplementedError

    def list_sent_invitations(self):
        """For polling: compare against what is still pending vs accepted."""
        raise NotImplementedError

    def list_relations(self):
        """For polling: newly appearing first degree connections."""
        raise NotImplementedError

    def send_message(self, provider_id, text):
        """
        Only valid once first degree, or via InMail if the account carries
        that license. Raise clearly rather than silently failing if neither
        condition holds, this is the exact mistake the connect first
        step exists to prevent.
        """
        raise NotImplementedError
