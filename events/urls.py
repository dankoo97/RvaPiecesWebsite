from django.urls import path

from . import views

urlpatterns = [
    path("schedule/", views.schedule, name="schedule"),
    path("calendar/", views.calendar, name="calendar"),
]
