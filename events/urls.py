from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("schedule/", views.schedule, name="schedule"),
    path("event/<slug:slug>/", views.EventView.as_view(), name="event"),
    path("", RedirectView.as_view(url="/events/schedule/", permanent=True)),
]
