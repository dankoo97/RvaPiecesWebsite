import datetime
import os

import requests
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from recurring.models import CalendarEntry


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

    tournament_event_link = models.URLField(blank=True)
    tournament_pairings_link = models.URLField(blank=True)
    tournament_standings_link = models.URLField(blank=True)

    # Calendar entry is bugged for non utc timezones, and will increment the time by 4 hours each time it is saved
    # https://github.com/boosh/django_recurring/issues/4
    calendar = models.ForeignKey(
        CalendarEntry, on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.name

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


class Announcement(models.Model):
    content = models.TextField(max_length=200, default="Something is happening!")
    expires = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["expires"]

    def __str__(self):
        return self.content
