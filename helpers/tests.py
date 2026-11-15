from unittest import mock

from django.test import SimpleTestCase, override_settings

from events.models import LichessStudy
from helpers.external_writes import ExternalWritesDisabled, require_external_writes


class ExternalWritesTests(SimpleTestCase):
    @override_settings(EXTERNAL_WRITES_ENABLED=True)
    def test_allowed_when_enabled(self):
        require_external_writes("Anything")

    @override_settings(EXTERNAL_WRITES_ENABLED=False)
    def test_blocked_when_disabled(self):
        with self.assertRaises(ExternalWritesDisabled):
            require_external_writes("Anything")

    @override_settings(EXTERNAL_WRITES_ENABLED=False)
    def test_lichess_and_discord_writes_never_reach_the_network(self):
        study = LichessStudy(study_id="abc12345")
        with (
            mock.patch("events.models.berserk.Client") as client,
            mock.patch("events.models.DiscordWebhook") as webhook,
        ):
            with self.assertRaises(ExternalWritesDisabled):
                study.add_chapters("1. e4 e5")
            with self.assertRaises(ExternalWritesDisabled):
                study.share_to_discord(mock.Mock(), "chapter")
            with self.assertRaises(ExternalWritesDisabled):
                LichessStudy.create_lichess_study(name="Test")
        client.assert_not_called()
        webhook.assert_not_called()
