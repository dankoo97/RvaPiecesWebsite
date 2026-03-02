import datetime
import calendar
from collections import defaultdict
from io import StringIO
from zoneinfo import ZoneInfo

import chess.pgn
from django.http import HttpResponseForbidden, HttpResponse, QueryDict
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from events.forms import LichessStudyForm, LichessStudyGameSubmissionForm
from events.models import Event, Announcement, LichessStudy


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
            published_event = self.object.publish()
            if published_event:
                return redirect(published_event.get_absolute_url())
        if "_archive" in request.POST:
            self.object.archive()
            return redirect("schedule")
        if "_study" in request.POST:
            study_id = request.POST["study_id"]
            tournament_date = request.POST["tournament_date"]
            LichessStudy.objects.create(
                event=self.object, study_id=study_id, tournament_date=tournament_date
            )
            return redirect(self.object.get_absolute_url())

        return None

    def get(self, request, *args, **kwargs):
        if request.GET.get("force_refresh", "false").lower() == "true":
            Event.get_all_chessnut_events(force_refresh=True)
            return redirect(request.path)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {
            "event": self.object,
            "lichess_form": LichessStudyForm,
            **kwargs,
        }
        if self.object.calendar:
            # Recalculate the calendar
            self.object.calendar.save()
            next_event = self.object.calendar.next_occurrence
            context["next_event"] = next_event
        if self.object.lichess_studies.count() > 0:
            context["has_lichess_study"] = True
        return context

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Event.objects.all()
        return Event.objects.public()


class UploadGameView(SingleObjectMixin, generic.FormView):
    form_class = LichessStudyGameSubmissionForm
    template_name = "events/forms/submit_game_form.html"
    success_url = "/"
    queryset = Event.objects.public()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def get_form(self, form_class=...):
        return LichessStudyGameSubmissionForm(self.get_object())

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
            self.get_object(), request.POST, request.FILES
        )
        if form.is_valid():
            if form.cleaned_data["pgn_file"]:
                pgn_bytes = form.cleaned_data["pgn_file"].read()
                pgn_text = pgn_bytes.decode("utf-8", errors="replace")
            else:
                pgn_text = form.cleaned_data["pgn_text"]
            game = chess.pgn.read_game(StringIO(pgn_text))
            if game is None:
                return HttpResponse("Invalid PGN", status=400)

            study = form.cleaned_data["study"]
            chapters = study.add_chapters(pgn_text)
            query = QueryDict(mutable=True)
            query.setlist("chapters", [c["id"] for c in chapters])
            query.setlist("success", ["true"])
            query.setlist("study_id", [study.study_id])

            # TODO: Setup email server to send confirmation message?

            return redirect(
                reverse("upload_game", kwargs={"slug": study.event.slug}, query=query)
            )
        return HttpResponse(form.errors, status=400)


def schedule(request):
    curr_datetime = datetime.datetime.now(tz=ZoneInfo("US/Eastern"))
    month_start = datetime.datetime(
        year=curr_datetime.year,
        month=curr_datetime.month,
        day=1,
        tzinfo=ZoneInfo("UTC"),
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
                # TODO: django-recurring timezones are bugged, so this should allow us to use UTC and just treat it as US/Eastern
                # https://github.com/boosh/django_recurring/issues/4
                event_instances[instance.date()].append(
                    {
                        "event": event,
                        "start_time": instance.time(),
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
