from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("schedule/", views.schedule, name="schedule"),
    path("event/<slug:slug>/", views.EventView.as_view(), name="event"),
    path(
        "invalidate-chessnut-cache/<slug:slug>",
        views.invalidate_chessnut_events_cache,
        name="invalidate_chessnut_cache",
    ),
    path("", RedirectView.as_view(url="/events/schedule/", permanent=True)),
]
