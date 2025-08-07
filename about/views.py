from django.contrib.auth.models import User
from django.shortcuts import render

# Create your views here.


def who_we_are(request):
    board = User.objects.filter(groups__name="Board").order_by("userprofile__order")

    return render(request, "about/who-we-are.html", {"board": board})


def code_of_conduct(request):
    return render(request, "about/code-of-conduct.html", {})


def contact_us(request):
    return render(request, "about/contact-us.html", {})
