import datetime
import os
import re
from io import StringIO

import berserk
import chess.pgn
from discord_webhook.webhook import DiscordWebhook, DiscordEmbed

from django.db import models, transaction
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from recurring.models import CalendarEntry
from django.utils import timezone

from events.chessnut import Chessnut
from helpers.models import PrettyJSONEncoder


def default_chessnut_handler():
    return {
        "enabled": False,
        "title_regex": "",
        "days_before_start": 0,
        "days_after_end": 0,
        "ignored_event_ids": [],
    }


def default_chessnut_events():
    return {"events": []}


class EventManager(models.Manager):
    def public(self):
        return self.filter(is_published=True)

    def drafts(self):
        return self.filter(is_published=False, is_archived=False)

    def archived(self):
        return self.filter(is_archived=True)


class LichessStudyManager(models.Manager):
    def create_study(self, name, event):
        pass

    def download_study(self, study_id, event):
        session = berserk.TokenSession(LichessStudy.api_token())
        client = berserk.Client(session=session)

        lichess_study_chapters = client.studies.export(study_id=study_id)
        my_chapters = []
        name = None

        for chapter in lichess_study_chapters:
            game = chess.pgn.read_game(StringIO(chapter))
            my_chapters.append(dict(game.headers))

            name = game.headers["StudyName"]

        default_values = {
            "Event": lambda: event.name,
            "Date": lambda: event.tournament_date,
            "Site": lambda: event.location,
        }

        study = self.create(
            name=name,
            event=event,
            study_id=study_id,
            chapters=my_chapters,
            default_values=default_values,
        )

        return study


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

    discord_channel_id = models.CharField(max_length=100, null=True, blank=True)
    discord_webhook_urls = models.JSONField(default=dict, null=True, blank=True)

    tournament_event_link = models.URLField(blank=True)
    tournament_pairings_link = models.URLField(blank=True)
    tournament_standings_link = models.URLField(blank=True)

    # Calendar entry is bugged for non utc timezones, and will increment the time by 4 hours each time it is saved
    # https://github.com/boosh/django_recurring/issues/4
    calendar = models.ForeignKey(
        CalendarEntry, on_delete=models.CASCADE, blank=True, null=True
    )

    chessnut_events = models.JSONField(
        default=default_chessnut_events,
        blank=True,
        null=True,
    )
    chessnut_handler = models.JSONField(
        default=default_chessnut_handler,
        blank=True,
    )

    objects = EventManager()
    chessnut_worker = Chessnut()

    def __str__(self):
        if self.is_archived:
            return f"{self.name} (Archived {self.archived_at.date()})"
        return self.name if self.is_published else f"{self.name} (Draft)"

    def publish(self):
        """
        Publish this event and return the published Event.

        Runs in a single transaction: if anything fails, the previously published version is
        left untouched and the exception is raised to the caller.
        """
        if self.is_published:
            return self

        if self.is_archived:
            self.is_archived = False
            self.archived_at = None

            self.is_published = True
            self.published_at = timezone.now()
            self.save()
            return self

        with transaction.atomic():
            old_published_version = self.published_version
            if old_published_version:
                old_published_version.archive()

            published = Event.objects.create(
                name=self.name,
                short_description=self.short_description,
                long_description=self.long_description,
                location=self.location,
                icon=self.icon,
                image=self.image,
                is_promoted=self.is_promoted,
                is_published=True,
                published_at=timezone.now(),
                calendar=self.calendar,
                tournament_event_link=self.tournament_event_link,
                tournament_pairings_link=self.tournament_pairings_link,
                tournament_standings_link=self.tournament_standings_link,
                discord_channel_id=self.discord_channel_id,
                discord_webhook_urls=self.discord_webhook_urls,
                chessnut_events=self.chessnut_events,
                chessnut_handler=self.chessnut_handler or default_chessnut_handler(),
            )

            if old_published_version:
                old_published_version.lichess_studies.update(event=published)

            self.published_version = published
            self.save(update_fields=["published_version"])

        return published

    def archive(self):
        self.is_archived = True
        self.is_published = False
        self.is_promoted = False
        self.archived_at = timezone.now()
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

        self.chessnut_events = self.chessnut_events or {"events": []}
        for event in self.chessnut_events.get("events", []):
            for date_field in ("start_date", "end_date"):
                if event.get(date_field) is datetime.date:
                    event[date_field] = event[date_field].isoformat()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"/events/event/{self.slug}/"

    def sync_magic_chessnut_events(self):
        config = self.chessnut_handler or {}
        if not config.get("enabled"):
            return False

        try:
            title_pattern = re.compile(config.get("title_regex", ""), re.IGNORECASE)
            days_before_start = int(config.get("days_before_start", 0))
            days_after_end = int(config.get("days_after_end", 0))
        except (TypeError, ValueError, re.error):
            return False

        today = datetime.date.today()
        ignored_event_ids = {
            str(event_id) for event_id in config.get("ignored_event_ids", [])
        }
        current_events = self.chessnut_events.get("events", [])
        manually_added_events = [
            event
            for event in current_events
            if not event.get("magic_added_by_handler")
            and not event.get("_magic_chessnut")
        ]
        generated_events = []
        manual_event_ids = {str(event.get("id")) for event in manually_added_events}

        for api_event in Chessnut.get_all_chessnut_events():
            event_id = str(api_event.get("id"))
            if event_id in ignored_event_ids or event_id in manual_event_ids:
                continue

            name = str(api_event.get("name", ""))
            if not title_pattern.search(name):
                continue

            start_date = api_event.get("start_date")
            end_date = api_event.get("end_date", start_date)
            try:
                start_date = datetime.date.fromisoformat(str(start_date)[:10])
                end_date = datetime.date.fromisoformat(str(end_date)[:10])
            except (TypeError, ValueError):
                continue

            if not (
                start_date - datetime.timedelta(days=days_before_start)
                <= today
                <= end_date + datetime.timedelta(days=days_after_end)
            ):
                continue

            event = dict(api_event)
            event["start_date"] = start_date.isoformat()
            event["end_date"] = end_date.isoformat()
            event["expires"] = (
                end_date + datetime.timedelta(days=days_after_end)
            ).isoformat()
            event["magic_added_by_handler"] = True
            generated_events.append(event)

        generated_events_by_id = {str(event["id"]): event for event in generated_events}
        updated_events = []
        for current_event in current_events:
            event_id = str(current_event.get("id"))
            if current_event.get("magic_added_by_handler") or current_event.get(
                "_magic_chessnut"
            ):
                if event_id in generated_events_by_id:
                    updated_events.append(generated_events_by_id.pop(event_id))
            else:
                updated_events.append(current_event)

        updated_events.extend(generated_events_by_id.values())
        if updated_events == current_events:
            return False

        self.chessnut_events = {"events": updated_events}
        self.save()
        return True

    def update_chessnut_json(self, new_json, removed_event_ids=None):
        current_event_ids = {
            str(event.get("id")) for event in self.chessnut_events.get("events", [])
        }
        updated_event_ids = {
            str(event.get("id")) for event in new_json.get("events", [])
        }
        explicitly_removed_ids = {
            str(event_id) for event_id in (removed_event_ids or [])
        }
        removed_ids = (
            current_event_ids - updated_event_ids
            if removed_event_ids is None
            else explicitly_removed_ids
        )
        handler = self.chessnut_handler or {}
        ignored_event_ids = handler.setdefault("ignored_event_ids", [])
        ignored_event_ids.extend(
            event_id
            for event_id in removed_ids
            if event_id not in {str(ignored_id) for ignored_id in ignored_event_ids}
        )

        updated_json = {"events": []}
        for item in new_json["events"]:
            if "club" not in item:
                chessnut_event = Chessnut().get_chessnut_event_by_id(
                    item["id"]
                ) or dict(item)
                for local_field in (
                    "expires",
                    "magic_added_by_handler",
                    "_magic_chessnut",
                ):
                    if local_field in item:
                        chessnut_event[local_field] = item[local_field]
                updated_json["events"].append(chessnut_event)
            else:
                updated_json["events"].append(item)

        if explicitly_removed_ids:
            updated_json["events"].extend(
                event
                for event in self.chessnut_events.get("events", [])
                if str(event.get("id")) not in updated_event_ids
                and str(event.get("id")) not in explicitly_removed_ids
            )

        self.chessnut_handler = handler
        self.chessnut_events = updated_json
        self.save()

    def add_chessnut_event(self, chessnut_event_id):
        chessnut_event = Chessnut.get_chessnut_event_by_id(chessnut_event_id)
        self.chessnut_events.append(chessnut_event)

    def delete_chessnut_event(self, chessnut_event_id):
        self.chessnut_events["events"] = [
            event
            for event in self.chessnut_events["events"]
            if str(event["id"]) != str(chessnut_event_id)
        ]
        handler = self.chessnut_handler or {}
        ignored_event_ids = handler.setdefault("ignored_event_ids", [])
        if str(chessnut_event_id) not in {
            str(event_id) for event_id in ignored_event_ids
        }:
            ignored_event_ids.append(chessnut_event_id)
        self.chessnut_handler = handler
        self.save()

    def refresh_chessnut_event(self, chessnut_event_id):
        chessnut_event = Chessnut.get_chessnut_event_by_id(chessnut_event_id)
        self.chessnut_events = [
            e if e.id != chessnut_event_id else chessnut_event
            for e in self.chessnut_events
        ]

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
    tournament_date = models.DateField(default=datetime.date.today)
    chessnut_event_id = models.CharField(max_length=100, blank=True, null=True)
    # default_values = models.JSONField(default=dict, encoder=PrettyJSONEncoder)

    _api_token = None
    _default_study_options = {
        "visibility": "unlisted",
        "computer": "everyone",
        "explorer": "everyone",
        "cloneable": "everyone",
        "shareable": "everyone",
        "chat": "everyone",
        "sticky": False,
    }

    @property
    def study_url(self):
        return f"https://lichess.org/study/{self.study_id}"

    @classmethod
    def api_token(cls) -> str:
        if not cls._api_token:
            api_token = os.environ.get("LICHESS_API_TOKEN", "")
            if (
                len(api_token) >= 2
                and api_token[0] == api_token[-1]
                and api_token[0] in "\"'"
            ):
                api_token = api_token[1:-1].strip()
            if not api_token:
                raise ValueError("LICHESS_API_TOKEN environment variable not set")
            cls._api_token = api_token
        return cls._api_token

    def save(self, *args, **kwargs):
        if "lichess" in self.study_id:
            p = re.compile(r"study/(?P<study_id>[a-zA-Z0-9]+)")
            self.study_id = p.search(self.study_id).group("study_id")

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def add_chapters(self, pgn, orientation=None, chapter_name=None):
        """
        https://lichess.org/api#tag/studies/POST/api/study/{studyId}/import-pgn
        :param pgn: Pgn representation of the chapters
        :param orientation: POV of white or black
        :param chapter_name: Name of the chapter
        :return: List of chapters created
        """
        session = berserk.TokenSession(LichessStudy.api_token())
        client = berserk.Client(session=session)
        created_chapters = client.studies.import_pgn(
            study_id=self.study_id,
            pgn=pgn,
            chapter_name=chapter_name,
            orientation=orientation,
        )
        self.chapters.append(created_chapters)
        return created_chapters

    def share_to_discord(
        self,
        game: chess.pgn.Game,
        lichess_chapter_id: str,
        white_player_discord=None,
        black_player_discord=None,
    ):
        """
        :param game: The game to share to discord
        :param lichess_chapter_id: The chapter id for the game on Lichess.com
        :param white_player_discord: The discord username of the white player
        :param black_player_discord: The discord username of the black player
        """

        webhook = DiscordWebhook(url=self.event.discord_webhook_urls["study"])
        chapter_url = f"{self.study_url}/{lichess_chapter_id}"
        dev = {
            "name": "dan_koontz",
            "id": "906504873976147979",
        }
        webhook.allowed_mentions = {"parse": ["users"]}

        embed = DiscordEmbed(
            description=f"""
                Check out this game!

                Questions? Contact the developer: [@{dev["name"]}](https://discord.com/users/{dev["id"]})
            """,
        )
        embed.set_url(url=chapter_url)
        embed.set_footer(text="This game was submitted via rvapieces.org")
        embed.set_image(url=f"{chapter_url}.gif")
        embed.set_timestamp()
        embed.set_color(0x9246E3)

        if "White" in game.headers and "Black" in game.headers:
            embed.set_title(f"{game.headers['White']} vs {game.headers['Black']}")

        webhook.add_embed(embed)
        webhook.execute()

    def download_study(self):
        """
        https://lichess.org/api#tag/studies/GET/api/study/{studyId}.pgn
        """
        session = berserk.TokenSession(LichessStudy.api_token())
        client = berserk.Client(session=session)

        chapters = client.studies.export(study_id=self.study_id)

        self.chapters = []
        for chapter in chapters:
            game = chess.pgn.read_game(StringIO(chapter))
            self.chapters.append(dict(game.headers))

            if not self.name:
                self.name = game.headers["StudyName"]

        return self.chapters

    @classmethod
    def get_all_lichess_studies(cls):
        session = berserk.TokenSession(LichessStudy.api_token())
        client = berserk.Client(session=session)
        return client.studies.get_by_user(username="rvapieces")

    @classmethod
    def create_lichess_study(cls, *, name, study_options=None):
        """
        Creates a new study on Lichess.com with the given name and options for the api_token owner

        :param name: The name of the study
        :param study_options: The study options based off of https://lichess.org/api#tag/studies/POST/api/study
        :return: Returns the study id
        """
        study_options = study_options or LichessStudy._default_study_options
        session = berserk.TokenSession(LichessStudy.api_token())
        client = berserk.Client(session=session)
        study_id = client.studies.create(name=name, **study_options)
        return study_id
