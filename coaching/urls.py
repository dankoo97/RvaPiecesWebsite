from django.urls import path

from . import views

urlpatterns = [
    path("private-coaching/", views.private_coaching, name="private_coaching"),
    path("beginner-classes/", views.beginner_classes, name="beginner_classes")
]