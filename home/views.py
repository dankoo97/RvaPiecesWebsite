from django.shortcuts import render


# Create your views here.


def index(request):
    return render(request, "home/home.html", {})


def faq(request):
    return render(request, "home/faq.html", {})


def donate(request):
    return render(request, "home/donate.html", {})
