from django.db.models import Q
from django.shortcuts import render
from userprofile.models import UserProfile


# Create your views here.


def who_we_are(request):
    board_and_volunteers = UserProfile.objects.filter(
        Q(user__groups__name="Board") | Q(user__groups__name="Volunteer")
    )
    return render(
        request, "about/who-we-are.html", {"board_and_volunteers": board_and_volunteers}
    )


def code_of_conduct(request):
    return render(request, "about/code-of-conduct.html", {})


def contact_us(request):
    return render(request, "about/contact-us.html", {})
