from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("faq/", views.faq, name="faq"),
    path("donate/", views.donate, name="donate"),
]
