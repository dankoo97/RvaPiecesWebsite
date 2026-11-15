"""Offline stand-ins for Lichess/Chessnut reads, used only by agent_settings.

The event detail page lists the club's Lichess studies (and staff views list Chessnut events)
on every render, which needs real API tokens. Local runs usually don't have them, so when a
token isn't set, the lookup returns "nothing" instead of raising. Set LICHESS_API_TOKEN /
CHESSNUT_API_KEY in the environment to talk to the real services instead.
"""

import os

from django.apps import AppConfig


class AgentStubsConfig(AppConfig):
    name = "agent_stubs"
    label = "agent_stubs"
    path = os.path.dirname(os.path.abspath(__file__))

    def ready(self):
        from events.chessnut import Chessnut
        from events.models import LichessStudy

        if not os.environ.get("LICHESS_API_TOKEN"):
            LichessStudy.get_all_lichess_studies = classmethod(lambda cls: [])
            print(
                "agent_stubs: LICHESS_API_TOKEN not set -> Lichess study list is empty"
            )
        if not os.environ.get("CHESSNUT_API_KEY"):
            Chessnut.get_all_chessnut_events = staticmethod(lambda **kwargs: [])
            Chessnut.get_chessnut_event_by_id = staticmethod(
                lambda *args, **kwargs: None
            )
            print(
                "agent_stubs: CHESSNUT_API_KEY not set -> Chessnut event lists are empty"
            )
