from django.contrib.auth.models import User
from django.shortcuts import render

from userprofile.models import UserProfile


# Create your views here.


def who_we_are(request):
    userprofiles = [
        UserProfile.objects.get(user=User.objects.get(username="spenser")),
        UserProfile.objects.get(user=User.objects.get(username="dan")),
        UserProfile.objects.get(user=User.objects.get(username="matt")),
    ]

    print(userprofiles[1].image.url)

    return render(request, "about/who-we-are.html", {"userprofiles": userprofiles})


def code_of_conduct(request):
    return render(request, "about/code-of-conduct.html", {})


def contact_us(request):
    return render(request, "about/contact-us.html", {})
