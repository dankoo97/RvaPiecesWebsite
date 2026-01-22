from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase

from .admin import EventAdmin
from .models import Event


test_vars = {
    "test1": {
        "name": "Test Event",
        "short_description": "This is a test event",
        "long_description": "This is a test event with a longer description",
        "slug": "test-event",
        "tournament_event_link": "https://www.example.com/tournament-event",  # Disables chessnut integration
    },
    "test2": {
        "name": "Test Event 2",
        "short_description": "This is a test event 2",
        "long_description": "This is a test event 2 with a longer description",
        "slug": "test-event-2",
        "tournament_event_link": "https://www.example.com/tournament-event-2",  # Disables chessnut integration
    },
}


class EventTests(TestCase):
    def setUp(self):
        self.draft_event = Event.objects.create(**test_vars["test1"])
        self.published_event = self.draft_event.publish()
        self.archived_event = Event.objects.create(**test_vars["test2"]).archive()

    def test_public_events_resolve(self):
        resolve = self.client.get(self.published_event.get_absolute_url())
        self.assertEqual(resolve.status_code, 200, "Failed to resolve published event")

    def test_draft_events_return_404_for_anon_users(self):
        resolve = self.client.get(self.draft_event.get_absolute_url())
        self.assertEqual(resolve.status_code, 404, "Resolved draft event for anon user")

    def test_archived_events_return_404_for_anon_users(self):
        resolve = self.client.get(self.archived_event.get_absolute_url())
        self.assertEqual(
            resolve.status_code, 404, "Resolved archived event for anon user"
        )


class EventAdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = EventAdmin(Event, self.site)
        self.user = User.objects.create_user(
            username="admin", password="", is_staff=True, is_superuser=True
        )

    def test_create_event(self):
        # Create event from admin
        self.admin.save_model(
            obj=Event(**test_vars["test2"]),
            request={"user": self.user},
            form=None,
            change=None,
        )
        event = Event.objects.get(name=test_vars["test2"]["name"])
        self.assertIsNotNone(event, "Failed to create event from admin")
        self.assertFalse(
            event.is_published,
            "Event created from admin is published before entering draft state",
        )

        # View draft as admin user
        self.client.force_login(self.user)
        resolve = self.client.get(event.get_absolute_url(), follow=True)
        self.assertEqual(
            resolve.status_code, 200, "Failed to resolve event created from admin"
        )
        self.assertEqual(
            Event.objects.drafts().count(), 1, "Draft event not created from admin"
        )

        # Publish and view event as admin user
        self.admin.publish_draft(
            request={"user": self.user}, queryset=Event.objects.filter(pk=event.pk)
        )
        self.assertTrue(
            event.is_published, "Failed to publish event published from admin"
        )
        resolve = self.client.get(event.get_absolute_url(), follow=True)
        self.assertEqual(
            resolve.status_code, 200, "Failed to resolve event published from admin"
        )
        self.assertEqual(
            Event.objects.published().count(),
            1,
            "Published event not created from admin",
        )

        # Archive and view event as admin user
        self.admin.archive_event(
            request={"user": self.user}, queryset=Event.objects.filter(pk=event.pk)
        )
        self.assertTrue(
            event.is_archived, "Failed to archive event archived from admin"
        )
        self.assertFalse(event.is_published, "Archived event is still published")
        resolve = self.client.get(event.get_absolute_url(), follow=True)
        self.assertEqual(
            resolve.status_code, 200, "Failed to resolve event archived from admin"
        )
        self.assertEqual(
            Event.objects.archived().count(), 1, "Archived event not created from admin"
        )
