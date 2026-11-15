"""Guard for actions that create or change data on outside services (Lichess, Discord, ...).

The dev deployment sets EXTERNAL_WRITES_ENABLED=False so it can still read from the live
services but can't post to the club's real Discord channels or Lichess account.
"""

from django.conf import settings


class ExternalWritesDisabled(Exception):
    """Raised instead of performing an external write when they're turned off."""


def require_external_writes(action: str) -> None:
    """Raise ExternalWritesDisabled if this environment may not perform `action`."""
    if not settings.EXTERNAL_WRITES_ENABLED:
        raise ExternalWritesDisabled(
            f"{action} is turned off on this test site, so nothing was sent."
        )
