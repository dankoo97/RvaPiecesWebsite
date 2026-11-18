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


@override_settings(ALLOWED_HOSTS=["rvapieces.org", "www.rvapieces.org"])
class WwwRedirectTests(SimpleTestCase):
    def test_www_redirects_to_bare_domain(self):
        response = self.client.get("/events/?page=2", HTTP_HOST="www.rvapieces.org")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "https://rvapieces.org/events/?page=2")

    def test_bare_domain_is_not_redirected(self):
        response = self.client.get("/does-not-exist/", HTTP_HOST="rvapieces.org")
        self.assertNotEqual(response.status_code, 301)
