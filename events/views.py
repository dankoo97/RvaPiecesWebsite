import datetime
import calendar
from collections import defaultdict

from django.shortcuts import render
from django.views import generic

from events.models import Event, EventInstance


# Create your views here.


class ListEventsView(generic.ListView):
    model = Event
    template_name = "events/list.html"


class EventView(generic.DetailView):
    model = Event
    template_name = "events/detail.html"


def schedule(request):
    curr_day = datetime.datetime.now().date()
    month = calendar.Calendar()
    month.setfirstweekday(calendar.SUNDAY)

    events = Event.objects.filter(is_archived=False)

    event_instances = defaultdict(list)
    for instance in EventInstance.objects.filter(date__month=curr_day.month):
        event_instances[instance.date].append(instance)

    context = {
        "event_instances": event_instances,
        "events": events,
        "curr_day": curr_day,
        "month": list(month.monthdatescalendar(curr_day.year, curr_day.month)),
        "weekdays": [*calendar.day_abbr[-1:], *calendar.day_abbr[:-1]],
    }
    return render(request, "events/schedule.html", context)
