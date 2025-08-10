from django.contrib.auth.models import User
from django.shortcuts import render

# Create your views here.


def private_coaching(request):
    coaches = User.objects.filter(groups__name="Coach")
    return render(request, "coaching/private-coaching.html", {"coaches": coaches})
