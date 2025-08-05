from django.urls import path

from . import views

urlpatterns = [
    path("schedule/", views.schedule, name="schedule"),
    path("event/<slug:slug>/", views.EventView.as_view(), name="event")
]
