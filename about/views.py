from django.shortcuts import render

from userprofile.models import UserProfile


# Create your views here.


def who_we_are(request):
    userprofiles = UserProfile.objects.all()

    return render(request, "about/who-we-are.html", {"userprofiles": userprofiles})


def code_of_conduct(request):
    return render(request, "about/code-of-conduct.html", {})


def contact_us(request):
    return render(request, "about/contact-us.html", {})
