from django.shortcuts import render

from events.models import Event


# Create your views here.
def index(request):
    events = Event.objects.public().filter(is_promoted=True)
    return render(request, "home/home.html", {"events": events})


def faq(request):
    return render(request, "home/faq.html", {})
