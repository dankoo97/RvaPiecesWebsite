import datetime
import calendar
import json
import logging
import re
from collections import defaultdict
from io import StringIO
from typing import Any
from urllib.parse import quote

import chess.pgn
from berserk.exceptions import ApiError, BerserkError
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from django.views.decorators.cache import cache_control
from django.views.generic.detail import SingleObjectMixin

from events.chessnut import Chessnut
from events.forms import LichessStudyForm, LichessStudyGameSubmissionForm, ChessnutForm
from events.models import Event, Announcement, LichessStudy

logger = logging.getLogger(__name__)


# Create your views here.
class ListEventsView(generic.ListView):
    model = Event
    template_name = "events/list.html"


class EventView(generic.DetailView):
    model = Event
    template_name = "events/event-details.html"

    def post(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return HttpResponseForbidden()

        self.object = self.get_object()
        if "_publish" in request.POST:
            try:
                published_event = self.object.publish()
            except Exception as e:
                logger.exception("Failed to publish event %s", self.object.pk)
                messages.error(request, f"Failed to publish {self.object}: {e}")
                return redirect(self.object.get_absolute_url())
            return redirect(published_event.get_absolute_url())
        if "_archive" in request.POST:
            self.object.archive()
            return redirect("schedule")
        if "_study" in request.POST:
            study_form = LichessStudyForm(self.object, request.POST)
            if study_form.is_valid():
                if not study_form.study_id:
                    study_form.study_id = "test"
                    # study.study_id = LichessStudy.create_lichess_study(name=study.name)
                study = study_form.save(commit=False)
                study.event = self.object
                study.save()
                return JsonResponse({"success": True})
            context = self.get_context_data()
            context["lichess_form"] = study_form
            return self.render_to_response(context)
        if "_chessnut" in request.POST:
            chessnut_event_id = request.POST["chessnut_event"]
            expires = request.POST["expires"]
            chessnut_event = Chessnut().get_chessnut_event_by_id(chessnut_event_id)
            chessnut_event["expires"] = expires
            self.object.chessnut_events["events"].append(chessnut_event)
            self.object.save()

        return redirect(self.object.get_absolute_url())

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {
            "event": self.object,
            "lichess_form": LichessStudyForm(self.object),
            "chessnut_form": ChessnutForm,
            **kwargs,
        }
        if self.object.calendar:
            # Recalculate the calendar
            self.object.calendar.save()
            context["event_obj"] = self.object.calendar.events.first()

        today = datetime.date.today()
        active_events = []
        removed_expired_event = False
        for chessnut_event in self.object.chessnut_events["events"]:
            expires = chessnut_event.get("expires")
            if expires:
                expiry = datetime.date.fromisoformat(str(expires)[:10])
                if expiry < today:
                    removed_expired_event = True
                    continue
            active_events.append(chessnut_event)

        if removed_expired_event:
            self.object.chessnut_events["events"] = active_events
            self.object.save()

        self.object.sync_magic_chessnut_events()
        context["magic_handler_config"] = self.object.chessnut_handler

        return context

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Event.objects.all()
        return Event.objects.public()

    def render_to_response(
        self, context: dict[str, Any], **response_kwargs: Any
    ) -> HttpResponse:
        response = super().render_to_response(context, **response_kwargs)
        response.set_cookie(
            "chessnut_json",
            quote(json.dumps(self.object.chessnut_events), safe=""),
            httponly=False,
            samesite="Lax",
        )
        return response


class UploadGameView(SingleObjectMixin, generic.FormView):
    form_class = LichessStudyGameSubmissionForm
    template_name = "events/forms/submit_game_form.html"
    success_url = "/"
    queryset = Event.objects.public()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def get_form(self, form_class=...):
        chessnut_event_id = self.request.GET.get("chessnut_event_id")
        form = LichessStudyGameSubmissionForm(
            self.get_object(),
            chessnut_event_id=chessnut_event_id,
        )
        form.initial["chessnut_event_id"] = chessnut_event_id
        study_id = self.request.GET.get("study_id")
        if (
            study_id
            and form.fields["study"].queryset.filter(study_id=study_id).exists()
        ):
            form.initial["study"] = study_id
        return form

    def get_context_data(self, **kwargs):
        success = self.request.GET.get("success", "not_found").lower()
        if success == "true":
            study_id = self.request.GET.get("study_id")
            kwargs["success"] = True
            kwargs["chapter_ids"] = self.request.GET.getlist("chapters")
            kwargs["study"] = LichessStudy.objects.get(study_id=study_id)

        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = LichessStudyGameSubmissionForm(
            self.object,
            chessnut_event_id=request.POST.get("chessnut_event_id"),
            data=request.POST,
        )
        if form.is_valid():
            pgn_text = form.cleaned_data["pgn"]
            share_to_discord = form.cleaned_data["share_to_discord"]
            game = chess.pgn.read_game(StringIO(pgn_text))
            if game is None:
                return HttpResponse("Invalid PGN", status=400)

            white_player_discord = form.cleaned_data["discord_white_player"] or None
            black_player_discord = form.cleaned_data["discord_black_player"] or None
            orientation = (
                form.cleaned_data["discord_game_orientation"].lower() or "white"
            )

            study = form.cleaned_data["study"]
            # TODO: Setup email server to send confirmation message?
            try:
                chapters = study.add_chapters(str(game), orientation=orientation)
            except ApiError as e:
                messages.error(request, f"Error adding chapter: {e}")
            except BerserkError as e:
                messages.error(request, f"Error adding chapter: {e}")
            else:
                if share_to_discord:
                    for chapter in chapters:
                        study.share_to_discord(
                            game,
                            chapter["id"],
                            white_player_discord,
                            black_player_discord,
                        )
                messages.success(
                    request, f"Game added successfully to study! {study.study_url}"
                )
                return redirect(reverse("event", kwargs={"slug": study.event.slug}))
        return HttpResponse(form.errors, status=400)


class ChessnutAPI(generic.View):
    slug_field = "event"
    slug_url_kwarg = "event"

    def post(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return HttpResponseForbidden()
        if "_update" in request.POST:
            logger.debug("POST data: %s", request.POST)
            event = Event.objects.get(slug=kwargs["event"])
            removed_ids = json.loads(request.POST.get("removedIds", "[]"))
            event.update_chessnut_json(
                json.loads(request.POST["newJson"]),
                removed_event_ids=removed_ids,
            )
            return JsonResponse({"success": True})
        if "_magic_update" in request.POST:
            event = Event.objects.get(slug=kwargs["event"])
            handler = event.chessnut_handler or {}
            try:
                handler.update(
                    {
                        "enabled": request.POST.get("enabled") == "true",
                        "title_regex": request.POST["title_regex"],
                        "days_before_start": int(request.POST["days_before_start"]),
                        "days_after_end": int(request.POST["days_after_end"]),
                    }
                )
                re.compile(handler["title_regex"])
            except (KeyError, TypeError, ValueError, re.error) as error:
                return JsonResponse({"error": str(error)}, status=400)

            event.chessnut_handler = handler
            event.save()
            event.sync_magic_chessnut_events(refresh=True)
            return JsonResponse({"success": True})
        if "_magic_clear_ignored" in request.POST:
            event = Event.objects.get(slug=kwargs["event"])
            handler = event.chessnut_handler or {}
            handler["ignored_event_ids"] = []
            event.chessnut_handler = handler
            event.save()
            event.sync_magic_chessnut_events(refresh=True)
            return JsonResponse({"success": True})
        return HttpResponse(status=400)


@cache_control(max_age=60 * 60 * 24)
def schedule(request):
    current_tz = timezone.get_current_timezone()
    curr_datetime = timezone.localtime(timezone.now(), current_tz)
    month_start = datetime.datetime(
        year=curr_datetime.year,
        month=curr_datetime.month,
        day=1,
        tzinfo=current_tz,
    )
    month = calendar.Calendar()
    month.setfirstweekday(calendar.SUNDAY)

    events = Event.objects.public().order_by("-is_promoted")

    event_instances = defaultdict(list)
    for event in events:
        if event.calendar:
            instances = event.calendar.to_rruleset().between(
                month_start, month_start + datetime.timedelta(days=70), inc=True
            )

            for instance in instances:
                if timezone.is_naive(instance):
                    instance = timezone.make_aware(instance, current_tz)
                else:
                    instance = timezone.localtime(instance, current_tz)

                event_instances[instance.date()].append(
                    {
                        "event": event,
                        "start_time": instance.timetz(),
                    }
                )

    context = {
        "event_instances": event_instances,
        "events": events,
        "curr_day": curr_datetime.date(),
        "curr_month": {
            "datetime": curr_datetime,
            "calendar": list(
                month.monthdatescalendar(curr_datetime.year, curr_datetime.month)
            ),
        },
        "next_month": {
            "datetime": month_start + datetime.timedelta(days=32),
            "calendar": list(
                month.monthdatescalendar(
                    curr_datetime.year
                    if curr_datetime.month < 12
                    else curr_datetime.year + 1,
                    curr_datetime.month + 1 if curr_datetime.month < 12 else 1,
                )
            ),
        }
        if curr_datetime.day >= 15
        else None,
        "weekdays": [*calendar.day_abbr[-1:], *calendar.day_abbr[:-1]],
        "announcements": Announcement.objects.filter(expires__gt=curr_datetime),
    }
    return render(request, "events/schedule.html", context)
