from django.shortcuts import render

from events.models import Event


# Create your views here.

def schedule(request):
    return render(request, "events/schedule.html", {})

def calendar(request):
    events = Event.objects.all()
    
    return render(request, "events/calendar.html", {})
