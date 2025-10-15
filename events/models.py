import datetime
import os

import requests
from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from recurring.models import CalendarEntry


class EventManager(models.Manager):
    def public(self):
        return self.filter(is_published=True)

    def drafts(self):
        return self.filter(is_published=False, is_archived=False)

    def archived(self):
        return self.filter(is_archived=True)


# Create your models here.
class Event(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, null=False, blank=False)
    short_description = models.TextField(
        max_length=500, default="Things are happening at Rva Pieces!"
    )
    long_description = CKEditor5Field(default="Things are happening at Rva Pieces!")
    location = models.CharField(max_length=100, blank=True)

    icon = models.ImageField(upload_to="media/images/events/", blank=True)
    image = models.ImageField(upload_to="media/images/events/", blank=True)

    is_promoted = models.BooleanField(default=False)

    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(blank=True, null=True)

    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    published_version = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True, related_name="+"
    )

    tournament_event_link = models.URLField(blank=True)
    tournament_pairings_link = models.URLField(blank=True)
    tournament_standings_link = models.URLField(blank=True)

    # Calendar entry is bugged for non utc timezones, and will increment the time by 4 hours each time it is saved
    # https://github.com/boosh/django_recurring/issues/4
    calendar = models.ForeignKey(
        CalendarEntry, on_delete=models.CASCADE, blank=True, null=True
    )

    objects = EventManager()

    def __str__(self):
        if self.is_archived:
            return f"{self.name} (Archived {self.archived_at.date()})"
        return self.name if self.is_published else f"{self.name} (Draft)"

    def publish(self):
        if self.is_published:
            return self

        if self.is_archived:
            self.is_archived = False
            self.archived_at = None

            self.is_published = True
            self.published_at = datetime.datetime.now()
            self.save()
            return self

        try:
            if self.published_version:
                old_published_version = self.published_version
                old_published_version.archive()
            else:
                old_published_version = None

            published = Event.objects.create(
                name=self.name,
                short_description=self.short_description,
                long_description=self.long_description,
                location=self.location,
                icon=self.icon,
                image=self.image,
                is_promoted=self.is_promoted,
                is_published=True,
                published_at=datetime.datetime.now(),
                calendar=self.calendar,
                tournament_event_link=self.tournament_event_link,
                tournament_pairings_link=self.tournament_pairings_link,
                tournament_standings_link=self.tournament_standings_link,
            )

        except Exception as e:
            # Skip saving the published version if there is an error
            print(e)
            return None

        self.published_version = published
        self.save(update_fields=["published_version"])

        return published

    def archive(self):
        self.is_archived = True
        self.is_published = False
        self.is_promoted = False
        self.archived_at = datetime.datetime.now()
        self.save()

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        if self.is_published:
            self.slug = base_slug
        elif self.is_archived:
            self.slug = (
                f"{base_slug}-archived-{self.archived_at.strftime('%Y-%m-%d-%H-%M-%S')}"
            )
        else:
            self.slug = f"{base_slug}-draft"

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"/events/event/{self.slug}/"

    @staticmethod
    def get_chessnut_event(chess_club_id, *, start_date=None, end_date=None):
        if not os.environ.get("CHESSNUT_API_KEY"):
            raise ValueError("CHESSNUT_API_KEY environment variable not set")

        if start_date is None:
            start_date = datetime.date.min
        if end_date is None:
            end_date = datetime.date.max

        headers = {"Authorization": f"Bearer {os.environ.get('CHESSNUT_API_KEY')}"}
        params = {}
        response = requests.get(
            f"https://chessnut.club/api/v1/club/{chess_club_id}/events/fetch-all",
            headers=headers,
            params=params,
        )
        if response.status_code != 200:
            return []
        events = response.json()

        events_on_date = []
        for event in events["events"]:
            date = datetime.datetime.strptime(
                event["start_date"][:10], "%Y-%m-%d"
            ).date()
            if start_date <= date <= end_date:
                events_on_date.append(event)

        return events_on_date

    class Meta:
        permissions = [
            ("can_publish_event", "Can publish event"),
            ("can_archive_event", "Can archive event"),
            ("can_view_unpublished_event", "Can view draft and archived events"),
        ]


class Announcement(models.Model):
    content = models.TextField(max_length=200, default="Something is happening!")
    expires = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["expires"]

    def __str__(self):
        return self.content
