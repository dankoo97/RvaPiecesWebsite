from django.shortcuts import render
from django.views import generic

from events.models import Event


# Create your views here.


class ListEventsView(generic.ListView):
    model = Event
    template_name = "events/list.html"


class EventView(generic.DetailView):
    model = Event
    template_name = "events/detail.html"


def schedule(request):
    events = Event.objects.filter(is_archived=False).order_by("-is_promoted")
    return render(request, "events/schedule.html", {"events": events, "short": True})
