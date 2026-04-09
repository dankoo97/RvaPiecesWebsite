import datetime
import os
import re
import requests
from io import StringIO

import berserk
import chess.pgn

from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from recurring.models import CalendarEntry
from django.core.cache import cache

from helpers.models import PrettyJSONEncoder


class EventManager(models.Manager):
    def public(self):
        return self.filter(is_published=True)

    def drafts(self):
        return self.filter(is_published=False, is_archived=False)

    def archived(self):
        return self.filter(is_archived=True)


CHESSNUT_CLUB_ID = os.environ.get("CHESSNUT_CLUB_ID")
CACHE_TIMEOUT = 60 * 60 * 24


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
        return self

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

    @property
    def chessnut_events(self):
        if self.tournament_event_link:
            # Assume the link is either to chessnut or another tournament website
            return []

        events = [
            event
            for event in self.get_all_chessnut_events()
            if event["name"].startswith(self.name)
        ]

        ongoing = [
            e
            for e in events
            if e["start_date"] <= datetime.date.today() <= e["end_date"]
        ]
        upcoming = sorted(
            [e for e in events if e["start_date"] > datetime.date.today()],
            key=lambda e: e["start_date"],
        )
        past = sorted(
            [e for e in events if datetime.date.today() > e["end_date"]],
            key=lambda e: e["end_date"],
            reverse=True,
        )

        return ongoing + upcoming + past

    @staticmethod
    def get_all_chessnut_events(force_refresh=None) -> list[dict]:
        cache_key = "chessnut_events"
        if not force_refresh:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        print("Fetching chessnut events...")
        if not os.environ.get("CHESSNUT_API_KEY"):
            raise ValueError("CHESSNUT_API_KEY environment variable not set")

        headers = {"Authorization": f"Bearer {os.environ.get('CHESSNUT_API_KEY')}"}
        params = {
            "start_date": (
                datetime.date.today() - datetime.timedelta(days=60)
            ).isoformat(),
            "end_date": (
                datetime.date.today() + datetime.timedelta(days=90)
            ).isoformat(),
        }
        # NOTE: If chessnut ever updates their api such that we can filter events in the request, we should do that here
        response = requests.get(
            f"https://chessnut.club/api/v1/club/{CHESSNUT_CLUB_ID}/events/fetch-all",
            headers=headers,
            params=params,
        )
        if response.status_code != 200:
            print(f"Failed to fetch chessnut events: {response.text}")
            return []

        def datetime_parser(dct):
            for k, v in dct.items():
                if "date" in k and isinstance(v, str):
                    dct[k] = datetime.date.fromisoformat(v)
            return dct

        result = response.json(object_hook=datetime_parser)["events"]
        print("Fetched chessnut events")
        if result is not None:
            cache.set(cache_key, result, CACHE_TIMEOUT)
        return result

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


class LichessStudy(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="lichess_studies",
        limit_choices_to={"is_published": True},
    )
    name = models.CharField(max_length=100)
    study_id = models.CharField(
        max_length=100, unique=True, null=False, blank=False, primary_key=True
    )
    chapters = models.JSONField(default=list, encoder=PrettyJSONEncoder)
    tournament_date = models.DateField()

    def save(self, *args, **kwargs):
        if "lichess" in self.study_id:
            p = re.compile(r"study/(?P<study_id>[a-zA-Z0-9]+)")
            self.study_id = p.search(self.study_id).group("study_id")

        if len(self.chapters) == 0:
            self.download_study()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def study_url(self):
        return f"https://lichess.org/study/{self.study_id}"

    def add_chapters(self, pgn, chapter_name=None):
        """
        https://lichess.org/api#tag/studies/POST/api/study/{studyId}/import-pgn
        :param pgn: Pgn representation of the chapters
        :param chapter_name: Name of the chapter
        :return: List of chapters created
        """
        session = berserk.TokenSession(os.environ.get("LICHESS_API_TOKEN"))
        client = berserk.Client(session=session)
        created_chapters = client.studies.import_pgn(
            study_id=self.study_id, pgn=pgn, chapter_name=chapter_name
        )
        self.chapters.append(created_chapters)
        return created_chapters

    def download_study(self):
        """
        https://lichess.org/api#tag/studies/GET/api/study/{studyId}.pgn
        """
        session = berserk.TokenSession(os.environ.get("LICHESS_API_TOKEN"))
        client = berserk.Client(session=session)

        chapters = client.studies.export(study_id=self.study_id)

        self.chapters = []
        for chapter in chapters:
            game = chess.pgn.read_game(StringIO(chapter))
            self.chapters.append(dict(game.headers))

            if not self.name:
                self.name = game.headers["StudyName"]

        return self.chapters
