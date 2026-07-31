import datetime
from unittest.mock import patch

from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase

from .admin import EventAdmin
from .models import Event


test_events = {
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
    "rvapieces": {
        "name": "RVAPieces",
        "short_description": "The official RVAPieces event",
        "long_description": "The official RVAPieces event with a longer description",
        "slug": "rvapieces",
        # Enable chessnut integration
    },
}

section_data = (
    [
        {
            "id": 1,
            "name": "Open",
            "player_count": 16,
        },
        {
            "id": 2,
            "name": "U1200",
            "player_count": 8,
        },
    ],
)


test_chessnut_events = {
    "ongoing_event": {
        "id": 1,
        "name": "RVAPieces Ongoing Event",
        "slug": "ongoing-event",
        "visibility": "public",
        "city": "Richmond",
        "state": "VA",
        "country": "US",
        "rating_system": "custom",
        "start_date": datetime.date(2026, 1, 1),
        "end_date": datetime.date(2026, 1, 31),
        "created": "2026-01-01T00:00:00Z",
        "sections": section_data,
    },
    "past_event": {
        "id": 2,
        "name": "RVAPieces Past Event",
        "slug": "past-event",
        "visibility": "public",
        "city": "Richmond",
        "state": "VA",
        "country": "US",
        "rating_system": "custom",
        "start_date": datetime.date(2025, 1, 1),
        "end_date": datetime.date(2025, 1, 31),
        "created": "2025-01-01T00:00:00Z",
        "sections": section_data,
    },
    "upcoming_event": {
        "id": 3,
        "name": "RVAPieces Upcoming Event",
        "slug": "upcoming-event",
        "visibility": "public",
        "city": "Richmond",
        "state": "VA",
        "country": "US",
        "rating_system": "custom",
        "start_date": datetime.date(2025, 1, 1),
        "end_date": datetime.date(2027, 1, 31),
        "created": "2027-01-01T00:00:00Z",
        "sections": section_data,
    },
    "ongoing_one_day_event": {
        "id": 4,
        "name": "RVAPieces Ongoing One Day Event",
        "slug": "ongoing-one-day-event",
        "visibility": "public",
        "city": "Richmond",
        "state": "VA",
        "country": "US",
        "rating_system": "custom",
        "start_date": datetime.date(2025, 1, 1),
        "created": "2026-01-01T00:00:00Z",
        "sections": section_data,
    },
    "past_one_day_event": {
        "id": 5,
        "name": "RVAPieces Past One Day Event",
        "slug": "past-one-day-event",
        "visibility": "public",
        "city": "Richmond",
        "state": "VA",
        "country": "US",
        "rating_system": "custom",
        "start_date": "2025-01-01",
        "created": "2025-01-01T00:00:00Z",
        "sections": section_data,
    },
    "upcoming_one_day_event": {
        "id": 6,
        "name": "RVAPieces Upcoming One Day Event",
        "slug": "upcoming-one-day-event",
        "visibility": "public",
        "city": "Richmond",
        "state": "VA",
        "country": "US",
        "rating_system": "custom",
        "start_date": "2027-01-01",
        "created": "2027-01-01T00:00:00Z",
        "sections": section_data,
    },
}


class EventTests(TestCase):
    def setUp(self):
        self.draft_event = Event.objects.create(**test_events["test1"])
        self.published_event = self.draft_event.publish()
        self.archived_event = Event.objects.create(**test_events["test2"]).archive()

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


class ChessnutEventTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(**test_events["rvapieces"]).publish()

    def tearDown(self):
        pass

    def test_ongoing_event_matches_chessnut_event(self, *args, **kwargs):
        pass

    def test_past_event_matches_chessnut_event(self):
        pass

    def test_upcoming_event_matches_chessnut_event(self):
        pass

    def test_ongoing_one_day_event_matches_chessnut_event(self):
        pass

    def test_past_one_day_event_matches_chessnut_event(self):
        pass

    def test_upcoming_one_day_event_matches_chessnut_event(self):
        pass


@patch(
    "django.contrib.messages.add_message", return_value=None
)  # Ignore if the message is not displayed
class EventAdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = EventAdmin(Event, self.site)
        self.user = User.objects.create_user(
            username="admin", password="", is_staff=True, is_superuser=True
        )
        self.request = HttpRequest()
        self.request.user = self.user

    def test_create_event(self, *args, **kwargs):
        # Create event from admin
        self.admin.save_model(
            obj=Event(**test_events["test2"]),
            request=self.request,
            form=None,
            change=None,
        )
        event = Event.objects.get(name=test_events["test2"]["name"])
        self.assertIsNotNone(event, "Failed to create event from admin")
        self.assertFalse(
            event.is_published,
            "Event created from admin is published before entering draft state",
        )

    def test_view_draft_as_admin(self, *args, **kwargs):
        # View draft as admin user
        self.client.force_login(self.user)
        draft_event = Event.objects.create(**test_events["test2"])
        resolve = self.client.get(draft_event.get_absolute_url(), follow=True)
        self.assertEqual(
            resolve.status_code, 200, "Failed to resolve event created from admin"
        )
        self.assertEqual(
            Event.objects.drafts().count(), 1, "Draft event not created from admin"
        )

    def test_publish_draft_as_admin(self, *args, **kwargs):
        # Publish and view event as admin user
        draft_event = Event.objects.create(**test_events["test2"])
        self.admin.publish_draft(
            request=self.request, queryset=Event.objects.filter(pk=draft_event.pk)
        )
        public_event = Event.objects.get(
            name=test_events["test2"]["name"], is_published=True
        )
        self.assertTrue(
            public_event.is_published, "Failed to publish event published from admin"
        )
        resolve = self.client.get(public_event.get_absolute_url(), follow=True)
        self.assertEqual(
            resolve.status_code, 200, "Failed to resolve event published from admin"
        )
        self.assertEqual(
            Event.objects.public().count(),
            1,
            "Published event not created from admin",
        )

    def test_archive_as_admin(self, *args, **kwargs):
        self.client.force_login(self.user)
        draft_event = Event.objects.create(**test_events["test2"])
        self.admin.archive_event(
            request=self.request, queryset=Event.objects.filter(pk=draft_event.pk)
        )
        archived_event = Event.objects.get(
            name=test_events["test2"]["name"], is_archived=True
        )
        self.assertTrue(
            archived_event.is_archived, "Failed to archive event archived from admin"
        )
        self.assertFalse(
            archived_event.is_published, "Archived event is still published"
        )
        resolve = self.client.get(archived_event.get_absolute_url(), follow=True)
        self.assertEqual(
            resolve.status_code, 200, "Failed to resolve event archived from admin"
        )
        self.assertEqual(
            Event.objects.archived().count(), 1, "Archived event not created from admin"
        )
