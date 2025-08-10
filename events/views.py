import datetime
import calendar
from collections import defaultdict
from zoneinfo import ZoneInfo

from django.shortcuts import render
from django.views import generic

from events.models import Event


# Create your views here.


class ListEventsView(generic.ListView):
    model = Event
    template_name = "events/list.html"


class EventView(generic.DetailView):
    model = Event
    template_name = "events/event-details.html"

    def get_context_data(self, **kwargs):
        return {
            "next_event": self.object.calendar.next_occurrence,
            "event": self.object,
            **kwargs,
        }


class EventInstance:
    def __init__(self, event, start_time, end_time=None):
        self.event = event
        self.start_time = start_time
        self.end_time = end_time


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

    events = Event.objects.filter(is_archived=False)

    event_instances = defaultdict(list)
    for event in events:
        if event.calendar:
            instances = event.calendar.to_rruleset().between(
                month_start, month_start + datetime.timedelta(days=31), inc=True
            )

            for instance in instances:
                # TODO: django-recurring timezones are bugged, so this should allow us to use UTC and just treat it as US/Eastern
                # https://github.com/boosh/django_recurring/issues/4
                event_instances[instance.date()].append(
                    EventInstance(event, instance.astimezone(ZoneInfo("US/Eastern")))
                )

    context = {
        "event_instances": event_instances,
        "events": events,
        "curr_day": curr_datetime.date(),
        "month": list(
            month.monthdatescalendar(curr_datetime.year, curr_datetime.month)
        ),
        "weekdays": [*calendar.day_abbr[-1:], *calendar.day_abbr[:-1]],
        "announcements": [],
    }
    return render(request, "events/schedule.html", context)
