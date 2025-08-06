from django.shortcuts import render

# Create your views here.


def private_coaching(request):
    return render(request, "coaching/private-coaching.html", {})
