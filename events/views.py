import datetime
import calendar
from collections import defaultdict
from zoneinfo import ZoneInfo

from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views import generic

from events.models import Event, Announcement


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
        if "_publish" in request.POST:
            published_event = self.object.publish()
            if published_event:
                return redirect(self.object.get_absolute_url())
        if "_archive" in request.POST:
            self.object.archive()
            return redirect("events:list")
        return None

    def get(self, request, *args, **kwargs):
        if request.GET.get("force_refresh", "false").lower() == "true":
            Event.get_all_chessnut_events(force_refresh=True)
            return redirect(request.path)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        next_event = None
        if self.object.calendar:
            # Recalculate the calendar
            self.object.calendar.save()
            next_event = self.object.calendar.next_occurrence
        return {
            "next_event": next_event,
            "event": self.object,
            **kwargs,
        }

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Event.objects.all()
        return Event.objects.public()


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
